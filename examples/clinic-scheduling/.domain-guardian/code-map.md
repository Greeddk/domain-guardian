# Code Map

## Domain Concepts To Code

- Concept: appointment lifecycle.
  - Files: `app/appointments/hold.ts`, `app/appointments/cancel.ts`, `app/appointments/state.ts`.
  - Primary functions/classes: `holdAppointment`, `cancelAppointment`, `transitionAppointment`.
  - Database tables or collections: `appointments`, `appointment_audit_events`.
  - API routes: `POST /appointments/:id/cancel`.
  - Events/jobs: `appointment.hold_expired`, `appointment.cancel_requested`.
  - Tests: `appointments/cancel-paid.test.ts`.
- Concept: payment intent lifecycle.
  - Files: `app/payments/create-intent.ts`, `app/payments/webhook.ts`, `app/payments/refund.ts`.
  - Primary functions/classes: `createPaymentIntent`, `handlePaymentWebhook`, `refundPayment`.
  - Database tables or collections: `payments`, `payment_events`.
  - API routes: `POST /payments/intent`, `POST /payments/webhook`.
  - Events/jobs: `payment.settled`, `payment.refunded`.
  - Tests: `payments/create-intent.test.ts`, `payments/webhook-idempotency.test.ts`.

## Ownership Boundaries

- Area: cancellation policy.
  - Owner: operations lead.
  - Safe to change: UI text and staff notification copy.
  - Requires review: state transitions, refund policy, patient self-service behavior.
  - Related knowledge rules: settled paid appointment cannot be patient-cancelled directly.
- Area: payment retry and webhook handling.
  - Owner: billing lead.
  - Safe to change: logging and observability.
  - Requires review: payment intent creation, idempotency keys, webhook state transitions.
  - Related knowledge rules: one appointment can have at most one active payment intent.

## High-Risk Code Paths

- Path: `app/appointments/cancel.ts`.
  - Why high risk: changing it can bypass clinic refund policy.
  - Protected rule: settled paid appointment moves to cancellation request.
  - Common mistake: treating all paid appointments as cancellable.
  - Required tests: patient cancellation, staff override, settlement webhook race.
- Path: `app/payments/webhook.ts`.
  - Why high risk: external events can be duplicated or out of order.
  - Protected rule: webhook handling must be idempotent.
  - Common mistake: sending duplicate confirmations or creating duplicate payment events.
  - Required tests: replayed webhook and cancellation race.

## Glossary

- Term: settled payment.
  - Meaning: payment provider confirms funds are captured and final enough for clinic policy.
  - Avoid confusing with: payment intent created or payment authorized.
- Term: cancellation request.
  - Meaning: patient request that staff must review before refund or credit.
  - Avoid confusing with: final cancelled appointment state.
