# Domain Rules

## Protected Invariants

- Rule: one appointment can have at most one active payment intent.
  - Applies to: checkout, retry, webhook, and staff payment collection flows.
  - Must always be true: retries reuse or cancel the previous payment intent before creating a new one.
  - Exceptions: none.
  - Enforced in code: `app/payments/create-intent.ts`, `app/payments/webhook.ts`.
  - Test coverage: `payments/create-intent.test.ts`.
  - Source or owner: billing lead.
- Rule: a settled paid appointment cannot be patient-cancelled directly.
  - Applies to: patient portal cancellation and appointment state transitions.
  - Must always be true: patient cancellation creates a cancellation request when payment is settled.
  - Exceptions: staff override may cancel and issue refund or clinic credit.
  - Enforced in code: `app/appointments/cancel.ts`.
  - Test coverage: `appointments/cancel-paid.test.ts`.
  - Source or owner: operations lead.

## Permissions And Access

- Actor: patient.
  - Can: book, pay, reschedule before clinic cutoff, request cancellation.
  - Cannot: directly refund a settled payment or delete appointment history.
  - Conditional rules: can self-cancel unpaid appointments before the clinic cutoff.
- Actor: clinic staff.
  - Can: cancel, refund, credit, reschedule, and override cutoff policy.
  - Cannot: erase audit events.
  - Conditional rules: refund after settlement requires reason code.

## Lifecycle States

- Entity: appointment.
  - States: draft, held, booked, paid, settlement_pending, settled, cancellation_requested, cancelled, completed.
  - Allowed transitions: booked to paid, paid to settlement_pending, settlement_pending to settled, settled to cancellation_requested.
  - Forbidden transitions: settled to cancelled by patient action.
  - Side effects: payment webhooks update payment state and append audit events.

## Eligibility And Policy

- Policy: late cancellation.
  - Eligible when: clinic cutoff has not passed or staff override is present.
  - Ineligible when: cutoff passed and actor is patient.
  - Manual override: clinic staff can override with reason code.
  - Audit requirement: actor, reason, previous state, next state, and payment action.

## Edge Cases

- Case: payment webhook arrives after patient requests cancellation.
  - Expected behavior: webhook updates payment state, cancellation remains a staff-reviewed request.
  - Why: payment provider ordering is not guaranteed.
  - Related incident or support issue: duplicate refund support tickets in May 2026.
