# Operational Context

## Operating Model

- Teams involved: product, billing, clinic support, and operations.
- Manual review steps: staff reviews settled appointment cancellation requests.
- Support responsibilities: support handles payment disputes and failed webhook reconciliation.
- Escalation owners: billing lead for money movement, operations lead for cancellation policy.

## External Dependencies

- System: Stripe.
  - Purpose: payment intent, settlement, refund, and webhook events.
  - Failure behavior: webhook may be delayed, duplicated, or delivered out of order.
  - Retry policy: webhook handlers must be idempotent.
  - Data contract: provider event id and payment intent id are stored on audit events.

## Incident History

- Incident: duplicate refund support tickets.
  - Date: 2026-05-12.
  - What happened: cancellation and settlement webhook order caused unclear appointment state.
  - Root cause: cancellation flow assumed payment state was final.
  - Preventive rule: settled or settling payments move to cancellation request, not direct cancellation.
  - Code paths: `app/appointments/cancel.ts`, `app/payments/webhook.ts`.

## Manual Overrides

- Override: staff refund after settlement.
  - Who can use it: clinic staff with billing permission.
  - When allowed: patient request, clinic policy exception, or support dispute resolution.
  - Required audit trail: actor id, reason code, payment provider refund id, timestamp.
  - Cleanup needed: notify patient and reconcile payment state.

## Compliance Or Legal Constraints

- Constraint: audit history retention.
  - Applies to: appointments, payments, refunds, and cancellation requests.
  - Required behavior: do not hard-delete business events.
  - Source: operations policy.
