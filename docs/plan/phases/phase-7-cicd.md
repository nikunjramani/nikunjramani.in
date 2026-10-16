# Phase 7 · CI/CD Hardening

**~5 hours** · Status: 🟡 PR checks + staging previews live (PR #2 green, 2026-10-15); prod
deploys await the catch-up (Prerequisites)

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
- [x] **Prod caught up with `main` before `PROD_DEPLOY_ENABLED` is set.** Done 2026-10-16 as a
      watched first run of `deploy.yml` (functions → App Hosting, `--force` deleting the old 12),
      then `infra_only` for the Terraform drift. `RESEND_API_KEY` holds a single-newline placeholder
      until Resend is set up (Secret Manager rejects empty) — `send_email` skips sending on a
      blank key. Original note: as of
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
- [x] Applied: `envs/staging` in full; `envs/prod` with `-target=module.project` /
      `-target=module.iam` only (RUNBOOK) — 2026-10-15
- [x] Billing-account roles granted: `billing.viewer` (both `github-plan`),
      `billing.costsManager` (both `github-terraform`)
- [x] GitHub environments + variables + Terraform secrets
- [x] Verified keyless in `staging` (preview deploy) and for both `github-plan`s (PR plans);
      `production` / `production-infra` are first exercised by `deploy.yml`
- [ ] Trim any role the first real runs prove unnecessary

### 7.2 · PR checks — `.github/workflows/pr.yml`

Each `pr.yml` job checks out and calls one composite action in `.github/actions/`
(`schema-check`, `backend-checks`, `frontend-checks`, `terraform-plan`, `firebase-deploy`). They
are jobs of the one `pr.yml` run on purpose: a required check that lives in a separate
path-filtered workflow never reports on PRs outside its paths, and blocks them forever;
path-skipped jobs inside one run count as passed. No config is hard-coded in CI — project IDs
from `.firebaserc`, URLs from each environment's `SITE_URL`, build env from `apphosting.yaml`.

- [x] `schemas` — validate, `make gen`, fail on diff (moved from `schemas.yml`, now deleted)
- [x] `backend` — ruff, ruff format, mypy strict, import-linter, pytest on the Firestore
      emulator. `REQUIRE_FIRESTORE_EMULATOR` turns the conftest's skip into a failure, so a broken
      emulator start can't pass as 61 skipped tests
- [x] `frontend` — tsc, eslint, vitest, `next build`
- [x] `infra-plan` — fmt, validate, plan for prod and staging, each posted as its own PR comment
- [x] `checks` — rolls the above up into the single required status check
- [x] Path filters (`dorny/paths-filter`); npm, uv and emulator caching
- [x] First green run on a real PR (#2, 2026-10-15)

### 7.3 · Staging project & preview deploys ([ADR 0018](../../adr/0018-staging-project-for-pr-previews.md))

**Project-aware config:**

- [x] `kernel/config.py` reads the project from `GCLOUD_PROJECT` (Firebase reserves the
      `FIREBASE_` dotenv prefix) — staging functions run as staging's own runtime SA. Tested
- [x] `backend/functions/.env.nikunjramani-in-staging` (and its `.gitignore` exception)
- [x] `frontend/apphosting.staging.yaml` — staging Firebase config, functions URL, App Check
      reCAPTCHA site key (ADR 0020; was a Turnstile test key)
      **test** site key, `SITE_INDEXABLE=false`
- [x] Fill its `NEXT_PUBLIC_FIREBASE_API_KEY` / `APP_ID` from the staging web app after apply
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
- [x] Staging App Hosting hostname added to Auth's authorized domains

**Terraform:**

- [x] `infra/terraform/envs/staging/` — same modules, staging project, ₹50 budget alert
- [x] `terraform apply` — staging matches the configuration (no pending changes)
- [x] Flip `functions_deployed` to `true` after the first staging functions deploy
- [x] Provision what a first `firebase deploy` would otherwise create itself (see Gotchas):
      service-agent bindings, `developerconnect` / `iam` / `pubsub` APIs, the default
      `firebase-app-hosting-compute` account
- [x] TTL fields declare `index_config {}` to match `firestore.indexes.json`'s fieldOverrides

**Secrets & data:**

- [x] Secret versions: `CONTACT_EMAIL_TO` = the owner's inbox, a
      placeholder `RESEND_API_KEY` (staging email fails by design)
- [ ] Admin claim for the owner on staging
- [ ] Seed placeholder content from `architecture/examples/valid/` — never a prod export

**CI — the `preview` job in `pr.yml`:**

- [x] Runs after `checks`, for same-repo PRs that change something deployable; fork PRs never
      reach it
- [x] Deploys to staging, as staging's `github-deploy`, only the targets the PR touched:
      Firestore rules + indexes (`infra/rules/**`), functions (`backend/**`), App Hosting
      (`frontend/**`); `architecture/**` → functions + App Hosting; `.github/**`, `firebase.json`,
      `.firebaserc` → all. Docs-only PRs run just `changes` + `checks`. Within functions it's
      still **all** of them; narrowing to changed subdomains comes later
      ([05 · CI/CD](../05-cicd.md#deploying-only-what-changed))
- [x] `concurrency: staging`, newest push wins
- [x] Smoke test (homepage + `/api/v1/ops/health`); Lighthouse report-only (3 runs, uploaded as
      an artifact, never fails the job)
- [x] PR comments via `marocchino/sticky-pull-request-comment` — one per header, updated in place
- [x] Preview URL commented on the PR, labelled staging
- [x] Deploy retried up to 3× (90s apart) for first-deploy propagation races
- [x] First successful preview — all 18 functions ACTIVE, homepage 200, health reports
      `nikunjramani-in-staging`, `robots.txt` disallow + `X-Robots-Tag: noindex` (2026-10-15)

### 7.4 · Production deploy — `.github/workflows/deploy.yml`

- [x] On push to `main`, gated by `PROD_DEPLOY_ENABLED=true` (enabled 2026-10-16)
- [x] `concurrency: production`, never cancelled mid-deploy
- [x] Each push deploys only the targets it changed, with the same filters as the preview
      (docs-only: nothing); a manual run deploys everything
- [x] Order: rules → functions → App Hosting → smoke test → `terraform apply` (staging, then
      prod) only when `infra/terraform/**` changed. Code first because Firebase makes a new HTTP
      function public on create, whereas Terraform's invoker binding fails on a function that
      doesn't exist yet. A change adding a **secret** runs `infra_only` first (RUNBOOK)
- [x] `production-infra` approval gates the apply credential, not just the job
- [x] Smoke test on homepage + health; failure → auto-redeploy of the previous commit
- [x] `pull_request`, never `pull_request_target` — fork PRs get no OIDC token
- [ ] First production run

### 7.5 · Branch protection

- [x] `main` protected — PRs only, admins included, no force pushes or deletion
- [x] Required check: `checks`
- [x] Squash merge only, linear history, branches deleted on merge
- [x] Conversation resolution required

### 7.6 · Monitoring & maintenance

- [ ] `backup-verify.yml` nightly — needs an identity with object read on the backups bucket
- [x] Dependency updates: **no bot** — Dependabot was tried and removed (one PR per ecosystem,
      each a full pipeline run). Updates go in one deliberate PR (RUNBOOK · Updating dependencies)
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

**A project's first functions deploy wants to edit project IAM.** The Firebase CLI grants
service agents roles for event triggers (GCS agent → `pubsub.publisher`, Pub/Sub agent →
`serviceAccountTokenCreator`, compute SA → `run.invoker` + `eventarc.eventReceiver`). As owner
that's silent; as CI's `github-deploy` it fails. `modules/iam` declares them, so the CLI finds them
present and skips its own `setIamPolicy`.

**`firebase deploy` provisions things itself on a fresh project — CI can't.** Beyond the
service agents: App Hosting's deploy enables `developerconnect.googleapis.com` and creates the
`firebase-app-hosting-compute` account if either is missing. Terraform declares both (the
account with `create_ignore_already_exists`, adopting prod's). A new project needs these before
its first CI deploy, not after.

**A fresh project's first functions deploy races itself.** The Eventarc service agent isn't
usable for minutes, the `gcf-artifacts` repo doesn't exist until one build creates it, and
parallel builds 409 on the source bucket. Google's remedy is "retry in a few minutes", which is
why the deploy steps retry. A function left `FAILED` by such a race is safest deleted and
redeployed.

**Firestore TTL fields have two writers.** `firestore.indexes.json` (generated) sets their
`fieldOverrides` and `firebase deploy` applies it; Terraform owns the TTL. Both must agree on
`index_config` or each run undoes the other.

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
