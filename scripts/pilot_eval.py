#!/usr/bin/env python3
"""Score a Domain Guardian A/B pilot against human-reviewed outcomes."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


CRITERIA = [
    "preserved_invariants",
    "used_relevant_context",
    "asked_when_unclear",
    "added_business_tests",
    "kept_context_updated",
]

TEMPLATE = {
    "pilot": "domain-guardian-a-b",
    "scale": "0=failed, 1=partial, 2=good",
    "criteria": CRITERIA,
    "tasks": [
        {
            "id": "paid-cancellation-example",
            "title": "Allow patients to cancel paid appointments",
            "expected_business_rule": "Settled paid appointments create a staff-reviewed cancellation request.",
            "baseline_without_domain_guardian": {
                "preserved_invariants": 0,
                "used_relevant_context": 0,
                "asked_when_unclear": 0,
                "added_business_tests": 1,
                "kept_context_updated": 0,
                "notes": "Example baseline score. Replace with reviewer findings.",
            },
            "guarded_with_domain_guardian": {
                "preserved_invariants": 2,
                "used_relevant_context": 2,
                "asked_when_unclear": 1,
                "added_business_tests": 2,
                "kept_context_updated": 1,
                "notes": "Example guarded score. Replace with reviewer findings.",
            },
        }
    ],
}

BLIND_REVIEW_TEMPLATE = {
    "pilot": "domain-guardian-blind-review",
    "reviewer": "reviewer-1",
    "scale": "0=failed, 1=partial, 2=good",
    "criteria": CRITERIA,
    "tasks": [
        {
            "id": "paid-cancellation-example",
            "title": "Allow patients to cancel paid appointments",
            "expected_business_rule": "Settled paid appointments create a staff-reviewed cancellation request.",
            "variant_a": {
                "preserved_invariants": None,
                "used_relevant_context": None,
                "asked_when_unclear": None,
                "added_business_tests": None,
                "kept_context_updated": None,
                "notes": "Score variant A without knowing whether it used Domain Guardian.",
            },
            "variant_b": {
                "preserved_invariants": None,
                "used_relevant_context": None,
                "asked_when_unclear": None,
                "added_business_tests": None,
                "kept_context_updated": None,
                "notes": "Score variant B without knowing whether it used Domain Guardian.",
            },
        }
    ],
}

BLIND_KEY_TEMPLATE = {
    "pilot": "domain-guardian-blind-key",
    "tasks": [
        {
            "id": "paid-cancellation-example",
            "variant_a": "baseline_without_domain_guardian",
            "variant_b": "guarded_with_domain_guardian",
        }
    ],
}

LOW_COST_TEMPLATES = {
    "plan-only": {
        "pilot": "domain-guardian-plan-only-a-b",
        "scale": "0=failed, 1=partial, 2=good",
        "criteria": CRITERIA,
        "review_instruction": "Ask both agents for an implementation plan only. Do not let either agent edit code.",
        "tasks": [
            {
                "id": "rush-booking-plan-example",
                "title": "Allow same-day rush stringing bookings",
                "expected_business_rule": "The plan should preserve cutoff, capacity, surcharge, pickup promise, and customer confirmation.",
                "baseline_without_domain_guardian": {
                    "preserved_invariants": 0,
                    "used_relevant_context": 0,
                    "asked_when_unclear": 0,
                    "added_business_tests": 1,
                    "kept_context_updated": 0,
                    "notes": "Score the baseline plan. Did it identify the business rules before implementation?",
                },
                "guarded_with_domain_guardian": {
                    "preserved_invariants": 2,
                    "used_relevant_context": 2,
                    "asked_when_unclear": 1,
                    "added_business_tests": 2,
                    "kept_context_updated": 1,
                    "notes": "Score the plan produced after prepare_change.py context was provided.",
                },
            }
        ],
    },
    "review-only": {
        "pilot": "domain-guardian-review-only-a-b",
        "scale": "0=failed, 1=partial, 2=good",
        "criteria": CRITERIA,
        "review_instruction": "Give both agents the same diff and ask for review only. Do not let either agent edit code.",
        "tasks": [
            {
                "id": "webhook-review-example",
                "title": "Review a simplified payment webhook diff",
                "expected_business_rule": "The review should catch replay/idempotency, deposit state, duplicate notification, and audit-event risks.",
                "baseline_without_domain_guardian": {
                    "preserved_invariants": 0,
                    "used_relevant_context": 0,
                    "asked_when_unclear": 0,
                    "added_business_tests": 1,
                    "kept_context_updated": 0,
                    "notes": "Score the context-free review. Did it catch business-rule regressions?",
                },
                "guarded_with_domain_guardian": {
                    "preserved_invariants": 2,
                    "used_relevant_context": 2,
                    "asked_when_unclear": 1,
                    "added_business_tests": 2,
                    "kept_context_updated": 1,
                    "notes": "Score the review produced after Domain Guardian context was provided.",
                },
            }
        ],
    },
}


@dataclass(frozen=True)
class SideScore:
    total: int
    max_total: int
    by_criterion: dict[str, int]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_template(path: Path, force: bool) -> int:
    if path.exists() and not force:
        print(f"FAIL: {path} already exists. Use --force to overwrite.")
        return 1
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(TEMPLATE, indent=2) + "\n", encoding="utf-8")
    print(f"WROTE: {path}")
    return 0


def write_blind_templates(review_path: Path, key_path: Path, force: bool) -> int:
    existing = [path for path in (review_path, key_path) if path.exists()]
    if existing and not force:
        print("FAIL: output file already exists. Use --force to overwrite.")
        for path in existing:
            print(f"  - {path}")
        return 1
    review_path.parent.mkdir(parents=True, exist_ok=True)
    key_path.parent.mkdir(parents=True, exist_ok=True)
    review_path.write_text(json.dumps(BLIND_REVIEW_TEMPLATE, indent=2) + "\n", encoding="utf-8")
    key_path.write_text(json.dumps(BLIND_KEY_TEMPLATE, indent=2) + "\n", encoding="utf-8")
    print(f"WROTE: {review_path}")
    print(f"WROTE: {key_path}")
    return 0


def write_low_cost_template(mode: str, path: Path, force: bool) -> int:
    if mode not in LOW_COST_TEMPLATES:
        print(f"FAIL: unsupported mode: {mode}")
        print(f"Supported modes: {', '.join(sorted(LOW_COST_TEMPLATES))}")
        return 1
    if path.exists() and not force:
        print(f"FAIL: {path} already exists. Use --force to overwrite.")
        return 1
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(LOW_COST_TEMPLATES[mode], indent=2) + "\n", encoding="utf-8")
    print(f"WROTE: {path}")
    return 0


def score_side(raw: dict[str, Any], task_id: str, side_name: str) -> SideScore:
    by_criterion: dict[str, int] = {}
    for criterion in CRITERIA:
        value = raw.get(criterion)
        if not isinstance(value, int) or value < 0 or value > 2:
            raise ValueError(f"{task_id}.{side_name}.{criterion} must be an integer from 0 to 2")
        by_criterion[criterion] = value
    return SideScore(total=sum(by_criterion.values()), max_total=len(CRITERIA) * 2, by_criterion=by_criterion)


def validate_task(raw: dict[str, Any]) -> None:
    task_id = str(raw.get("id", "unnamed-task"))
    for side in ("baseline_without_domain_guardian", "guarded_with_domain_guardian"):
        if side not in raw or not isinstance(raw[side], dict):
            raise ValueError(f"{task_id}.{side} is required")
        score_side(raw[side], task_id, side)


def pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def blind_key_by_task(key_data: dict[str, Any]) -> dict[str, dict[str, str]]:
    tasks = key_data.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        raise ValueError("blind key tasks must be a non-empty list")
    mapping: dict[str, dict[str, str]] = {}
    allowed = {"baseline_without_domain_guardian", "guarded_with_domain_guardian"}
    for raw_task in tasks:
        if not isinstance(raw_task, dict):
            raise ValueError("each blind key task must be an object")
        task_id = str(raw_task.get("id", ""))
        if not task_id:
            raise ValueError("blind key task id is required")
        variant_map: dict[str, str] = {}
        for variant in ("variant_a", "variant_b"):
            source = raw_task.get(variant)
            if source not in allowed:
                raise ValueError(f"{task_id}.{variant} must map to one of {sorted(allowed)}")
            variant_map[variant] = str(source)
        if set(variant_map.values()) != allowed:
            raise ValueError(f"{task_id} must map one variant to baseline and one variant to guarded")
        mapping[task_id] = variant_map
    return mapping


def render_blind_report(review_files: list[Path], key_data: dict[str, Any]) -> str:
    if not review_files:
        raise ValueError("at least one blind review file is required")
    key = blind_key_by_task(key_data)
    lines = ["# Domain Guardian Blind Pilot Evaluation", ""]
    baseline_total = 0
    guarded_total = 0
    max_total = 0
    improved_task_reviews = 0
    regressed_task_reviews = 0
    scored_task_reviews = 0
    criterion_deltas = {criterion: 0 for criterion in CRITERIA}
    task_deltas: dict[str, list[int]] = {}

    for review_file in review_files:
        review = load_json(review_file)
        reviewer = str(review.get("reviewer", review_file.name))
        tasks = review.get("tasks")
        if not isinstance(tasks, list) or not tasks:
            raise ValueError(f"{review_file}: tasks must be a non-empty list")
        for raw_task in tasks:
            if not isinstance(raw_task, dict):
                raise ValueError(f"{review_file}: each task must be an object")
            task_id = str(raw_task.get("id", ""))
            if task_id not in key:
                raise ValueError(f"{review_file}: no blind key mapping for task {task_id}")
            variant_scores = {
                "variant_a": score_side(raw_task.get("variant_a", {}), task_id, "variant_a"),
                "variant_b": score_side(raw_task.get("variant_b", {}), task_id, "variant_b"),
            }
            by_source = {key[task_id][variant]: score for variant, score in variant_scores.items()}
            baseline = by_source["baseline_without_domain_guardian"]
            guarded = by_source["guarded_with_domain_guardian"]
            delta = guarded.total - baseline.total
            baseline_total += baseline.total
            guarded_total += guarded.total
            max_total += baseline.max_total
            scored_task_reviews += 1
            task_deltas.setdefault(task_id, []).append(delta)
            if delta > 0:
                improved_task_reviews += 1
            elif delta < 0:
                regressed_task_reviews += 1
            for criterion in CRITERIA:
                criterion_deltas[criterion] += guarded.by_criterion[criterion] - baseline.by_criterion[criterion]
            lines.append(f"## {task_id} ({reviewer})")
            lines.append("")
            lines.append(f"- Baseline score: {baseline.total}/{baseline.max_total}")
            lines.append(f"- Guarded score: {guarded.total}/{guarded.max_total}")
            lines.append(f"- Delta: {delta:+d}")
            if raw_task.get("expected_business_rule"):
                lines.append(f"- Expected business rule: {raw_task['expected_business_rule']}")
            lines.append("")

    total_delta = guarded_total - baseline_total
    lines.insert(2, f"- Review files: {len(review_files)}")
    lines.insert(3, f"- Scored task reviews: {scored_task_reviews}")
    lines.insert(4, f"- Baseline total: {baseline_total}/{max_total} ({pct(baseline_total / max_total)})")
    lines.insert(5, f"- Guarded total: {guarded_total}/{max_total} ({pct(guarded_total / max_total)})")
    lines.insert(6, f"- Total delta: {total_delta:+d}")
    lines.insert(7, f"- Improved task reviews: {improved_task_reviews}")
    lines.insert(8, f"- Regressed task reviews: {regressed_task_reviews}")
    lines.insert(9, "")
    lines.insert(10, "## Criterion Deltas")
    lines.insert(11, "")
    for index, criterion in enumerate(CRITERIA, start=12):
        lines.insert(index, f"- {criterion}: {criterion_deltas[criterion]:+d}")
    insert_at = 12 + len(CRITERIA)
    lines.insert(insert_at, "")
    lines.insert(insert_at + 1, "## Task Delta Summary")
    lines.insert(insert_at + 2, "")
    for offset, (task_id, deltas) in enumerate(sorted(task_deltas.items()), start=insert_at + 3):
        average = sum(deltas) / len(deltas)
        lines.insert(offset, f"- {task_id}: avg delta {average:+.1f} across {len(deltas)} review(s)")

    if regressed_task_reviews:
        lines.append("## Blind Pilot Decision")
        lines.append("")
        lines.append("- NEEDS WORK: guarded runs regressed in at least one blinded task review.")
    elif total_delta <= 0:
        lines.append("## Blind Pilot Decision")
        lines.append("")
        lines.append("- INCONCLUSIVE: guarded runs did not improve the aggregate blinded score.")
    else:
        lines.append("## Blind Pilot Decision")
        lines.append("")
        lines.append("- PROMISING: guarded runs improved the aggregate blinded score without task-level regression.")
    return "\n".join(lines) + "\n"


def render_report(data: dict[str, Any]) -> str:
    tasks = data.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        raise ValueError("tasks must be a non-empty list")

    lines = ["# Domain Guardian Pilot Evaluation", ""]
    baseline_total = 0
    guarded_total = 0
    max_total = 0
    improved_tasks = 0
    regressed_tasks = 0
    criterion_deltas = {criterion: 0 for criterion in CRITERIA}

    for raw_task in tasks:
        if not isinstance(raw_task, dict):
            raise ValueError("each task must be an object")
        validate_task(raw_task)
        task_id = str(raw_task.get("id", "unnamed-task"))
        title = str(raw_task.get("title", task_id))
        baseline = score_side(raw_task["baseline_without_domain_guardian"], task_id, "baseline_without_domain_guardian")
        guarded = score_side(raw_task["guarded_with_domain_guardian"], task_id, "guarded_with_domain_guardian")
        delta = guarded.total - baseline.total
        baseline_total += baseline.total
        guarded_total += guarded.total
        max_total += baseline.max_total
        if delta > 0:
            improved_tasks += 1
        elif delta < 0:
            regressed_tasks += 1
        for criterion in CRITERIA:
            criterion_deltas[criterion] += guarded.by_criterion[criterion] - baseline.by_criterion[criterion]
        lines.append(f"## {task_id}: {title}")
        lines.append("")
        lines.append(f"- Baseline score: {baseline.total}/{baseline.max_total}")
        lines.append(f"- Guarded score: {guarded.total}/{guarded.max_total}")
        lines.append(f"- Delta: {delta:+d}")
        if raw_task.get("expected_business_rule"):
            lines.append(f"- Expected business rule: {raw_task['expected_business_rule']}")
        lines.append("")

    total_delta = guarded_total - baseline_total
    lines.insert(2, f"- Tasks: {len(tasks)}")
    lines.insert(3, f"- Baseline total: {baseline_total}/{max_total} ({pct(baseline_total / max_total)})")
    lines.insert(4, f"- Guarded total: {guarded_total}/{max_total} ({pct(guarded_total / max_total)})")
    lines.insert(5, f"- Total delta: {total_delta:+d}")
    lines.insert(6, f"- Improved tasks: {improved_tasks}")
    lines.insert(7, f"- Regressed tasks: {regressed_tasks}")
    lines.insert(8, "")
    lines.insert(9, "## Criterion Deltas")
    lines.insert(10, "")
    for index, criterion in enumerate(CRITERIA, start=11):
        lines.insert(index, f"- {criterion}: {criterion_deltas[criterion]:+d}")
    lines.insert(11 + len(CRITERIA), "")

    if regressed_tasks:
        lines.append("## Pilot Decision")
        lines.append("")
        lines.append("- NEEDS WORK: guarded runs regressed on at least one task.")
    elif total_delta <= 0:
        lines.append("## Pilot Decision")
        lines.append("")
        lines.append("- INCONCLUSIVE: guarded runs did not improve the aggregate score.")
    else:
        lines.append("## Pilot Decision")
        lines.append("")
        lines.append("- PROMISING: guarded runs improved the aggregate score without task-level regression.")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Initialize or report on a Domain Guardian pilot evaluation.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser("init", help="Write a pilot scoring template.")
    init.add_argument("--output", required=True, help="Output JSON path.")
    init.add_argument("--force", action="store_true", help="Overwrite an existing output file.")

    report = subparsers.add_parser("report", help="Render a markdown report from pilot scores.")
    report.add_argument("--input", required=True, help="Input pilot JSON path.")
    report.add_argument("--output", help="Optional markdown report path.")

    blind_init = subparsers.add_parser("blind-init", help="Write separate blind review and answer key templates.")
    blind_init.add_argument("--review-output", required=True, help="Output blind review JSON path.")
    blind_init.add_argument("--key-output", required=True, help="Output answer key JSON path.")
    blind_init.add_argument("--force", action="store_true", help="Overwrite existing output files.")

    blind_report = subparsers.add_parser("blind-report", help="Render a markdown report from blind review scores.")
    blind_report.add_argument("--review", action="append", required=True, help="Blind review JSON path. Repeat for multiple reviewers.")
    blind_report.add_argument("--key", required=True, help="Blind answer key JSON path.")
    blind_report.add_argument("--output", help="Optional markdown report path.")

    low_cost_init = subparsers.add_parser("low-cost-init", help="Write a plan-only or review-only scoring template.")
    low_cost_init.add_argument("--mode", required=True, choices=sorted(LOW_COST_TEMPLATES), help="Low-cost pilot mode.")
    low_cost_init.add_argument("--output", required=True, help="Output scoring JSON path.")
    low_cost_init.add_argument("--force", action="store_true", help="Overwrite an existing output file.")

    args = parser.parse_args()
    if args.command == "init":
        return write_template(Path(args.output), args.force)
    if args.command == "blind-init":
        return write_blind_templates(Path(args.review_output), Path(args.key_output), args.force)
    if args.command == "low-cost-init":
        return write_low_cost_template(args.mode, Path(args.output), args.force)

    try:
        if args.command == "report":
            rendered = render_report(load_json(Path(args.input)))
        else:
            rendered = render_blind_report([Path(path) for path in args.review], load_json(Path(args.key)))
    except (json.JSONDecodeError, ValueError) as error:
        print(f"FAIL: {error}")
        return 1

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8")
        print(f"WROTE: {output_path}")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
