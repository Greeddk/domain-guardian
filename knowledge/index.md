# Domain Context Index

Use this file as the first stop before reading the full knowledge base. It maps task keywords,
business concepts, and code paths to the smallest useful context files.

## How To Use

- Start here for every domain-sensitive task.
- Match the user's task, changed files, and diff keywords against the entries below.
- Read only the linked context files first.
- Escalate to the full knowledge base when the index match is weak, the task changes policy, or a protected invariant is unclear.

## Index Entries

- Area:
  - Keywords:
  - Read:
  - Code:
  - Owners:
  - Risk:
  - Required brief topics:

## Default Escalation Rules

- If a task changes pricing, billing, refunds, eligibility, permissions, lifecycle states, audit trails, notifications, retries, or external integrations, create a Domain Impact Brief.
- If no index entry matches but the diff touches business logic, read `domain-rules.md`, `user-flows.md`, and `code-map.md`.
- If the code and context disagree, treat it as a product question.
