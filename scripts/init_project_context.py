#!/usr/bin/env python3
"""Initialize a project-local Domain Guardian context directory."""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil


REQUIRED_FILES = [
    "index.md",
    "business-model.md",
    "domain-rules.md",
    "user-flows.md",
    "operational-context.md",
    "code-map.md",
]


def plugin_root() -> Path:
    return Path(__file__).resolve().parents[1]


def copy_templates(project_root: Path, context_dir_name: str, force: bool) -> tuple[list[Path], list[Path]]:
    source_dir = plugin_root() / "knowledge"
    target_dir = project_root / context_dir_name
    target_dir.mkdir(parents=True, exist_ok=True)

    copied: list[Path] = []
    skipped: list[Path] = []

    for filename in REQUIRED_FILES:
        source = source_dir / filename
        target = target_dir / filename
        if target.exists() and not force:
            skipped.append(target)
            continue
        shutil.copyfile(source, target)
        copied.append(target)

    return copied, skipped


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a project-local Domain Guardian context.")
    parser.add_argument(
        "project_root",
        nargs="?",
        default=".",
        help="Project root where the context directory should be created.",
    )
    parser.add_argument(
        "--context-dir",
        default=".domain-guardian",
        help="Context directory name inside the project root.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing context files.",
    )
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    if not project_root.exists():
        print(f"FAIL: project root does not exist: {project_root}")
        return 1
    if not project_root.is_dir():
        print(f"FAIL: project root is not a directory: {project_root}")
        return 1

    copied, skipped = copy_templates(project_root, args.context_dir, args.force)
    print(f"Domain Guardian context: {project_root / args.context_dir}")
    for path in copied:
        print(f"CREATED: {path}")
    for path in skipped:
        print(f"SKIPPED: {path} already exists")

    if skipped and not args.force:
        print("Use --force only when you intentionally want to replace existing context files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
