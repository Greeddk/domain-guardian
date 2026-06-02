#!/usr/bin/env python3
"""Prepare all Domain Guardian context an agent needs before editing code."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from domain_brief import confidence_for_score, find_context_dir, matched_index_entries, read_context, render_brief
from task_context import render_packet


def confidence_for_task(task: str, context_dir: Path) -> str:
    matches = matched_index_entries(task, context_dir)
    top_score = matches[0][0] if matches else 0
    return confidence_for_score(top_score)


def default_output_dir() -> Path:
    return Path("docs/domain-guardian/pre-change") / date.today().isoformat()


def write_outputs(task: str, context_dir: Path, output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    context_path = output_dir / "task-context.md"
    brief_path = output_dir / "domain-impact-brief.md"
    context_path.write_text(render_packet(task, context_dir), encoding="utf-8")
    brief_path.write_text(render_brief(task, context_dir, read_context(context_dir)), encoding="utf-8")
    return context_path, brief_path


def render_stdout(task: str, context_dir: Path) -> str:
    context = read_context(context_dir)
    return "\n".join(
        [
            render_packet(task, context_dir).rstrip(),
            "",
            "---",
            "",
            render_brief(task, context_dir, context).rstrip(),
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare Domain Guardian context before code edits.")
    parser.add_argument("--task", required=True, help="The planned feature, bug fix, refactor, or review target.")
    parser.add_argument(
        "--knowledge-dir",
        help="Domain Guardian context directory. Defaults to .domain-guardian, docs/domain-guardian, then knowledge.",
    )
    parser.add_argument(
        "--output-dir",
        help="Directory for generated task-context.md and domain-impact-brief.md. Defaults to stdout.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return a non-zero exit code when no indexed business flow matches the task.",
    )
    args = parser.parse_args()

    context_dir = find_context_dir(args.knowledge_dir)
    if context_dir is None:
        print("FAIL: no Domain Guardian context directory found.")
        print("Run scripts/init_project_context.py first, or pass --knowledge-dir.")
        return 1

    confidence = confidence_for_task(args.task, context_dir)
    if args.output_dir:
        context_path, brief_path = write_outputs(args.task, context_dir, Path(args.output_dir))
        print(f"WROTE: {context_path}")
        print(f"WROTE: {brief_path}")
    else:
        print(render_stdout(args.task, context_dir))

    if args.strict and confidence == "LOW":
        print("NEEDS CLARIFICATION: no indexed business flow matched this task.")
        print("Ask which business flow, rule owner, or policy decision applies before editing domain-sensitive code.")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
