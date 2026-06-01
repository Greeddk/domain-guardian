# User Flows

## Critical Flows

- Flow: paid appointment booking.
  - Actor: patient.
  - Owner: billing lead.
  - Entry point: patient selects appointment and starts checkout.
  - Successful path: hold slot, create or reuse payment intent, settle payment, mark appointment paid, send confirmation.
  - Failure path: release expired hold, keep failed payment event, let patient retry without duplicate charge.
  - Business outcome: clinic gets a reliable paid booking.
  - Code paths: `app/appointments/hold.ts`, `app/payments/create-intent.ts`, `app/payments/webhook.ts`.
  - Tests: `booking/paid-booking.test.ts`.
  - Source: 2026-05 billing policy review.
- Flow: cancellation request for settled appointment.
  - Actor: patient.
  - Owner: operations lead.
  - Entry point: patient portal cancellation button.
  - Successful path: create cancellation request, notify clinic staff, keep appointment state auditable.
  - Failure path: if appointment is already completed, show support contact path.
  - Business outcome: protects clinic refund policy while giving patient a clear path.
  - Code paths: `app/appointments/cancel.ts`, `app/notifications/staff.ts`.
  - Tests: `appointments/cancel-paid.test.ts`.
  - Source: 2026-05 operations policy review.

## Money Flows

- Flow: checkout payment.
  - Trigger: patient confirms booking.
  - Amount or pricing rule: clinic-defined appointment price plus allowed fees.
  - Required validation: one active payment intent per appointment.
  - External systems: Stripe.
  - Reversal or retry behavior: retry reuses existing payment intent when possible.

## Trust And Safety Flows

- Flow: staff refund override.
  - Risk: unauthorized refund or erased audit trail.
  - Guardrails: staff role, reason code, audit event, payment provider refund id.
  - Escalation: billing lead reviews disputed refunds.
  - Audit trail: append-only appointment audit event.

## Notification Flows

- Notification: paid booking confirmation.
  - Trigger: payment settlement webhook.
  - Recipient: patient and clinic staff.
  - Timing: send after payment state is confirmed.
  - Suppression rules: do not send duplicate confirmation for replayed webhook.
  - Required copy or compliance notes: include clinic cancellation policy.
