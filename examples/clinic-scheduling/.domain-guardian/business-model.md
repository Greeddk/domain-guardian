# Business Model

## Product Summary

- Product: appointment scheduling and payment workflow for small outpatient clinics.
- Primary users: clinic staff, clinicians, and patients booking appointments.
- Paying customers: clinics pay a monthly SaaS fee and a usage fee for online payments.
- Buyer vs user differences: clinic administrators buy the product; reception staff and patients use it daily.

## Revenue Model

- Pricing model: monthly clinic subscription plus payment processing usage.
- Billing trigger: subscription renews monthly; payment usage is billed when patient payment settles.
- Upgrade/downgrade rules: downgrades apply at the next billing cycle and must not remove audit history.
- Refund, cancellation, or dispute rules: patient refunds are allowed before settlement or through a staff override after settlement.

## Value-Critical Outcomes

- Outcome: patients can book and pay for valid appointments without double charging.
  - Why it matters: payment trust is the main adoption driver for clinics.
  - What must not break: a patient must never be charged twice for the same appointment.
  - Owner: product and billing lead.
- Outcome: clinics keep an auditable appointment and payment history.
  - Why it matters: clinics need reliable records for support, disputes, and compliance.
  - What must not break: cancellation and refund actions must preserve audit records.
  - Owner: operations lead.

## Business Metrics

- Activation: clinic completes first paid booking.
- Retention: clinics keep online booking enabled for more than 90 days.
- Conversion: patient completes checkout after selecting an appointment.
- Revenue: subscription renewal and settled payment usage.
- Trust or safety: payment dispute rate and support tickets about booking state.
- Operational workload: staff manual refund and rescheduling requests.

## Known Tradeoffs

- Decision: settled paid appointments require staff-assisted cancellation.
  - Chosen behavior: patients can request cancellation, but staff must approve refund or credit.
  - Rejected alternative: instant self-service cancellation after settlement.
  - Reason: clinics need control over late cancellation policy and refund handling.
  - Source: 2026-05 billing policy review.
