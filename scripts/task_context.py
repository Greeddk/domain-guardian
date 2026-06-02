#!/usr/bin/env python3
"""Prepare a business-flow-aware context packet before code changes."""

from __future__ import annotations

import argparse
from pathlib import Path

from domain_brief import (
    confidence_for_score,
    find_context_dir,
    matched_index_entries,
    ranked_lines,
    read_context,
    split_topics,
)


def bullet_block(items: list[str]) -> str:
    return "\n".join(items)


def render_matched_flows(matches: list[tuple[int, dict[str, str]]]) -> list[str]:
    if not matches:
        return ["- No strong indexed flow matched this task."]
    lines: list[str] = []
    for score, entry in matches:
        lines.append(f"- Area: {entry.get('Area', 'Unnamed area')} (score {score})")
        for key in ("Risk", "Owners", "Required brief topics"):
            if entry.get(key):
                lines.append(f"  - {key}: {entry[key]}")
    return lines


def render_context_files(matches: list[tuple[int, dict[str, str]]]) -> list[str]:
    files: list[str] = []
    seen: set[str] = set()
    for _score, entry in matches:
        for filename in split_topics(entry.get("Read", "")):
            normalized = filename.strip("` ")
            if normalized and normalized not in seen:
                seen.add(normalized)
                files.append(f"- {normalized}")
    if not files:
        return ["- No indexed context file selected. Read index.md, then ask before editing business logic."]
    return files


def render_code_paths(matches: list[tuple[int, dict[str, str]]]) -> list[str]:
    paths: list[str] = []
    seen: set[str] = set()
    for _score, entry in matches:
        for path in split_topics(entry.get("Code", "")):
            normalized = path.strip("` ")
            if normalized and normalized not in seen:
                seen.add(normalized)
                paths.append(f"- {normalized}")
    if not paths:
        return ["- No indexed code path selected. Inspect code only after clarifying the business flow."]
    return paths


def render_required_topics(matches: list[tuple[int, dict[str, str]]]) -> list[str]:
    topics: list[str] = []
    seen: set[str] = set()
    for _score, entry in matches:
        for topic in split_topics(entry.get("Required brief topics", "")):
            normalized = topic.lower()
            if normalized not in seen:
                seen.add(normalized)
                topics.append(f"- {topic}")
    if not topics:
        return ["- No indexed required topic selected."]
    return topics


def render_packet(task: str, context_dir: Path) -> str:
    context = read_context(context_dir)
    matches = matched_index_entries(task, context_dir)
    top_score = matches[0][0] if matches else 0
    confidence = confidence_for_score(top_score)
    mode = "READY_WITH_GUARDRAILS" if confidence != "LOW" else "NEEDS_CLARIFICATION"

    if confidence == "LOW":
        business = ranked_lines(task, context["business-model.md"], limit=4)
        rules = ["- Skipped: no strong indexed business flow matched the task."]
        flows = ["- Skipped: ask a focused product question before editing domain-sensitive code."]
        instructions = [
            "- Do not infer company policy from code shape alone.",
            "- Ask what business flow this task belongs to if it touches money, permissions, lifecycle state, user eligibility, operations, or external events.",
            "- If the task is clearly non-domain work, proceed with normal coding review.",
        ]
    else:
        business = ranked_lines(task, context["business-model.md"], limit=4)
        rules = ranked_lines(task, context["domain-rules.md"], limit=7)
        flows = ranked_lines(task, context["user-flows.md"] + context["operational-context.md"], limit=7)
        instructions = [
            "- Preserve the protected rules and flows below unless the user explicitly asks for a policy change.",
            "- Treat code as evidence of current behavior, not proof of the intended business rule.",
            "- Before editing, inspect the selected code paths and verify where each required topic is enforced.",
            "- If the simplest technical fix weakens a listed invariant, stop and ask for product confirmation.",
            "- Add or update tests that assert the business invariant, not only the implementation detail.",
            "- After editing, review the diff against the required topics and update Domain Guardian context if a new rule or exception was discovered.",
        ]

    return f"""# Domain Task Context Packet

- Task: {task}
- Context directory: {context_dir}
- Confidence: {confidence}
- Context mode: {mode}

## Business Model Context

{bullet_block(business)}

## Matched Business Flows

{bullet_block(render_matched_flows(matches))}

## Context Files To Read First

{bullet_block(render_context_files(matches))}

## Code Paths To Inspect

{bullet_block(render_code_paths(matches))}

## Protected Rules To Preserve

{bullet_block(rules)}

## User Or Operations Flows To Preserve

{bullet_block(flows)}

## Required Topics To Cover

{bullet_block(render_required_topics(matches))}

## AI Change Instructions

{bullet_block(instructions)}
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare business-flow context before a code change.")
    parser.add_argument("--task", required=True, help="The planned feature, bug fix, refactor, or review target.")
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

    packet = render_packet(args.task, context_dir)
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(packet, encoding="utf-8")
        print(f"WROTE: {output_path}")
    else:
        print(packet)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
