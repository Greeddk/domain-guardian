#!/usr/bin/env python3
"""Generate a first-pass Domain Impact Brief from Domain Guardian context."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
import re
from typing import Iterable


CONTEXT_CANDIDATES = [
    ".domain-guardian",
    "docs/domain-guardian",
    "knowledge",
]

REQUIRED_FILES = [
    "index.md",
    "business-model.md",
    "domain-rules.md",
    "user-flows.md",
    "operational-context.md",
    "code-map.md",
]


def find_context_dir(explicit: str | None) -> Path | None:
    if explicit:
        path = Path(explicit)
        return path if path.exists() else None
    for candidate in CONTEXT_CANDIDATES:
        path = Path(candidate)
        if path.exists():
            return path
    return None


def useful_lines(text: str) -> list[str]:
    lines: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line.startswith("-"):
            continue
        if re.match(r"^-\s+[^:\n]+:\s*$", line):
            continue
        if "No answer provided" in line:
            continue
        lines.append(line)
    return lines


def normalize_token(token: str) -> str:
    token = token.lower()
    if token.startswith("cancel"):
        return "cancel"
    for suffix in ("ments", "ment", "ings", "ing", "ed", "s"):
        if len(token) > len(suffix) + 3 and token.endswith(suffix):
            return token[: -len(suffix)]
    return token


def tokens(text: str) -> set[str]:
    raw_tokens = re.findall(r"[a-zA-Z0-9_]+", text.lower())
    ignored = {
        "allow",
        "change",
        "create",
        "update",
        "the",
        "and",
        "for",
        "with",
        "this",
        "that",
        "from",
    }
    return {normalize_token(token) for token in raw_tokens if len(token) > 2 and token not in ignored}


def ranked_lines(task: str, lines: Iterable[str], limit: int = 6) -> list[str]:
    task_tokens = tokens(task)
    scored: list[tuple[int, int, str]] = []
    for index, line in enumerate(lines):
        line_tokens = tokens(line)
        score = len(task_tokens & line_tokens)
        if line.startswith("- Rule:"):
            score += 2
        if "must always be true" in line.lower() or "protected" in line.lower():
            score += 1
        scored.append((score, -index, line))

    selected = [line for score, _index, line in sorted(scored, reverse=True) if score > 0]
    if not selected:
        selected = [line for _score, _index, line in sorted(scored, reverse=True)]
    return selected[:limit] if selected else ["- No concrete context captured yet."]


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


def score_index_entry(entry: dict[str, str], haystack: str) -> int:
    haystack_tokens = tokens(haystack)
    score = 0
    score += len(tokens(entry.get("Area", "")) & haystack_tokens) * 4
    score += len(tokens(entry.get("Keywords", "")) & haystack_tokens) * 3
    score += len(tokens(entry.get("Code", "")) & haystack_tokens) * 2
    return score


def confidence_for_score(score: int) -> str:
    if score >= 8:
        return "HIGH"
    if score >= 3:
        return "MEDIUM"
    return "LOW"


def split_topics(raw_topics: str) -> list[str]:
    return [topic.strip().strip(".") for topic in raw_topics.split(",") if topic.strip()]


def matched_index_entries(task: str, context_dir: Path, limit: int = 3) -> list[tuple[int, dict[str, str]]]:
    entries = extract_index_entries(context_dir / "index.md")
    scored = sorted(
        [(score_index_entry(entry, task), entry) for entry in entries],
        key=lambda item: item[0],
        reverse=True,
    )
    return [(score, entry) for score, entry in scored if score > 0][:limit]


def read_context(context_dir: Path) -> dict[str, list[str]]:
    context: dict[str, list[str]] = {}
    for filename in REQUIRED_FILES:
        path = context_dir / filename
        if path.exists():
            context[filename] = useful_lines(path.read_text(encoding="utf-8"))
        else:
            context[filename] = [f"- Missing {filename}"]
    return context


def pick(lines: Iterable[str], limit: int = 5) -> list[str]:
    selected = [line for line in lines if line.strip()]
    return selected[:limit] if selected else ["- No concrete context captured yet."]


def render_brief(task: str, context_dir: Path, context: dict[str, list[str]]) -> str:
    matches = matched_index_entries(task, context_dir)
    top_score = matches[0][0] if matches else 0
    confidence = confidence_for_score(top_score)
    if confidence == "LOW":
        index = ["- No strong index match. Ask the user or inspect code before pulling domain rules into the brief."]
        rules = ["- Skipped for LOW confidence: no strong index match."]
        flows = ["- Skipped for LOW confidence."]
        code = ["- Skipped for LOW confidence."]
        business = ranked_lines(task, context["business-model.md"], limit=4)
    else:
        index = []
        for score, entry in matches:
            index.append(f"- Area: {entry.get('Area', 'Unnamed area')} (score {score})")
            for key in ("Owners", "Risk", "Read", "Code", "Required brief topics"):
                if entry.get(key):
                    index.append(f"  - {key}: {entry[key]}")
        rules = ranked_lines(task, context["domain-rules.md"])
        flows = ranked_lines(task, context["user-flows.md"] + context["operational-context.md"])
        code = ranked_lines(task, context["code-map.md"])
        business = ranked_lines(task, context["business-model.md"], limit=4)

    def bullet_block(items: list[str]) -> str:
        return "\n".join(items)

    return f"""# Domain Impact Brief

- Date: {date.today().isoformat()}
- Task: {task}
- Context directory: {context_dir}
- Confidence: {confidence}

## Relevant Business Context

{bullet_block(business)}

## Selected Context From Index

{bullet_block(index)}

## Relevant Business Rules

{bullet_block(rules)}

## Relevant User Or Operations Flows

{bullet_block(flows)}

## Code Areas Likely Involved

{bullet_block(code)}

## Protected Invariants

- Preserve the rules above unless the user explicitly changes the policy.
- Treat gaps, exceptions, and owner/source conflicts as product questions.
- Do not rely on passing implementation-level tests as proof of domain correctness.

## Ambiguities Or Questions

- Which rule owner can approve a behavior change?
- Which existing tests prove the business invariant rather than just the current implementation?
- Which user or operations flow should be manually checked after the change?

## Test Or Review Guardrails

- Add or update tests for the protected invariant touched by this task.
- Review lifecycle transitions, permissions, notifications, retries, and audit trails.
- Update Domain Guardian context if the work reveals a new rule or exception.
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a Domain Impact Brief.")
    parser.add_argument("--task", required=True, help="The planned code change or review target.")
    parser.add_argument(
        "--knowledge-dir",
        help="Domain Guardian context directory. Defaults to .domain-guardian, docs/domain-guardian, then knowledge.",
    )
    parser.add_argument("--output", help="Optional markdown output path.")
    args = parser.parse_args()

    context_dir = find_context_dir(args.knowledge_dir)
    if context_dir is None:
        print("FAIL: no Domain Guardian context directory found.")
        print("Run scripts/init_project_context.py first, or pass --knowledge-dir.")
        return 1

    brief = render_brief(args.task, context_dir, read_context(context_dir))
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(brief, encoding="utf-8")
        print(f"WROTE: {output_path}")
    else:
        print(brief)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
