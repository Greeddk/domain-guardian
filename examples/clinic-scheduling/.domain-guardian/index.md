# Domain Context Index

Use this file first. It points an agent to the smallest relevant context before reading the full
clinic scheduling knowledge base.

## Index Entries

- Area: paid appointment cancellation
  - Keywords: cancel, cancellation, paid, settled, appointment, refund, patient, staff override
  - Read: `domain-rules.md`, `user-flows.md`, `operational-context.md`, `code-map.md`
  - Code: `app/appointments/cancel.ts`, `app/payments/webhook.ts`, `app/notifications/staff.ts`
  - Owners: operations lead, billing lead
  - Risk: patient self-service cancellation can bypass refund policy and audit requirements.
  - Required brief topics: settlement state, cancellation request state, staff review, audit event, refund side effect.
- Area: payment intent and webhook idempotency
  - Keywords: payment, intent, webhook, stripe, retry, duplicate, idempotent, confirmation
  - Read: `domain-rules.md`, `user-flows.md`, `operational-context.md`, `code-map.md`
  - Code: `app/payments/create-intent.ts`, `app/payments/webhook.ts`, `app/payments/refund.ts`
  - Owners: billing lead
  - Risk: duplicate payment intents or replayed webhooks can double charge patients or send duplicate confirmations.
  - Required brief topics: payment intent reuse, provider event id, webhook replay, retry behavior.
- Area: appointment lifecycle transitions
  - Keywords: appointment, state, transition, booked, paid, settled, cancelled, completed, hold
  - Read: `domain-rules.md`, `user-flows.md`, `code-map.md`
  - Code: `app/appointments/state.ts`, `app/appointments/hold.ts`, `app/appointments/cancel.ts`
  - Owners: operations lead
  - Risk: invalid transitions can erase operational state or break support workflows.
  - Required brief topics: allowed transition, forbidden transition, actor, side effects.

## Default Escalation Rules

- If a task changes cancellation, refunds, payment, appointment lifecycle, audit events, or staff permissions, create a Domain Impact Brief.
- If the task touches Stripe webhook handling, read the payment idempotency entry even if the user request sounds like an appointment change.
- If no entry matches, read `domain-rules.md`, `user-flows.md`, and `code-map.md` before editing.
