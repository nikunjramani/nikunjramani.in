# 0019 · CI identities are gated by GitHub environment, and CI applies Terraform

**Status:** ✅ Accepted · **Date:** 2026-10-15
**Deciders:** Owner

---

## Context

Phase 7 automates deploys ([phase-7-cicd.md](../plan/phases/phase-7-cicd.md)). Until now one
service account, `github-deploy`, existed per project, and Workload Identity Federation let **any
workflow in this repository** impersonate it — on any branch, including a PR branch. With a
staging project for previews ([ADR 0018](./0018-staging-project-for-pr-previews.md)), that would
have let a PR's workflow deploy to production just by naming the prod identity.

Separately, the owner chose to have CI run `terraform apply` rather than keeping it manual. This
Terraform manages project IAM, service accounts, Workload Identity Federation, Secret Manager,
Firestore and the billing budget, so whatever applies it is effectively a project owner.

GitHub puts an `environment` claim in a job's OIDC token, and mints the token only after that
environment's protection rules — allowed branches, required reviewers — have passed.

## Decision

Each project has three CI identities, each bound to exactly one thing:

| Identity | Can | Bound to |
|---|---|---|
| `github-deploy` | `firebase deploy` (rules, functions, App Hosting) | environment `production` / `staging` |
| `github-terraform` | `terraform apply` | environment `production-infra` / `staging-infra` |
| `github-plan` | `terraform plan` (read-only) | the repository |

The WIF provider maps `attribute.environment` from the token, and each binding is a
`principalSet://…/attribute.environment/<name>`. On GitHub: `production`, `production-infra`
and `staging-infra` accept only `main`; `production-infra` also requires the owner's approval.
`staging` accepts any branch, because PR previews deploy there.

So approval gates the **credential**, not just a job: no workflow can obtain `github-terraform`
for prod without the owner approving that run on `main`.

## Consequences

### What this makes easier

- A PR can only ever reach staging. Production deploys and every `terraform apply` happen from
  `main`, after merge.
- Infra changes deploy without anyone's laptop: merge, approve, applied.
- The read-only plan identity can post a plan on every PR without being able to change anything.

### What this makes harder — the cost we're accepting

- **A GitHub identity holds owner-equivalent rights** on each project, once approved. The
  approval on `production-infra` is now load-bearing: approve only runs you expect.
- **Billing-budget rights can't be granted by this Terraform**, because they live on the billing
  account, not the project. They're granted by hand once (.docs/RUNBOOK.md); forgetting it makes
  the CI apply fail on the budget resource.
- **Six service accounts and four GitHub environments** to keep aligned. The names are in
  Terraform (`deploy_environment`, `infra_environment`) and the workflows; they must match.
- The `production` environment must stay main-only. Opening it to other branches silently
  re-opens prod deploys to PR branches.

## Alternatives considered

### Keep `terraform apply` manual; CI only plans
The safest option — no GitHub identity ever holds owner rights. Rejected by the owner for
convenience: infra changes would need a laptop with the right credentials. Remains the fallback
if the approval step ever feels like a rubber stamp.

### Bind identities to the repository and rely on workflow `if:` conditions
That is what existed. A condition in a workflow file doesn't restrict the credential — any
workflow, including one added in a PR, can request the same token.

### Bind to branch (`assertion.ref == 'refs/heads/main'`) instead of environment
Restricts to `main`, but has no notion of approval, and PR previews would need a different
mechanism. Environments give branch policy and approval in one place.

## Revisit if

- Someone other than the owner gets write access to the repository — environment approval and
  branch policies then need review of who can change them.
- GitHub or Google changes how the `environment` claim is minted.
