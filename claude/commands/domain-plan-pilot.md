---
description: Start a low-cost Domain Guardian plan-only or review-only pilot.
---

# Domain Guardian Low-Cost Pilot

Mode or goal: `$ARGUMENTS`

Use this when full implementation A/B would cost too many tokens.

For plan-only:

```bash
python3 "{{DOMAIN_GUARDIAN_ROOT}}/scripts/pilot_eval.py" low-cost-init \
  --mode plan-only \
  --output docs/domain-guardian/plan-only-scores.json
```

For review-only:

```bash
python3 "{{DOMAIN_GUARDIAN_ROOT}}/scripts/pilot_eval.py" low-cost-init \
  --mode review-only \
  --output docs/domain-guardian/review-only-scores.json
```

Then run the same task twice:

- baseline: ask for a plan or review without Domain Guardian context,
- guarded: run `/domain-prepare <task>` first, then ask for the same plan or review.

Score both outputs with the generated JSON and render:

```bash
python3 "{{DOMAIN_GUARDIAN_ROOT}}/scripts/pilot_eval.py" report \
  --input docs/domain-guardian/plan-only-scores.json \
  --output docs/domain-guardian/plan-only-report.md
```
