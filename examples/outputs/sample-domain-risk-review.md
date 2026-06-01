# Sample Domain Risk Review

## Finding: Settled Paid Appointments Can Be Directly Cancelled

- Severity: High
- Changed code: `app/appointments/cancel.ts`
- Domain rule at risk: a settled paid appointment cannot be patient-cancelled directly.
- Why it matters: direct cancellation bypasses staff refund policy and can create payment disputes.
- User or business consequence: clinics may lose control over late cancellation and refund handling.
- Recommended fix: when actor is `patient` and payment state is `settled` or `settlement_pending`, create a `cancellation_requested` state instead of `cancelled`.
- Required test: patient cancellation of a settled paid appointment should notify staff and preserve audit history.

## Finding: Missing Idempotency Guard On Payment Webhook

- Severity: Medium
- Changed code: `app/payments/webhook.ts`
- Domain rule at risk: one appointment can have at most one active payment intent and duplicate provider events must not duplicate business side effects.
- Why it matters: replayed payment events can send duplicate confirmations or append conflicting audit events.
- User or business consequence: patients and staff lose trust in payment state.
- Recommended fix: store and check provider event id before applying side effects.
- Required test: replaying the same settlement webhook does not send a second confirmation.
