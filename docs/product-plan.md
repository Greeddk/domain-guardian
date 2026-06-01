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
- A project-local knowledge base template.
- Interactive onboarding that asks focused questions and appends answers to the right context files.
- A context completeness checker.
- A Domain Impact Brief generator.
- English README and development checks.

## Out Of Scope For MVP

- Automatic semantic indexing of the full codebase.
- CI integration that blocks PRs.
- Vector search, embeddings, or remote storage.
- Automatic policy inference from production data.

These can come later. The MVP should first prove the behavior change: the agent stops, asks, and
uses explicit domain context before editing.

## Acceptance Criteria

- The plugin manifest validates.
- The skill clearly defines onboarding, pre-change, review, and context-update modes.
- A user can initialize `.domain-guardian` in another project.
- A user can run a question-based bootstrap flow.
- A user can check whether context is still too sparse.
- A user can generate a Domain Impact Brief from existing context.
- The README explains installation, quick start, commands, and intended usage in English.
- Local tests cover the key scripts.
