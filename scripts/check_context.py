#!/usr/bin/env python3
"""Check whether Domain Guardian knowledge files have enough signal to guide an agent."""

from __future__ import annotations

import argparse
from pathlib import Path
import re


REQUIRED_FILES = [
    "index.md",
    "business-model.md",
    "domain-rules.md",
    "user-flows.md",
    "operational-context.md",
    "code-map.md",
]

PLACEHOLDER_MARKERS = [
    "- Product:\n",
    "- Rule:\n",
    "- Flow:\n",
    "- Concept:\n",
    "- Teams involved:\n",
    "- Keywords:\n",
]


def split_list(raw_value: str) -> list[str]:
    backtick_values = re.findall(r"`([^`]+)`", raw_value)
    if backtick_values:
        return [value.strip() for value in backtick_values if value.strip()]
    return [value.strip().strip("` ") for value in raw_value.split(",") if value.strip()]


def index_code_paths(index_path: Path) -> list[str]:
    if not index_path.exists():
        return []
    paths: list[str] = []
    seen: set[str] = set()
    for raw_line in index_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line.startswith("- Code:"):
            continue
        for path in split_list(line.split(":", 1)[1]):
            if path not in seen:
                seen.add(path)
                paths.append(path)
    return paths


def check_index_code_map_coverage(base: Path) -> tuple[bool, list[str]]:
    index_path = base / "index.md"
    code_map_path = base / "code-map.md"
    if not index_path.exists() or not code_map_path.exists():
        return False, ["missing index.md or code-map.md"]

    code_map_text = code_map_path.read_text(encoding="utf-8")
    problems = [
        f"index code path missing from code-map: {path}"
        for path in index_code_paths(index_path)
        if path not in code_map_text
    ]
    return not problems, problems


def score_file(path: Path) -> tuple[bool, list[str]]:
    problems: list[str] = []
    if not path.exists():
        return False, ["missing"]

    text = path.read_text(encoding="utf-8")
    non_empty_lines = [line for line in text.splitlines() if line.strip()]

    if len(non_empty_lines) < 12:
        problems.append("too sparse")

    placeholder_count = sum(text.count(marker) for marker in PLACEHOLDER_MARKERS)
    if placeholder_count >= 2:
        problems.append("mostly template placeholders")

    blank_field_count = len(re.findall(r"^\s*-\s+[^:\n]+:\s*$", text, flags=re.MULTILINE))
    if blank_field_count >= 6:
        problems.append("many unfilled fields")

    has_source = "source" in text.lower() or "owner" in text.lower()
    if not has_source:
        problems.append("no source/owner signal")

    return not problems, problems


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Domain Guardian context completeness.")
    parser.add_argument(
        "knowledge_dir",
        nargs="?",
        default="knowledge",
        help="Directory containing Domain Guardian markdown files.",
    )
    args = parser.parse_args()

    base = Path(args.knowledge_dir)
    if not base.exists():
        print(f"FAIL: knowledge directory not found: {base}")
        return 1

    failed = False
    for filename in REQUIRED_FILES:
        ok, problems = score_file(base / filename)
        status = "OK" if ok else "NEEDS WORK"
        print(f"{status}: {filename}")
        for problem in problems:
            print(f"  - {problem}")
        failed = failed or not ok

    ok, problems = check_index_code_map_coverage(base)
    status = "OK" if ok else "NEEDS WORK"
    print(f"{status}: index-code-map coverage")
    for problem in problems:
        print(f"  - {problem}")
    failed = failed or not ok

    if failed:
        print("\nDomain Guardian context is not ready enough for unsupervised domain-sensitive edits.")
        print("Run scripts/bootstrap_context.py or ask the agent to onboard one section at a time.")
        return 1

    print("\nDomain Guardian context has enough structure for a first-pass Domain Impact Brief.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
