# 05 · CI/CD

Designed now so the repo structure supports it; wired up in
[Phase 7](./phases/phase-7-cicd.md).

> **As-built note:** the first production deploy used `firebase deploy --only
> apphosting` (local source) rather than a GitHub connection — see
> [ADR 0013](../adr/0013-local-source-app-hosting.md). `deploy.yml` below can either
> keep deploying App Hosting the same way from CI, or trigger an automatic rollout if
> a GitHub connection is added later; both are valid, the connection is optional.

---

## Workflows

> **As built (Phase 7):** two thin orchestrators — `pr.yml` and `deploy.yml` — call reusable
> workflows that each do one job: `_schemas`, `_backend`, `_frontend`, `_terraform-plan`,
> `_terraform-apply`, `_firebase-deploy` (shared by the preview, the prod deploy and its
> rollback). The PR checks stay jobs of the one `pr.yml` run rather than separate workflows: a
> required check in a path-filtered workflow never reports on PRs outside its paths and blocks
> them forever, whereas path-skipped jobs inside one run count as passed and a `checks` job
> rolls them up into the one required status check.

| `pr.yml` job / workflow | Trigger | Does |
|---|---|---|
| `schemas` | PR touching `architecture/` or generated code | Validate schemas, validate examples, run `make gen`, **fail on any diff** |
| `frontend` | PR touching `frontend/` | `tsc --noEmit`, eslint, vitest, `next build` |
| `backend` | PR touching `backend/` | ruff, `mypy --strict`, import-linter, pytest against the Firestore emulator |
| `infra-plan` | PR touching `infra/terraform/` | `terraform fmt -check`, `validate`, `plan` for prod and staging → PR comments |
| `checks` | every PR | The single required status check |
| `preview` | PR changing anything deployable | Deploy rules, all functions and App Hosting to the **staging project** ([ADR 0018](../adr/0018-staging-project-for-pr-previews.md)); smoke test; Lighthouse; comment the staging URL |
| `deploy.yml` | push to `main` | Rules → functions → App Hosting → smoke test (rollback on failure) → `terraform apply` behind approval when infra changed ([ADR 0019](../adr/0019-ci-identities-gated-by-github-environment.md)) |
| `backup-verify.yml` | nightly cron | Confirm the Firestore export actually landed — *not built yet* |

---

## The drift check is the important one

The `schemas` job is what makes the schema-first approach real rather than aspirational:

```yaml
- run: make gen
- run: git diff --exit-code || (
    echo "::error::Generated code is out of date. Run 'make gen' and commit."; exit 1)
```

Without this, someone edits a Pydantic model by hand one afternoon, and the schemas silently stop
being the source of truth. With it, that's a red build.

---

## Auth: Workload Identity Federation

No service-account JSON key in GitHub secrets. GitHub Actions exchanges its OIDC token for a
short-lived GCP token, scoped to this repository:

```yaml
permissions:
  contents: read
  id-token: write

- uses: google-github-actions/auth@v2
  with:
    workload_identity_provider: ${{ vars.WIF_PROVIDER }}
    service_account: ${{ vars.DEPLOY_SA }}
```

A leaked long-lived key is valid until someone notices. A leaked OIDC token expires in minutes and
only works from this repo. The WIF pool and its bindings are Terraform-managed
([04 · Infrastructure](./04-infrastructure.md)).

---

## Path filters

The four independent roots exist partly for this — a copy tweak in `frontend/` must not rebuild the
Python functions:

```yaml
on:
  pull_request:
    paths: ['frontend/**', 'architecture/**', '.github/workflows/ci-frontend.yml']
```

`architecture/**` appears in both frontend and backend filters on purpose: a schema change affects
generated code on both sides, so both suites must run.

### Deploying only what changed

Each subdomain is its own function ([ADR 0017](../adr/0017-bounded-context-domains.md)), so the
deploy can be narrowed to the subdomains a PR actually touched:

```bash
firebase deploy --only functions:api_content_projects,functions:api_media_library
```

A change under `src/<domain>/<sub>/` deploys every function that subdomain lists in its domain's
`FUNCTIONS` table (`src/<domain>/main.py`) — its `api_<domain>_<sub>` plus any trigger or scheduled
job it owns. A change under `kernel/`, `shared/`, the root `main.py` or the dependency files
touches everything, so it deploys everything. Derive the mapping from the `FUNCTIONS` tables
rather than hard-coding it in the workflow, or the two drift.

Worth doing, but not first: `preview.yml` and `deploy.yml` start by deploying all functions,
and narrow once the pipeline is proven.

---

## CI reuses the Makefile

Workflows call `make lint`, `make test`, `make build` — the same targets you run locally. When CI
fails, you reproduce it with one command, and "works on my machine" has one less cause.

---

## Branch protection on `main`

- No direct pushes; PRs only
- Required checks: `schemas`, `ci-frontend`, `ci-backend`, `infra-plan`
- Linear history (squash merge)
- Conversation resolution required

Solo-project caveat: this is deliberately mild friction. It's what stops a 2am "quick fix" pushed
straight to prod, which is exactly when that happens.

---

## Environments & approvals

`deploy.yml` runs in a GitHub **environment** called `production` with:

- A required reviewer (you) on the `terraform apply` step — so infra changes are never silent
- Secrets scoped to that environment only

Function and frontend deploys don't need approval. Infra does, because that's where the
expensive mistakes live.

---

## Quality gates

| Gate | Threshold |
|---|---|
| Lighthouse Performance | ≥ 95 |
| Lighthouse Accessibility | 100 |
| Lighthouse SEO | 100 |
| LCP | < 2.0s |
| CLS | < 0.05 |
| INP | < 200ms |
| Backend coverage | ≥ 80% on services + repositories |
| `mypy --strict` | zero errors |

The Lighthouse budget fails the build, not just warns. A performance budget that only warns is a
performance budget that gets ignored.

---

**Next:** [06 · Content Checklist](./06-content-checklist.md)
