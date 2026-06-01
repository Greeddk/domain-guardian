# Domain Diff Risk Report

- Context directory: `examples/clinic-scheduling/.domain-guardian`
- Risk level: HIGH
- Changed files: `app/appointments/cancel.ts`

## Matched Index Entries

- paid appointment cancellation
  - Read: `domain-rules.md`, `user-flows.md`, `operational-context.md`, `code-map.md`
  - Code: `app/appointments/cancel.ts`, `app/payments/webhook.ts`, `app/notifications/staff.ts`
  - Owners: operations lead, billing lead
  - Risk: patient self-service cancellation can bypass refund policy and audit requirements.
  - Required brief topics: settlement state, cancellation request state, staff review, audit event, refund side effect.
- appointment lifecycle transitions
  - Read: `domain-rules.md`, `user-flows.md`, `code-map.md`
  - Code: `app/appointments/state.ts`, `app/appointments/hold.ts`, `app/appointments/cancel.ts`
  - Owners: operations lead
  - Risk: invalid transitions can erase operational state or break support workflows.

## Relevant Rules

- Rule: a settled paid appointment cannot be patient-cancelled directly.
- Must always be true: patient cancellation creates a cancellation request when payment is settled.

## Recommended Gate

- Create or update a Domain Impact Brief before merging this change.
- Add tests for patient cancellation, staff override, audit history, and webhook race behavior.

## Brief Check

- OK: Domain Impact Brief
