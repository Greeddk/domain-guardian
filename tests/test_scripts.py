from __future__ import annotations

from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest


PLUGIN_ROOT = Path(__file__).resolve().parents[1]


class ScriptTests(unittest.TestCase):
    def run_script(self, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, *args],
            cwd=cwd or PLUGIN_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_init_project_context_copies_templates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_script("scripts/init_project_context.py", tmp)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            context_dir = Path(tmp) / ".domain-guardian"
            self.assertTrue((context_dir / "business-model.md").exists())
            self.assertTrue((context_dir / "domain-rules.md").exists())

            changed = context_dir / "business-model.md"
            changed.write_text("custom", encoding="utf-8")
            skipped = self.run_script("scripts/init_project_context.py", tmp)
            self.assertIn("SKIPPED", skipped.stdout)
            self.assertEqual(changed.read_text(encoding="utf-8"), "custom")

            forced = self.run_script("scripts/init_project_context.py", tmp, "--force")
            self.assertEqual(forced.returncode, 0, forced.stderr + forced.stdout)
            self.assertIn("Business Model", changed.read_text(encoding="utf-8"))

    def test_manifest_has_publish_metadata(self) -> None:
        manifest = json.loads((PLUGIN_ROOT / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["name"], "domain-guardian")
        self.assertEqual(manifest["license"], "MIT")
        self.assertIn("repository", manifest)
        self.assertIsInstance(manifest["interface"]["defaultPrompt"], list)

    def test_check_context_flags_empty_templates(self) -> None:
        result = self.run_script("scripts/check_context.py", "knowledge")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("NEEDS WORK", result.stdout)

    def test_check_context_accepts_filled_example(self) -> None:
        result = self.run_script(
            "scripts/check_context.py",
            "examples/clinic-scheduling/.domain-guardian",
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("enough structure", result.stdout)

    def test_domain_brief_renders_task(self) -> None:
        result = self.run_script(
            "scripts/domain_brief.py",
            "--task",
            "Change paid booking cancellation rules",
            "--knowledge-dir",
            "knowledge",
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("# Domain Impact Brief", result.stdout)
        self.assertIn("Change paid booking cancellation rules", result.stdout)

    def test_domain_brief_prioritizes_paid_cancellation_context(self) -> None:
        result = self.run_script(
            "scripts/domain_brief.py",
            "--task",
            "Allow patients to cancel paid appointments",
            "--knowledge-dir",
            "examples/clinic-scheduling/.domain-guardian",
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("settled paid appointment cannot be patient-cancelled directly", result.stdout)
        self.assertIn("cancellation request for settled appointment", result.stdout.lower())


if __name__ == "__main__":
    unittest.main()
