# Domain Impact Brief

- Date: 2026-06-01
- Task: Allow patients to cancel paid appointments
- Context directory: `examples/clinic-scheduling/.domain-guardian`

## Relevant Business Context

- Clinics pay for reliable booking and payment workflows.
- Payment trust is a value-critical outcome.
- Settled paid appointments require staff-assisted cancellation.

## Selected Context From Index

- Area: paid appointment cancellation.
- Keywords: cancel, cancellation, paid, settled, appointment, refund, patient, staff override.
- Read: `domain-rules.md`, `user-flows.md`, `operational-context.md`, `code-map.md`.
- Code: `app/appointments/cancel.ts`, `app/payments/webhook.ts`, `app/notifications/staff.ts`.
- Risk: patient self-service cancellation can bypass refund policy and audit requirements.
- Required brief topics: settlement state, cancellation request state, staff review, audit event, refund side effect.

## Relevant Business Rules

- One appointment can have at most one active payment intent.
- A settled paid appointment cannot be patient-cancelled directly.
- Patient cancellation creates a cancellation request when payment is settled.

## Relevant User Or Operations Flows

- Paid appointment booking must avoid duplicate charges.
- Cancellation request for settled appointment notifies clinic staff.
- Stripe webhooks can be delayed, duplicated, or delivered out of order.

## Code Areas Likely Involved

- `app/appointments/cancel.ts`
- `app/payments/webhook.ts`
- `app/notifications/staff.ts`
- `appointments/cancel-paid.test.ts`

## Protected Invariants

- Do not allow direct patient cancellation of settled paid appointments.
- Preserve appointment and payment audit history.
- Keep payment webhook handling idempotent.

## Ambiguities Or Questions

- Should the new behavior apply to `paid`, `settlement_pending`, and `settled`, or only `settled`?
- Which staff role should approve refunds after settlement?
- Should patients see cancellation request status in the portal?

## Test Or Review Guardrails

- Add tests for patient cancellation before and after settlement.
- Add a webhook race test where settlement arrives after cancellation request.
- Review notifications to avoid duplicate patient confirmation or staff alerts.
