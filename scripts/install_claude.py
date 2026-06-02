#!/usr/bin/env python3
"""Install Domain Guardian Claude Code commands into a target project."""

from __future__ import annotations

import argparse
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_DIR = PLUGIN_ROOT / "claude"
COMMAND_TEMPLATE_DIR = TEMPLATE_DIR / "commands"


def render_template(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("{{DOMAIN_GUARDIAN_ROOT}}", str(PLUGIN_ROOT))


def install_commands(project_dir: Path, force: bool) -> list[Path]:
    output_dir = project_dir / ".claude" / "commands"
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for template in sorted(COMMAND_TEMPLATE_DIR.glob("*.md")):
        output = output_dir / template.name
        if output.exists() and not force:
            continue
        output.write_text(render_template(template), encoding="utf-8")
        written.append(output)
    return written


def install_claude_md(project_dir: Path, force: bool) -> Path | None:
    output = project_dir / "CLAUDE.md"
    rendered = render_template(TEMPLATE_DIR / "CLAUDE.md")
    if output.exists() and not force:
        return None
    output.write_text(rendered, encoding="utf-8")
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Install Domain Guardian Claude Code commands.")
    parser.add_argument("project_dir", help="Target project directory.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing Claude command files and CLAUDE.md.")
    parser.add_argument(
        "--skip-claude-md",
        action="store_true",
        help="Only install .claude/commands files; do not write CLAUDE.md.",
    )
    args = parser.parse_args()

    project_dir = Path(args.project_dir)
    if not project_dir.exists():
        print(f"FAIL: project directory not found: {project_dir}")
        return 1

    written_commands = install_commands(project_dir, args.force)
    for path in written_commands:
        print(f"WROTE: {path}")
    if not written_commands:
        print("SKIPPED: Claude command files already exist. Use --force to overwrite.")

    if not args.skip_claude_md:
        claude_md = install_claude_md(project_dir, args.force)
        if claude_md is None:
            print("SKIPPED: CLAUDE.md already exists. Use --force to overwrite.")
        else:
            print(f"WROTE: {claude_md}")

    print("OK: Domain Guardian Claude Code support installed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
