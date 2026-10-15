# Phase 7 · CI/CD Hardening

**~5 hours** · Status: 🟡 Built on branch `phase-7-cicd`; awaiting the first applies and runs

> **Goal:** Push to `main` deploys safely; every PR is checked automatically; no
> long-lived credentials anywhere.

Done **after** launch on purpose — the deploy path is proven manually first, so when you
automate it you're encoding something known to work.

Design: [ADR 0018](../../adr/0018-staging-project-for-pr-previews.md) (separate staging
project) · [ADR 0019](../../adr/0019-ci-identities-gated-by-github-environment.md) (identities
gated by GitHub environment; CI applies Terraform) · operating it:
[RUNBOOK · CI/CD and staging](../../RUNBOOK.md#cicd-and-staging).

---

## Prerequisites

- [x] [Phase 6](./phase-6-deploy.md) done — deployed manually at least once
- [x] [05 · CI/CD](../05-cicd.md) read
- [ ] **Prod caught up with `main`, by hand, before `PROD_DEPLOY_ENABLED` is set.** As of
      2026-10-15 prod still runs the 12 pre-[ADR 0017](../../adr/0017-bounded-context-domains.md)
      functions (`api_contact`, `api_projects`, …); `main` has the 15 `api_<domain>_<sub>` ones,
      plus the unapplied [ADR 0015](../../adr/0015-remove-revalidation-webhook.md) secret cleanup.
      `terraform plan` on prod: 17 add / 2 change / 18 destroy — it drops public invoke on the 12
      live functions and binds 15 that don't exist yet. Left to the first automated deploy,
      that's an outage. Do it supervised: deploy the new functions → deploy App Hosting (frontend
      switches names) → `terraform apply` → confirm, then delete the old 12. The first staging
      preview deploy rehearses the same functions + App Hosting sequence

---

## Tasks

### 7.1 · Identities — Workload Identity Federation ([ADR 0019](../../adr/0019-ci-identities-gated-by-github-environment.md))

- [x] One pool + provider **per project**, from the same `iam` module — prod's existed since
      Phase 6 (verified 2026-10-15, no user-managed SA keys anywhere); staging's comes from
      `envs/staging`
- [x] Provider maps `attribute.environment` from the GitHub token
- [x] `github-deploy` bound to environment `production` / `staging` (was: the whole repository,
      so any branch could deploy prod); `deploy_roles` widened to what `firebase deploy` needs —
      secret, Cloud Build, Artifact Registry, Scheduler, Eventarc, App Hosting
- [x] `github-terraform` (apply) bound to `production-infra` / `staging-infra`
- [x] `github-plan` (read-only, plus state-lock write) bound to the repository
- [ ] Applied: `envs/staging` in full; `envs/prod` with `-target=module.iam` only (RUNBOOK)
- [ ] Billing-account roles granted (RUNBOOK · First-time setup)
- [ ] GitHub environments + variables (RUNBOOK · First-time setup)
- [ ] Verified: a workflow authenticates with **no** JSON key, in every environment
- [ ] Trim any role the first real runs prove unnecessary

### 7.2 · PR checks — `.github/workflows/pr.yml`

One workflow, not one per area: a required check that lives in a path-filtered workflow never
reports on PRs outside its paths, and blocks them forever. Path-skipped jobs inside one workflow
count as passed.

- [x] `schemas` — validate, `make gen`, fail on diff (moved from `schemas.yml`, now deleted)
- [x] `backend` — ruff, ruff format, mypy strict, import-linter, pytest on the Firestore
      emulator. `REQUIRE_FIRESTORE_EMULATOR` turns the conftest's skip into a failure, so a broken
      emulator start can't pass as 61 skipped tests
- [x] `frontend` — tsc, eslint, vitest, `next build`
- [x] `infra-plan` — fmt, validate, plan for prod and staging, each posted as its own PR comment
- [x] `checks` — rolls the above up into the single required status check
- [x] Path filters (`dorny/paths-filter`); npm, uv and emulator caching
- [ ] First green run on a real PR

### 7.3 · Staging project & preview deploys ([ADR 0018](../../adr/0018-staging-project-for-pr-previews.md))

**Project-aware config:**

- [x] `kernel/config.py` reads the project from `GCLOUD_PROJECT` (Firebase reserves the
      `FIREBASE_` dotenv prefix) — staging functions run as staging's own runtime SA. Tested
- [x] `backend/functions/.env.nikunjramani-in-staging` (and its `.gitignore` exception)
- [x] `frontend/apphosting.staging.yaml` — staging Firebase config, functions URL, Turnstile
      **test** site key, `SITE_INDEXABLE=false`
- [ ] Fill its `NEXT_PUBLIC_FIREBASE_API_KEY` / `APP_ID` from the staging web app after apply
- [x] `SITE_INDEXABLE=false` → `robots.txt` disallows everything and every response carries
      `X-Robots-Tag: noindex`
- [x] `.firebaserc` `staging` alias; CI always passes `--project`
- [x] `modules/app-hosting` takes `custom_domain` and `environment`; prod's two domains carry
      `moved` blocks (planned: moves only, nothing destroyed)
- [x] No `monitoring` module in staging

**Bootstrap:**

