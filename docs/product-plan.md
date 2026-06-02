# Product Plan

Date: 2026-06-01

## Product Thesis

Domain Guardian helps AI coding agents avoid context-blind changes: code that is technically valid
but wrong for a company's domain rules, business model, user flows, or operations.

## Target Users

- Engineering teams using AI coding agents in production codebases.
- Founders and product engineers whose business rules live partly in people, docs, incidents, and support history.
- Reviewers who need AI-assisted PR review to catch policy and workflow regressions, not only syntax or test failures.

## MVP Scope

- A Codex plugin with one primary skill: `domain-context`.
- Claude Code support through project slash commands and `CLAUDE.md`.
- A project-local knowledge base template.
- Interactive onboarding that asks focused questions and appends answers to the right context files.
- A context completeness checker.
- A Domain Impact Brief generator.
- An indexed task-context packet that tells the agent which business flow, rules, code paths, and required topics to use before editing.
- A pre-change entrypoint that generates both the task context packet and a draft brief.
- A diff-risk analyzer that can require a valid brief for domain-sensitive changes.
- A pilot evaluation rubric for comparing AI output with and without Domain Guardian.
- English README and development checks.

## Out Of Scope For MVP

- Automatic semantic indexing of the full codebase.
- CI integration that blocks PRs.
- Vector search, embeddings, or remote storage.
- Automatic policy inference from production data.
- Automatic proof that a generated code change is business-correct.

These can come later. The MVP should first prove the behavior change: the agent stops, asks, and
uses explicit domain context before editing.

## Acceptance Criteria

- The plugin manifest validates.
- The skill clearly defines onboarding, pre-change, review, and context-update modes.
- A user can initialize `.domain-guardian` in another project.
- A user can run a question-based bootstrap flow.
- A user can check whether context is still too sparse.
- A user can generate a Domain Impact Brief from existing context.
- A user can generate a pre-change task context packet that selects relevant business flows and code paths.
- A user can fail low-confidence domain-sensitive work in strict mode before editing.
- A user can analyze a diff for domain risk and missing required brief topics.
- A user can run an A/B pilot rubric to measure whether Domain Guardian improved AI output quality.
- A user can install Claude Code commands into another project and run the same pre-change/review workflow outside Codex.
- The README explains installation, quick start, commands, and intended usage in English.
- Local tests cover the key scripts.

## Current Product Readiness

Status: pilot-ready MVP.

Domain Guardian is now strong enough to test on one real project where business rules are concrete
and a reviewer can score AI output. It should be positioned as a pre-change context and review
workflow, not as an automatic policy enforcement system.

The strongest current signal is that it can make the agent inspect the correct business flow before
editing. The weakest current signal is that matching is still rule/index based, so a sparse or stale
knowledge base will produce either low-confidence stops or missed medium-risk changes.

The most important context-quality risk is stale cross-file structure: if `index.md` points to a
code path that `code-map.md` does not explain, the agent may select the right business flow but still
receive a weak implementation map. `scripts/check_context.py` now checks this coverage explicitly.

## Next Validation Step

Run a real A/B pilot on 3-10 domain-sensitive tasks:

1. Start with `scripts/pilot_eval.py low-cost-init --mode plan-only` or `--mode review-only`.
2. If low-cost results are promising, ask an AI agent to solve each task without Domain Guardian.
3. Ask it to solve the same task after running `scripts/prepare_change.py --strict`.
4. Have a human reviewer score both outputs with `scripts/pilot_eval.py`.
5. Treat the result as useful only if guarded runs improve invariant preservation and context usage
   without adding excessive clarification friction.
