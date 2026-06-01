#!/usr/bin/env python3
"""Interactive first-pass onboarding for Domain Guardian knowledge files."""

from __future__ import annotations

from datetime import date
from pathlib import Path
import textwrap


QUESTIONS = [
    (
        "business-model.md",
        "Product summary",
        "What does this product sell or enable, who uses it, and who pays for it?",
    ),
    (
        "business-model.md",
        "Value-critical outcomes",
        "What user action or business outcome must never be broken?",
    ),
    (
        "domain-rules.md",
        "Protected invariants",
        "What business rule should code preserve even if a simpler implementation is tempting?",
    ),
    (
        "domain-rules.md",
        "Lifecycle and eligibility",
        "What are the important entities, states, eligibility rules, and forbidden transitions?",
    ),
    (
        "user-flows.md",
        "Critical flows",
        "Which user flows create money, trust, compliance, or operational workload?",
    ),
    (
        "operational-context.md",
        "Operational constraints",
        "Which manual reviews, overrides, external systems, or incident lessons matter?",
    ),
    (
        "code-map.md",
        "Code map",
        "Which files, modules, APIs, jobs, or tests enforce these rules?",
    ),
]


def append_answer(knowledge_dir: Path, filename: str, title: str, answer: str) -> None:
    path = knowledge_dir / filename
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.exists():
        existing = path.read_text(encoding="utf-8").rstrip()
    else:
        existing = f"# {filename.removesuffix('.md').replace('-', ' ').title()}"

    block = f"""

## Onboarding: {title}

- Date: {date.today().isoformat()}
- Source: interactive Domain Guardian bootstrap
- Notes:
{format_bullets(answer)}
"""
    path.write_text(existing + block, encoding="utf-8")


def format_bullets(answer: str) -> str:
    lines = [line.strip() for line in answer.splitlines() if line.strip()]
    if not lines:
        return "  - No answer provided."
    return "\n".join(f"  - {line}" for line in lines)


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Interactively fill Domain Guardian context files.")
    parser.add_argument(
        "knowledge_dir",
        nargs="?",
        default="knowledge",
        help="Directory containing Domain Guardian markdown files.",
    )
    args = parser.parse_args()

    knowledge_dir = Path(args.knowledge_dir)
    print("Domain Guardian onboarding")
    print("Answer briefly. Press Enter on an empty answer to skip a question.\n")

    for index, (filename, title, question) in enumerate(QUESTIONS, start=1):
        print(f"[{index}/{len(QUESTIONS)}] {question}")
        print("> ", end="")
        answer = input().strip()
        if not answer:
            print("Skipped.\n")
            continue
        append_answer(knowledge_dir, filename, title, answer)
        wrapped = textwrap.shorten(answer, width=90, placeholder="...")
        print(f"Saved to {knowledge_dir}/{filename}: {wrapped}\n")

    print(f"Done. Run: python3 scripts/check_context.py {knowledge_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