- [x] `nikunjramani-in-staging` created, same billing account, Firebase added (2026-10-15)
- [x] OAuth consent + Google sign-in provider enabled
- [x] State bucket `nikunjramani-in-staging-tfstate`, in the staging project — a **separate
      bucket**, not a prefix in prod's: staging identities then never need anything in prod
- [ ] Staging App Hosting hostname added to Auth's authorized domains

**Terraform:**

- [x] `infra/terraform/envs/staging/` — same modules, staging project, ₹50 budget alert
- [ ] `terraform apply` (planned: 87 to add, 0 change, 0 destroy)
- [ ] Flip `functions_deployed` to `true` after the first staging functions deploy

**Secrets & data:**

- [ ] Secret versions: Turnstile test secret, `CONTACT_EMAIL_TO` = the owner's inbox, a
      placeholder `RESEND_API_KEY` (staging email fails by design)
- [ ] Admin claim for the owner on staging
- [ ] Seed placeholder content from `architecture/examples/valid/` — never a prod export

**CI — the `preview` job in `pr.yml`:**

- [x] Runs after `checks`, for same-repo PRs that change something deployable; fork and
      Dependabot PRs never reach it
- [x] Deploys Firestore rules + indexes, **all** functions, App Hosting to staging as staging's
      `github-deploy`; narrowing to changed subdomains comes later
      ([05 · CI/CD](../05-cicd.md#deploying-only-what-changed))
- [x] `concurrency: staging`, newest push wins
- [x] Smoke test (homepage + `/api/v1/ops/health`); Lighthouse report-only (3 runs, uploaded as
      an artifact, never fails the job)
- [x] PR comments via `marocchino/sticky-pull-request-comment` — one per header, updated in place
- [x] Preview URL commented on the PR, labelled staging
- [ ] First successful preview

### 7.4 · Production deploy — `.github/workflows/deploy.yml`

- [x] On push to `main`, inert until `PROD_DEPLOY_ENABLED=true` (see Prerequisites)
- [x] `concurrency: production`, never cancelled mid-deploy
- [x] Order: rules → functions → App Hosting → smoke test → `terraform apply` (staging, then
      prod) only when `infra/terraform/**` changed. Code first because Firebase makes a new HTTP
      function public on create, whereas Terraform's invoker binding fails on a function that
      doesn't exist yet. A change adding a **secret** runs `infra_only` first (RUNBOOK)
- [x] `production-infra` approval gates the apply credential, not just the job
- [x] Smoke test on homepage + health; failure → auto-redeploy of the previous commit
- [x] `pull_request`, never `pull_request_target` — fork PRs get no OIDC token
- [ ] First production run

### 7.5 · Branch protection

- [ ] `main` protected — PRs only, admins included
- [ ] Required check: `checks`
- [ ] Squash merge only, linear history, branches deleted on merge
- [ ] Conversation resolution required

### 7.6 · Monitoring & maintenance

- [ ] `backup-verify.yml` nightly — needs an identity with object read on the backups bucket
- [x] Dependabot: npm (frontend, codegen), uv, Actions, Terraform — weekly, grouped
- [ ] Uptime alerts routed to email
- [ ] Error-rate alert verified by deliberately triggering it

---

## Definition of done

1. A PR runs only the relevant checks, and merging is blocked until they're green
2. Merging to `main` deploys automatically, with an approval gate on infra changes
3. No service-account JSON key exists anywhere
4. Every PR gets a working preview URL, deployed to the staging project ([ADR 0018](../../adr/0018-staging-project-for-pr-previews.md)) — never the production one
5. Hand-editing a generated file turns CI red
6. A failed smoke test rolls back without you intervening

---

## Gotchas

**WIF setup is fiddly.** The attribute condition on the provider must match the repo exactly, or
auth fails with a message that doesn't say why. Get one workflow authenticating before writing the
other six.

**Previews run in a second Firebase project, not prod ([ADR 0018](../../adr/0018-staging-project-for-pr-previews.md)).** A PR that redeploys functions into the same project prod runs in redeploys over the live ones — the exact risk this ADR exists to avoid.

**`production` must stay main-only.** The deploy identity is bound to the environment, so the
environment's branch policy *is* the access control. Opening it to other branches re-opens prod
deploys to PR branches (ADR 0019).

**Staging is one shared slot, not one per PR.** The most recently pushed PR is whatever's live there. Two PRs pushing around the same time stomp each other's preview — fine for a solo repo, a real limit if that changes.

**Terraform drift between `envs/prod/` and `envs/staging/` is a new failure mode.** A module change now has to be reviewed against both environments, not one. `deploy.yml` applies staging first for exactly this reason.

**`-target` on prod's first IAM apply is a one-off.** Prod's full plan carries the un-deployed
ADR 0017/0015 changes until the catch-up; don't let them ride along with the IAM apply.

**Staging Lighthouse scores aren't prod's.** Staging is `noindex` on purpose (fails the SEO
"page is crawlable" audit) and scales to zero (cold starts in the performance score) — which is
why the preview's Lighthouse is report-only. Production is the number that counts.

**Emulator startup dominates backend CI.** Cache the emulator binaries or the suite takes minutes
for seconds of tests.

**Branch protection on a solo repo feels silly right up until it saves you.** Keep it.

---

**Next:** [Phase 8 · Post-Launch](./phase-8-post-launch.md)
