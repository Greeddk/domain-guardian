# Domain Guardian Context Template

Copy the `knowledge/` directory into a project as `.domain-guardian/` or `docs/domain-guardian/`.

Minimum useful context:

```text
Business model:
- Who pays?
- What event creates value?
- What must never happen?

Domain rules:
- Which validations are business policy?
- Which lifecycle transitions are forbidden?
- Which exceptions exist?

User flows:
- What are the revenue, trust, and support-critical flows?
- What happens on failure or retry?

Operational context:
- Who manually reviews or overrides outcomes?
- Which external systems can fail?

Code map:
- Which files enforce each rule?
- Which tests prove the invariant?
```

Good rule format:

```text
Rule: A trial user can create at most one active workspace.
Applies to: Workspace creation and invite acceptance.
Exceptions: Internal QA accounts can bypass the limit.
Enforced in code: app/workspaces/create.ts, app/invites/accept.ts.
Tests: workspace-limit.test.ts.
Source: 2026-05 pricing policy decision.
```
