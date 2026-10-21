---
paths:
  - ".github/**"
---

# CI/CD rules

Decisions: `.docs/decisions/ci-cd.md`; the flow end to end: `.docs/CODE_FLOW.md` (CI/CD);
operations: `.docs/RUNBOOK.md` (CI/CD and staging). ADR 0018, 0019.

## Shape

- **Two thin workflows** — `pr.yml` (checks → staging preview → PR comment) and `deploy.yml`
  (push to `main` → prod deploy → rollback on failure → Terraform). Steps live in **composite
  actions** under `.github/actions/<name>/action.yml`. No `_`-prefixed reusable workflows, no
  monolith.
- **No scripts.** Shell in a step is a few lines of glue. If an action exists for the job (PR
  comments: `marocchino/sticky-pull-request-comment`; change detection: `dorny/paths-filter`),
  use it.
- **Config from its source**: project IDs from `.firebaserc` aliases, frontend env from
  `frontend/apphosting*.yaml` (read with `yq`), URLs/identities from GitHub environment variables.
  Never hard-code a project ID, bucket, domain or URL in a workflow.

## Path filters

- `pr.yml` and `deploy.yml` define the **same deploy targets** (`rules`, `api`, `apphosting`)
  — change both together. `api` deploys first (`cloud-run-deploy`), then `firebase-deploy`.
- A `.github/**` change runs everything (the `ci` anchor). Markdown never runs anything
  (`'!**/*.md'` with `predicate-quantifier: some-with-excludes`). A docs-only PR runs only
  `changes` + `checks`.
- `checks` is the single required status check; it passes when every job succeeded or was
  skipped. Never make an individual job required.

## Versions and auth

- **Pin every action and tool to a version looked up live** (`gh api repos/<o>/<r>/releases`,
  npm). Floating major tags (`@v4`) are fine for actions; `firebase-tools` is pinned exactly.
- **Keyless auth only** (`google-github-actions/auth` + WIF). Identities are bound to GitHub
  environments: `staging`, `staging-infra`, `production`, `production-infra` (approval).
  A job that deploys must declare its `environment`, or GCP refuses the token.

## Before pushing a workflow change

- `actionlint` (`UV_SYSTEM_CERTS=1 uvx --from actionlint-py actionlint <files>` in PowerShell
  after refreshing PATH).
- Think through: PR from a fork (no OIDC → never reaches staging), docs-only PR, `.github`-only PR,
  first push to a branch (`github.event.before` all zeros), manual `workflow_dispatch`.
- Then watch the run to green.
