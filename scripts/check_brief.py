#!/usr/bin/env python3
"""Validate that a Domain Impact Brief exists and contains required sections."""

from __future__ import annotations

import argparse
from pathlib import Path


REQUIRED_SECTIONS = [
    "Domain Impact Brief",
    "Relevant Business Context",
    "Relevant Business Rules",
    "Relevant User Or Operations Flows",
    "Code Areas Likely Involved",
    "Protected Invariants",
    "Ambiguities Or Questions",
    "Test Or Review Guardrails",
]

WEAK_MARKERS = [
    "No concrete context captured yet",
    "TBD",
    "TODO",
    "Task: TBD",
    "Task: TODO",
]


def validate_brief(path: Path, required_topics: list[str] | None = None) -> list[str]:
    problems: list[str] = []
    if not path.exists():
        return [f"brief not found: {path}"]
    text = path.read_text(encoding="utf-8")
    normalized_text = text.lower()
    for section in REQUIRED_SECTIONS:
        if section not in text:
            problems.append(f"missing section: {section}")
    for marker in WEAK_MARKERS:
        if marker in text:
            problems.append(f"weak placeholder marker: {marker}")
    if len([line for line in text.splitlines() if line.strip().startswith("-")]) < 10:
        problems.append("brief is too sparse")
    for topic in required_topics or []:
        if topic.strip() and topic.lower() not in normalized_text:
            problems.append(f"missing required topic: {topic}")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a Domain Impact Brief.")
    parser.add_argument("brief", help="Path to a Domain Impact Brief markdown file.")
    parser.add_argument(
        "--required-topic",
        action="append",
        default=[],
        help="Topic that must be explicitly covered in the brief. May be repeated.",
    )
    args = parser.parse_args()

    problems = validate_brief(Path(args.brief), args.required_topic)
    if problems:
        print("NEEDS WORK: Domain Impact Brief")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print("OK: Domain Impact Brief")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
