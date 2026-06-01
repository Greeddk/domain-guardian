---
name: domain-context
description: Use before feature work, bug fixes, refactors, or code review when project-specific business rules, user flows, permissions, pricing, lifecycle states, operational policies, or hidden product assumptions may affect the change.
---

# Domain Context

Domain Guardian reduces the risk of context-blind code changes: code that is syntactically valid and locally reasonable, but wrong for the product's business rules.

Use this skill when a user asks to:

- onboard a project into Domain Guardian,
- explain or update business/domain context,
- implement a feature or bug fix in a domain-heavy area,
- review a diff for business-rule risk,
- change logic related to pricing, permissions, eligibility, lifecycle states, matching, ranking, moderation, billing, fulfillment, notifications, data retention, or operational workflows.

## Required Knowledge Files

Read these files from the plugin or project copy before making domain-sensitive changes:

- `knowledge/business-model.md`
- `knowledge/domain-rules.md`
- `knowledge/user-flows.md`
- `knowledge/operational-context.md`
- `knowledge/code-map.md`

If the current repository has its own `.domain-guardian/` or `docs/domain-guardian/` directory, prefer that project-local knowledge over the plugin's starter templates. If neither exists, ask to initialize one or use `scripts/init_project_context.py`.

## Operating Modes

### 1. Onboarding Mode

Use when the knowledge files are empty, vague, or missing.

Ask one focused question at a time. Do not ask a long questionnaire all at once.

Start with these questions in order:

1. What does this product sell or enable, and who pays for it?
2. What user action or business outcome must never be broken?
3. What are the most important domain entities and lifecycle states?
4. Which rules are policy decisions rather than technical constraints?
5. Which user flows produce money, trust, compliance, or operational workload?
6. Which edge cases have caused incidents or expensive support work?
7. Which code paths enforce these rules?

After each answer in agent-led onboarding:

- summarize the answer in 3-7 bullets,
- identify which knowledge file should be updated,
- ask before making broad rewrites,
- keep facts separate from assumptions.

The helper script `scripts/bootstrap_context.py` is intentionally simpler: it captures raw first-pass notes. The agent should polish those notes into 3-7 bullets when updating project context during a real coding session.

### 2. Pre-Change Mode

Before editing code, produce a Domain Impact Brief:

```text
Domain Impact Brief
- Task:
- Relevant business rule(s):
- Relevant user/ops flow(s):
- Code areas likely involved:
- Protected invariants:
- Ambiguities or questions:
- Test or review guardrails:
```

If any protected invariant is unclear, ask the user before editing.

You may use `scripts/domain_brief.py --task "<task>" --knowledge-dir <dir>` to create a draft, but the final brief must still reflect your own reading of the code and the user's latest request.

### 3. Code Review Mode

When reviewing a diff, lead with findings. Look for:

- removed validations,
- broadened permissions,
- changed lifecycle transitions,
- altered pricing or eligibility,
- changed defaults,
- skipped notifications or audit trails,
- weaker idempotency or retry behavior,
- operational flows that now require manual cleanup,
- tests that assert implementation details but not business invariants.

For each issue, explain:

- the changed code,
- the domain rule it may violate,
- the user or business consequence,
- the concrete fix or question needed.

### 4. Context Update Mode

When work reveals a new rule or exception, update the knowledge base. Add:

- source of the rule,
- rule owner if known,
- affected code paths,
- examples and counterexamples,
- date discovered.

Do not overwrite a rule just because code disagrees with it. Treat disagreement as a product question.

## Decision Rules

- Prefer explicit user confirmation over guessing business policy.
- Treat tests as evidence, not truth. Tests can encode incomplete domain knowledge.
- Separate "the code currently does this" from "the business requires this."
- If a change seems technically simpler but weakens a protected business flow, stop and ask.
- If a rule has exceptions, preserve the exception list as carefully as the rule.

## Completion Checklist

Before saying the task is complete, confirm:

- the relevant knowledge files were read or the absence was reported,
- a Domain Impact Brief was produced for domain-sensitive code changes,
- tests or review notes cover the protected business invariants,
- any newly discovered rule was added or proposed as a knowledge update.
