#!/usr/bin/env python3
"""Analyze a diff against Domain Guardian context and report domain risk."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys

from check_brief import validate_brief
from domain_brief import (
    confidence_for_score,
    find_context_dir,
    ranked_lines,
    read_context,
    split_topics,
    tokens,
)


DOMAIN_SENSITIVE_TERMS = {
    "price",
    "pricing",
    "bill",
    "billing",
    "payment",
    "refund",
    "permission",
    "role",
    "eligibility",
    "cancel",
    "state",
    "transition",
    "webhook",
    "retry",
    "audit",
    "notification",
    "fulfillment",
    "moderation",
}


def read_diff(diff_file: str | None) -> str:
    if diff_file:
        return Path(diff_file).read_text(encoding="utf-8")
    if not sys.stdin.isatty():
        return sys.stdin.read()
    return ""


def changed_files(diff_text: str) -> list[str]:
    files: list[str] = []
    for line in diff_text.splitlines():
        if line.startswith("+++ b/"):
            files.append(line.removeprefix("+++ b/"))
        elif line.startswith("diff --git "):
            parts = line.split()
            if len(parts) >= 4 and parts[3].startswith("b/"):
                files.append(parts[3].removeprefix("b/"))
    seen: set[str] = set()
    ordered: list[str] = []
    for path in files:
        if path != "/dev/null" and path not in seen:
            seen.add(path)
            ordered.append(path)
    return ordered


def extract_index_entries(index_path: Path) -> list[dict[str, str]]:
    if not index_path.exists():
        return []
    entries: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for raw_line in index_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line.startswith("- Area:"):
            if current:
                entries.append(current)
            current = {"Area": line.split(":", 1)[1].strip()}
            continue
        if current is not None and line.startswith("- ") and ":" in line:
            key, value = line[2:].split(":", 1)
            current[key.strip()] = value.strip()
    if current:
        entries.append(current)
    return entries


def score_entry(entry: dict[str, str], haystack_tokens: set[str], files: list[str]) -> int:
    score = 0
    keyword_tokens = tokens(entry.get("Keywords", ""))
    code_tokens = tokens(entry.get("Code", ""))
    score += len(keyword_tokens & haystack_tokens) * 3
    score += len(code_tokens & haystack_tokens) * 2
    code = entry.get("Code", "")
    for file_path in files:
        if file_path in code:
            score += 6
        elif Path(file_path).name and Path(file_path).name in code:
            score += 3
    return score


def risk_level(diff_text: str, files: list[str], matches: list[tuple[int, dict[str, str]]]) -> str:
    diff_tokens = tokens(diff_text + " " + " ".join(files))
    if any(term in diff_tokens for term in DOMAIN_SENSITIVE_TERMS) and matches:
        return "HIGH"
    if matches:
        return "MEDIUM"
    if any(term in diff_tokens for term in DOMAIN_SENSITIVE_TERMS):
        return "MEDIUM"
    return "LOW"


def required_topics_from_matches(matches: list[tuple[int, dict[str, str]]]) -> list[str]:
    topics: list[str] = []
    seen: set[str] = set()
    if not matches:
        return topics
    top_score = matches[0][0]
    required_threshold = max(8, top_score - 3)
    for score, entry in matches:
        if score < required_threshold:
            continue
        for topic in split_topics(entry.get("Required brief topics", "")):
            normalized = topic.lower()
            if normalized not in seen:
                seen.add(normalized)
                topics.append(topic)
    return topics


def render_report(
    *,
    diff_text: str,
    files: list[str],
    context_dir: Path,
    require_brief: bool,
    brief: str | None,
) -> tuple[str, int]:
    haystack = diff_text + "\n" + "\n".join(files)
    haystack_tokens = tokens(haystack)
    entries = extract_index_entries(context_dir / "index.md")
    scored = sorted(
        [(score_entry(entry, haystack_tokens, files), entry) for entry in entries],
        key=lambda item: item[0],
        reverse=True,
    )
    matches = [(score, entry) for score, entry in scored if score > 0][:5]
    level = risk_level(diff_text, files, matches)
    confidence = confidence_for_score(matches[0][0] if matches else 0)

    exit_code = 0
    lines: list[str] = [
        "# Domain Diff Risk Report",
        "",
        f"- Context directory: {context_dir}",
        f"- Risk level: {level}",
        f"- Confidence: {confidence}",
        f"- Changed files: {', '.join(files) if files else 'none detected'}",
    ]

    if matches:
        lines.extend(["", "## Matched Index Entries", ""])
        for score, entry in matches:
            lines.append(f"- {entry.get('Area', 'Unnamed area')} (score {score})")
            for key in ("Read", "Code", "Owners", "Risk", "Required brief topics"):
                if entry.get(key):
                    lines.append(f"  - {key}: {entry[key]}")
    else:
        lines.extend(["", "## Matched Index Entries", "", "- No index entry matched. Escalate to full context if this is business logic."])

    if level in {"HIGH", "MEDIUM"}:
        context = read_context(context_dir)
        task = " ".join(files) + " " + re.sub(r"[^a-zA-Z0-9_ ]+", " ", diff_text[:2000])
        lines.extend(["", "## Relevant Rules", ""])
        lines.extend(ranked_lines(task, context["domain-rules.md"], limit=6))
        lines.extend(["", "## Relevant Flows And Operations", ""])
        lines.extend(ranked_lines(task, context["user-flows.md"] + context["operational-context.md"], limit=6))
    else:
        lines.extend(["", "## Relevant Rules", "", "- Skipped for LOW risk: no index entry or domain-sensitive term matched."])
        lines.extend(["", "## Relevant Flows And Operations", "", "- Skipped for LOW risk."])
    lines.extend(["", "## Recommended Gate", ""])

    if level in {"HIGH", "MEDIUM"}:
        lines.append("- Create or update a Domain Impact Brief before merging this change.")
        lines.append("- Add tests for the matched protected invariants.")
    else:
        lines.append("- No strong domain signal found. Use normal review unless the code owner knows hidden policy impact.")

    if require_brief:
        lines.extend(["", "## Brief Check", ""])
        if not brief:
            lines.append("- NEEDS WORK: --require-brief was set but --brief was not provided.")
            exit_code = 1
        else:
            problems = validate_brief(Path(brief), required_topics_from_matches(matches))
            if problems:
                lines.append("- NEEDS WORK: Domain Impact Brief")
                lines.extend(f"  - {problem}" for problem in problems)
                exit_code = 1
            else:
                lines.append("- OK: Domain Impact Brief")

    return "\n".join(lines) + "\n", exit_code


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze a git diff for domain-rule risk.")
    parser.add_argument("--diff-file", help="Path to a diff file. Reads stdin when omitted.")
    parser.add_argument("--knowledge-dir", help="Domain Guardian context directory.")
    parser.add_argument("--brief", help="Domain Impact Brief path to validate.")
    parser.add_argument("--require-brief", action="store_true", help="Fail when a valid brief is missing.")
    args = parser.parse_args()

    context_dir = find_context_dir(args.knowledge_dir)
    if context_dir is None:
        print("FAIL: no Domain Guardian context directory found.")
        return 1
    diff_text = read_diff(args.diff_file)
    if not diff_text.strip():
        print("FAIL: no diff input provided.")
        return 1

    report, exit_code = render_report(
        diff_text=diff_text,
        files=changed_files(diff_text),
        context_dir=context_dir,
        require_brief=args.require_brief,
        brief=args.brief,
    )
    print(report)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
