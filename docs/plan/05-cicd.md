# 05 · CI/CD

Designed now so the repo structure supports it; wired up in
[Phase 7](./phases/phase-7-cicd.md).

---

## Workflows

| Workflow | Trigger | Does |
|---|---|---|
| `schemas.yml` | PR touching `architecture/` | Validate schemas, validate examples, run `make gen`, **fail on any diff** |
| `ci-frontend.yml` | PR touching `frontend/` | `tsc --noEmit`, eslint, vitest, `next build`, Lighthouse CI budget |
| `ci-backend.yml` | PR touching `backend/` | ruff, `mypy --strict`, pytest against the Firebase emulator |
| `infra-plan.yml` | PR touching `infra/` | `terraform fmt -check`, `validate`, `plan` → posted as a PR comment |
| `preview.yml` | PR | App Hosting preview channel + a comment with the URL |
| `deploy.yml` | push to `main` | `terraform apply` → deploy rules → deploy **changed** function domains → App Hosting auto-builds |
| `backup-verify.yml` | nightly cron | Confirm the Firestore export actually landed |

---

## The drift check is the important one

`schemas.yml` is what makes the schema-first approach real rather than aspirational:

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

Functions are split by domain ([ADR 0011](../adr/0011-domain-wise-separate-functions.md)), so the
deploy can be narrowed to the domains a PR actually touched:

```bash
firebase deploy --only functions:api_projects,functions:api_media
```

A change under `backend/functions/shared/` touches everything, so it deploys everything. A change
under `backend/functions/src/projects/` deploys one function. Worth doing — it turns a multi-minute
deploy into a seconds-long one for the common case.

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
