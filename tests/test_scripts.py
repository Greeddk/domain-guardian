from __future__ import annotations

from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_DIFF = """diff --git a/app/appointments/cancel.ts b/app/appointments/cancel.ts
index 1111111..2222222 100644
--- a/app/appointments/cancel.ts
+++ b/app/appointments/cancel.ts
@@ -1,4 +1,4 @@
- if (payment.state === "settled") return createCancellationRequest()
+ if (payment.state === "settled") return cancelAppointment()
"""


class ScriptTests(unittest.TestCase):
    def run_script(
        self,
        *args: str,
        cwd: Path | None = None,
        input_text: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, *args],
            cwd=cwd or PLUGIN_ROOT,
            input=input_text,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_init_project_context_copies_templates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_script("scripts/init_project_context.py", tmp)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            context_dir = Path(tmp) / ".domain-guardian"
            self.assertTrue((context_dir / "index.md").exists())
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

    def test_install_claude_copies_commands_with_plugin_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_script("scripts/install_claude.py", tmp)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            command = Path(tmp) / ".claude" / "commands" / "domain-prepare.md"
            claude_md = Path(tmp) / "CLAUDE.md"
            self.assertTrue(command.exists())
            self.assertTrue(claude_md.exists())
            command_text = command.read_text(encoding="utf-8")
            self.assertIn(str(PLUGIN_ROOT), command_text)
            self.assertNotIn("{{DOMAIN_GUARDIAN_ROOT}}", command_text)
            self.assertIn("Domain Guardian", claude_md.read_text(encoding="utf-8"))

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
        self.assertIn("OK: index-code-map coverage", result.stdout)

    def test_check_context_flags_index_code_missing_from_code_map(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            shared = """# Filled

- Source or owner: operations lead.
- Product: example.
- Rule: example rule.
- Flow: example flow.
- Concept: example concept.
- Detail: one.
- Detail: two.
- Detail: three.
- Detail: four.
- Detail: five.
- Detail: six.
- Detail: seven.
"""
            for filename in (
                "business-model.md",
                "domain-rules.md",
                "user-flows.md",
                "operational-context.md",
            ):
                (base / filename).write_text(shared, encoding="utf-8")
            (base / "index.md").write_text(
                """# Domain Context Index

- Area: missing code map path
  - Keywords: booking, payment, state
  - Read: `domain-rules.md`, `user-flows.md`, `code-map.md`
  - Code: `app/bookings/create.ts`
  - Owners: operations lead
  - Risk: missing code map coverage weakens pre-change context.
  - Required brief topics: booking state, owner, side effects.
""",
                encoding="utf-8",
            )
            (base / "code-map.md").write_text(
                shared + "\n- Files: `app/bookings/cancel.ts`.\n",
                encoding="utf-8",
            )

            result = self.run_script("scripts/check_context.py", str(base))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("NEEDS WORK: index-code-map coverage", result.stdout)
            self.assertIn("index code path missing from code-map: app/bookings/create.ts", result.stdout)

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
        self.assertIn("Selected Context From Index", result.stdout)

    def test_task_context_packet_instructs_agent_with_business_flow(self) -> None:
        result = self.run_script(
            "scripts/task_context.py",
            "--task",
            "Allow patients to cancel paid appointments",
            "--knowledge-dir",
            "examples/clinic-scheduling/.domain-guardian",
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("# Domain Task Context Packet", result.stdout)
        self.assertIn("Context mode: READY_WITH_GUARDRAILS", result.stdout)
        self.assertIn("cancellation request for settled appointment", result.stdout.lower())
        self.assertIn("Preserve the protected rules and flows", result.stdout)
        self.assertIn("settlement state", result.stdout)

    def test_task_context_low_confidence_asks_before_policy_guessing(self) -> None:
        result = self.run_script(
            "scripts/task_context.py",
            "--task",
            "Update homepage marketing copy",
            "--knowledge-dir",
            "examples/clinic-scheduling/.domain-guardian",
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("Confidence: LOW", result.stdout)
        self.assertIn("Context mode: NEEDS_CLARIFICATION", result.stdout)
        self.assertIn("Do not infer company policy from code shape alone", result.stdout)
        self.assertNotIn("settled paid appointment cannot be patient-cancelled directly", result.stdout)

    def test_prepare_change_writes_task_context_and_brief(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_script(
                "scripts/prepare_change.py",
                "--task",
                "Allow patients to cancel paid appointments",
                "--knowledge-dir",
                "examples/clinic-scheduling/.domain-guardian",
                "--output-dir",
                tmp,
            )
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            context_path = Path(tmp) / "task-context.md"
            brief_path = Path(tmp) / "domain-impact-brief.md"
            self.assertTrue(context_path.exists())
            self.assertTrue(brief_path.exists())
            self.assertIn("WROTE", result.stdout)
            self.assertIn("Domain Task Context Packet", context_path.read_text(encoding="utf-8"))
            self.assertIn("Domain Impact Brief", brief_path.read_text(encoding="utf-8"))

    def test_prepare_change_strict_low_confidence_blocks_pre_change(self) -> None:
        result = self.run_script(
            "scripts/prepare_change.py",
            "--task",
            "Update homepage marketing copy",
            "--knowledge-dir",
            "examples/clinic-scheduling/.domain-guardian",
            "--strict",
        )
        self.assertEqual(result.returncode, 2, result.stderr + result.stdout)
        self.assertIn("Confidence: LOW", result.stdout)
        self.assertIn("NEEDS CLARIFICATION", result.stdout)

    def test_pilot_eval_init_and_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            scores = Path(tmp) / "pilot.json"
            init = self.run_script("scripts/pilot_eval.py", "init", "--output", str(scores))
            self.assertEqual(init.returncode, 0, init.stderr + init.stdout)
            self.assertTrue(scores.exists())

            report = self.run_script("scripts/pilot_eval.py", "report", "--input", str(scores))
            self.assertEqual(report.returncode, 0, report.stderr + report.stdout)
            self.assertIn("# Domain Guardian Pilot Evaluation", report.stdout)
            self.assertIn("Total delta: +7", report.stdout)
            self.assertIn("PROMISING", report.stdout)

    def test_pilot_eval_rejects_invalid_scores(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            scores = Path(tmp) / "pilot.json"
            scores.write_text(
                json.dumps(
                    {
                        "tasks": [
                            {
                                "id": "invalid",
                                "baseline_without_domain_guardian": {
                                    "preserved_invariants": 3,
                                    "used_relevant_context": 0,
                                    "asked_when_unclear": 0,
                                    "added_business_tests": 0,
                                    "kept_context_updated": 0,
                                },
                                "guarded_with_domain_guardian": {
                                    "preserved_invariants": 0,
                                    "used_relevant_context": 0,
                                    "asked_when_unclear": 0,
                                    "added_business_tests": 0,
                                    "kept_context_updated": 0,
                                },
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            report = self.run_script("scripts/pilot_eval.py", "report", "--input", str(scores))
            self.assertEqual(report.returncode, 1, report.stderr + report.stdout)
            self.assertIn("must be an integer from 0 to 2", report.stdout)

    def test_pilot_eval_blind_init_and_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            review = Path(tmp) / "blind-review.json"
            key = Path(tmp) / "blind-key.json"
            init = self.run_script(
                "scripts/pilot_eval.py",
                "blind-init",
                "--review-output",
                str(review),
                "--key-output",
                str(key),
            )
            self.assertEqual(init.returncode, 0, init.stderr + init.stdout)
            self.assertTrue(review.exists())
            self.assertTrue(key.exists())

            review.write_text(
                json.dumps(
                    {
                        "pilot": "domain-guardian-blind-review",
                        "reviewer": "reviewer-1",
                        "criteria": [
                            "preserved_invariants",
                            "used_relevant_context",
                            "asked_when_unclear",
                            "added_business_tests",
                            "kept_context_updated",
                        ],
                        "tasks": [
                            {
                                "id": "paid-cancellation-example",
                                "title": "Allow patients to cancel paid appointments",
                                "expected_business_rule": "Settled paid appointments create a staff-reviewed cancellation request.",
                                "variant_a": {
                                    "preserved_invariants": 0,
                                    "used_relevant_context": 0,
                                    "asked_when_unclear": 0,
                                    "added_business_tests": 1,
                                    "kept_context_updated": 0,
                                },
                                "variant_b": {
                                    "preserved_invariants": 2,
                                    "used_relevant_context": 2,
                                    "asked_when_unclear": 1,
                                    "added_business_tests": 2,
                                    "kept_context_updated": 1,
                                },
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            report = self.run_script(
                "scripts/pilot_eval.py",
                "blind-report",
                "--review",
                str(review),
                "--key",
                str(key),
            )
            self.assertEqual(report.returncode, 0, report.stderr + report.stdout)
            self.assertIn("# Domain Guardian Blind Pilot Evaluation", report.stdout)
            self.assertIn("Total delta: +7", report.stdout)
            self.assertIn("PROMISING", report.stdout)

    def test_pilot_eval_low_cost_init_plan_only_and_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            scores = Path(tmp) / "plan-only.json"
            init = self.run_script(
                "scripts/pilot_eval.py",
                "low-cost-init",
                "--mode",
                "plan-only",
                "--output",
                str(scores),
            )
            self.assertEqual(init.returncode, 0, init.stderr + init.stdout)
            data = json.loads(scores.read_text(encoding="utf-8"))
            self.assertEqual(data["pilot"], "domain-guardian-plan-only-a-b")
            self.assertIn("implementation plan only", data["review_instruction"])

            report = self.run_script("scripts/pilot_eval.py", "report", "--input", str(scores))
            self.assertEqual(report.returncode, 0, report.stderr + report.stdout)
            self.assertIn("# Domain Guardian Pilot Evaluation", report.stdout)
            self.assertIn("PROMISING", report.stdout)

    def test_pilot_eval_low_cost_init_review_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            scores = Path(tmp) / "review-only.json"
            init = self.run_script(
                "scripts/pilot_eval.py",
                "low-cost-init",
                "--mode",
                "review-only",
                "--output",
                str(scores),
            )
            self.assertEqual(init.returncode, 0, init.stderr + init.stdout)
            data = json.loads(scores.read_text(encoding="utf-8"))
            self.assertEqual(data["pilot"], "domain-guardian-review-only-a-b")
            self.assertIn("review only", data["review_instruction"])

    def test_check_brief_accepts_sample_brief(self) -> None:
        result = self.run_script(
            "scripts/check_brief.py",
            "examples/outputs/sample-domain-impact-brief.md",
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("OK", result.stdout)

    def test_analyze_diff_uses_index_and_requires_brief(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            diff_path = Path(tmp) / "change.diff"
            diff_path.write_text(SAMPLE_DIFF, encoding="utf-8")
            missing = self.run_script(
                "scripts/analyze_diff.py",
                "--diff-file",
                str(diff_path),
                "--knowledge-dir",
                "examples/clinic-scheduling/.domain-guardian",
                "--require-brief",
            )
            self.assertNotEqual(missing.returncode, 0)
            self.assertIn("paid appointment cancellation", missing.stdout)
            self.assertIn("NEEDS WORK", missing.stdout)

            with_brief = self.run_script(
                "scripts/analyze_diff.py",
                "--diff-file",
                str(diff_path),
                "--knowledge-dir",
                "examples/clinic-scheduling/.domain-guardian",
                "--require-brief",
                "--brief",
                "examples/outputs/sample-domain-impact-brief.md",
            )
            self.assertEqual(with_brief.returncode, 0, with_brief.stderr + with_brief.stdout)
            self.assertIn("Risk level: HIGH", with_brief.stdout)
            self.assertIn("OK: Domain Impact Brief", with_brief.stdout)

    def test_analyze_diff_low_risk_does_not_dump_unrelated_rules(self) -> None:
        low_risk = self.run_script(
            "scripts/analyze_diff.py",
            "--knowledge-dir",
            "examples/clinic-scheduling/.domain-guardian",
            input_text="""diff --git a/README.md b/README.md
--- a/README.md
+++ b/README.md
@@ -1,1 +1,1 @@
- Old wording
+ New wording
""",
        )
        self.assertEqual(low_risk.returncode, 0, low_risk.stderr + low_risk.stdout)
        self.assertIn("Risk level: LOW", low_risk.stdout)
        self.assertIn("Skipped for LOW risk", low_risk.stdout)
        self.assertNotIn("settled paid appointment cannot be patient-cancelled directly", low_risk.stdout)

    def test_analyze_diff_ignores_generic_state_outside_domain_flow(self) -> None:
        low_risk = self.run_script(
            "scripts/analyze_diff.py",
            "--knowledge-dir",
            "examples/clinic-scheduling/.domain-guardian",
            input_text="""diff --git a/app/components/Button.tsx b/app/components/Button.tsx
--- a/app/components/Button.tsx
+++ b/app/components/Button.tsx
@@ -1,3 +1,4 @@
 export function Button({ children }) {
+  const [state, setState] = useState("idle")
   return <button>{children}</button>
 }
""",
        )
        self.assertEqual(low_risk.returncode, 0, low_risk.stderr + low_risk.stdout)
        self.assertIn("Risk level: LOW", low_risk.stdout)

    def test_analyze_diff_ignores_low_signal_fixture_webhook(self) -> None:
        low_risk = self.run_script(
            "scripts/analyze_diff.py",
            "--knowledge-dir",
            "examples/clinic-scheduling/.domain-guardian",
            input_text="""diff --git a/tests/fixtures/webhook.json b/tests/fixtures/webhook.json
--- a/tests/fixtures/webhook.json
+++ b/tests/fixtures/webhook.json
@@ -1,1 +1,1 @@
- {"type": "payment.succeeded", "id": "evt_1"}
+ {"type": "payment.succeeded", "id": "evt_2"}
""",
        )
        self.assertEqual(low_risk.returncode, 0, low_risk.stderr + low_risk.stdout)
        self.assertIn("Risk level: LOW", low_risk.stdout)

    def test_domain_brief_low_confidence_does_not_invent_context(self) -> None:
        result = self.run_script(
            "scripts/domain_brief.py",
            "--task",
            "Update homepage marketing copy",
            "--knowledge-dir",
            "examples/clinic-scheduling/.domain-guardian",
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("Confidence: LOW", result.stdout)
        self.assertIn("No strong index match", result.stdout)
        self.assertNotIn("settled paid appointment cannot be patient-cancelled directly", result.stdout)

    def test_check_brief_requires_index_topics_when_provided(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            brief = Path(tmp) / "generic.md"
            brief.write_text(
                """# Domain Impact Brief

## Relevant Business Context
- Generic context

## Relevant Business Rules
- Generic rule

## Relevant User Or Operations Flows
- Generic flow

## Code Areas Likely Involved
- Generic code

## Protected Invariants
- Generic invariant

## Ambiguities Or Questions
- Generic question

## Test Or Review Guardrails
- Generic guardrail
- Extra bullet
- Extra bullet
- Extra bullet
""",
                encoding="utf-8",
            )
            result = self.run_script(
                "scripts/check_brief.py",
                str(brief),
                "--required-topic",
                "refund side effect",
                "--required-topic",
                "audit event",
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing required topic: refund side effect", result.stdout)
            self.assertIn("missing required topic: audit event", result.stdout)

    def test_analyze_diff_validates_required_topics_from_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            diff_path = Path(tmp) / "change.diff"
            diff_path.write_text(SAMPLE_DIFF, encoding="utf-8")
            generic_brief = Path(tmp) / "generic.md"
            generic_brief.write_text(
                """# Domain Impact Brief

## Relevant Business Context
- Generic context

## Relevant Business Rules
- Generic rule

## Relevant User Or Operations Flows
- Generic flow

## Code Areas Likely Involved
- Generic code

## Protected Invariants
- Generic invariant

## Ambiguities Or Questions
- Generic question

## Test Or Review Guardrails
- Generic guardrail
- Extra bullet
- Extra bullet
- Extra bullet
""",
                encoding="utf-8",
            )
            result = self.run_script(
                "scripts/analyze_diff.py",
                "--diff-file",
                str(diff_path),
                "--knowledge-dir",
                "examples/clinic-scheduling/.domain-guardian",
                "--require-brief",
                "--brief",
                str(generic_brief),
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Confidence: HIGH", result.stdout)
            self.assertIn("missing required topic", result.stdout)


if __name__ == "__main__":
    unittest.main()
