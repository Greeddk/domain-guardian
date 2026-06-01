# Publishing Domain Guardian

This repository is prepared for a public GitHub release on:

```text
public/domain-guardian-v0.2
```

## Release Preconditions

- The repository owner has approved public publication of this directory.
- GitHub CLI is authenticated with an account that can create or push to `GreedDK/domain-guardian`.
- The local branch is clean.

Check authentication:

```bash
gh auth status
```

If authentication is expired:

```bash
gh auth login -h github.com
```

## Create The Public Repository

From the repository root:

```bash
gh repo create Greeddk/domain-guardian \
  --public \
  --source=. \
  --remote=origin \
  --push \
  --description "Codex plugin that keeps AI coding agents grounded in business rules and domain context."
```

If the repository already exists:

```bash
git push -u origin public/domain-guardian-v0.2
```

## Verify Publication

```bash
curl -I https://github.com/Greeddk/domain-guardian
gh run list --repo Greeddk/domain-guardian --limit 5
```

The public README should explain:

- the problem Domain Guardian solves,
- how to install it as a Codex plugin,
- how to initialize project context,
- how to run onboarding and readiness checks,
- how to generate a Domain Impact Brief.
