---
description: Check whether Domain Guardian context is ready for business-sensitive edits.
---

# Domain Guardian Context Check

Run:

```bash
python3 "{{DOMAIN_GUARDIAN_ROOT}}/scripts/check_context.py" .domain-guardian
```

If `.domain-guardian` does not exist, retry with `docs/domain-guardian` or `knowledge`.

Report:

- which files are ready,
- which files need work,
- whether `index.md` code paths are covered by `code-map.md`,
- the next one or two onboarding questions needed to improve the context.
