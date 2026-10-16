# Runbook

Operational procedures. Deploy, rollback, and the things that go wrong.

---

## Local development

**Prerequisites:** Node 22 · Python 3.13 (via `uv`, *not* a system 3.9) · Terraform 1.9+ ·
Firebase CLI · gcloud · uv

```bash
make setup     # install both sides
make dev       # Next.js on :3000 + emulators (UI on :4040 — moved off the default :4000, which collides on macOS)
```

| Command | Does |
|---|---|
| `make gen` | Regenerate models from `architecture/schemas` |
| `make validate` | Validate schemas + example fixtures |
| `make lint` | ruff · mypy --strict · import-linter · eslint · tsc · terraform fmt (all modules) |
| `make test` | pytest + vitest |
| `make build` | Production build |

### Two accounts

This machine has a **work** Google account and a **personal** one. The Firebase project
belongs to the personal account. Neither the Firebase CLI nor gcloud defaults to it.

```bash
firebase login                                     # sign in as the personal account
gcloud auth login --account=<personal>
gcloud --account=<personal> projects describe nikunjramani-in
```

Prefer `--account=` on individual commands over changing the global default — that leaves
the work setup alone.

### Emulator ports are sticky

The emulators sometimes survive a killed shell and hold their ports, which shows up as
`Port 8080 is not open`:

```bash
lsof -ti :8080 :9199 :4040
pkill -f cloud-firestore-emulator
pkill -f firebase-storage-emulator
```

---

## Debugging (VS Code)

`.vscode/launch.json`, `tasks.json`, `settings.json` and `extensions.json` are committed —
they're project infrastructure (which interpreter, how to reach a breakpoint), not personal
editor preferences, so there's nothing to set up beyond opening the repo.

| Config | What it does |
|---|---|
| **Backend: debug a domain** | Prompts for a domain name (e.g. `contact`), runs it directly via `functions-framework` under `debugpy`. Breakpoints in `routes.py`/`service.py`/`repository.py` work normally. Starts the data-only emulator task first. |
| **Backend: debug pytest (current file)** / **all tests** | Runs the open test file, or the whole suite, under the debugger. |
| **Frontend: debug full stack** | `next dev` with both server and client breakpoints — VS Code's own [Next.js debugging recipe](https://nextjs.org/docs/app/guides/debugging), launched via `node-terminal` with a `serverReadyAction` that opens Chrome once the dev server is up. |
| **Full stack: backend domain + frontend** | Both of the above together. |

**Debug the function directly — never through the Firebase Functions emulator.** A function's
breakpoints won't reliably hit if you route through `firebase emulators:start --only functions`;
that emulator manages its own subprocess per function, which doesn't compose with an attached
debugger the way a plain `functions-framework` process does. Worse, for this project specifically,
the WSGI/ASGI bridge outright hangs the first time the emulator's underlying reloader forks — see
[ADR 0003](./adr/0003-fastapi-in-a-single-function.md)'s implementation note. The **"emulators:
data services"** task deliberately starts only Firestore, Auth and Storage — real data, no
Functions emulator in the way — and the debug configs talk to the target function's own dev server
directly on `:8091`.

---

## Deploy

Order is not optional — each step depends on the one before.

```bash
make deploy
# 1. terraform apply     infra, IAM, secrets, indexes
# 2. firebase deploy     rules + indexes
# 3. firebase deploy     functions (needs secrets to exist)
# 4. firebase deploy --only apphosting   local source → Cloud Build → rollout
```

### Pre-flight

- [ ] `make lint` and `make test` green
- [ ] `make gen && git diff --exit-code` clean
- [ ] `terraform plan` reviewed — nothing unexpected being destroyed
- [ ] New secrets present in Secret Manager
- [ ] New Firestore indexes deployed **before** the code that queries them
- [ ] Not a Friday evening

### Smoke test

- [ ] Site loads over HTTPS
- [ ] A project detail page renders
- [ ] `view-source` shows real content, not an empty shell
- [ ] Contact form delivers an email
- [ ] `/admin` login works
- [ ] An admin edit appears publicly within seconds
- [ ] Function logs clean — check immediately; missing secrets surface here

---

## CI/CD and staging

Two projects: `nikunjramani-in` (prod) and `nikunjramani-in-staging` (PR previews, ADR 0018).
Three CI identities per project, each gated by a GitHub environment (ADR 0019):

| Workflow | When | Identity · environment |
|---|---|---|
| `pr.yml` checks | every PR — only the suites its paths touch | — (`github-plan` for `terraform plan`, read-only) |
| `pr.yml` preview | same-repo PRs, after checks — only the targets touched | staging `github-deploy` · `staging` |
| `deploy.yml` deploy | push to `main` — only the targets touched | prod `github-deploy` · `production` (main only) |
| `deploy.yml` terraform | `infra/terraform/**` changed | `github-terraform` · `staging-infra`, then `production-infra` (**your approval**) |

What runs for what (`dorny/paths-filter`, same filters in both workflows):

| Change | Checks | Deploys |
|---|---|---|
| `frontend/**` (design, pages) | frontend | App Hosting |
| `backend/**` | backend | functions |
| `infra/rules/**` | — | Firestore rules + indexes (+ Storage rules on prod) |
| `infra/terraform/**` | `terraform plan` | — then, on `main`, `terraform apply` |
| `architecture/**` | schemas, backend, frontend | functions + App Hosting |
| `firebase.json`, `.firebaserc` | backend | everything |
| `.github/**` | everything | everything |
| docs, `*.md` | none (just the `checks` rollup, which branch protection requires) | nothing |

### First-time setup (done once)

1. **Terraform.** Staging in full; prod's IAM only:
   ```bash
   terraform -chdir=infra/terraform/envs/staging apply
   terraform -chdir=infra/terraform/envs/prod apply -target=module.iam \
     -target=module.app-hosting.google_firebase_app_hosting_domain.apex \
     -target=module.app-hosting.google_firebase_app_hosting_domain.www
   ```
   The `-target` on prod is deliberate, one time only: prod's full plan also carries the
   uncaught-up ADR 0017/0015 changes (phase-7-cicd.md prerequisites), which must not ride along.
2. **Staging secrets** — staging-safe values only, added with `gcloud secrets versions add`:
   `TURNSTILE_SECRET_KEY` = Cloudflare's always-passes test secret; `CONTACT_EMAIL_TO` = the
   owner's inbox; `RESEND_API_KEY` = a placeholder until a real key exists (staging email fails).
3. **Billing-account roles** Terraform can't grant (budgets live on the billing account):
   `roles/billing.costsManager` for each project's `github-terraform`, `roles/billing.viewer`
   for each `github-plan`.
4. **`frontend/apphosting.staging.yaml`** — API key and app ID from
   `firebase apps:sdkconfig WEB <staging web_app_id> --project nikunjramani-in-staging`.
5. **GitHub** (repo Settings, or `gh`):
   - Environments: `staging` (any branch), `staging-infra` (main only), `production` (main only),
     `production-infra` (main only + **you** as required reviewer)
   - Environment variables from `terraform output`: `WIF_PROVIDER` on all four; `DEPLOY_SA` on
     `staging` / `production`; `TERRAFORM_SA` on the two `-infra` ones. Plus `SITE_URL` on
     `staging` / `production` — the deploy's smoke-test target and environment link
   - Repository variables: `PROD_WIF_PROVIDER`, `PROD_PLAN_SA`, `STAGING_WIF_PROVIDER`,
     `STAGING_PLAN_SA`. Repository secrets: `TF_VAR_BILLING_ACCOUNT`, `TF_VAR_ALERT_EMAIL`
     (`infra-plan` fails fast without them)

### Updating dependencies

No bot opens dependency PRs (Dependabot was removed — one PR per ecosystem, each re-running the
whole pipeline, cost more CI than it saved). Update everything **in one PR**: bump npm
(`frontend/`, `architecture/codegen/`), `uv lock --upgrade` in `backend/functions/`, action
versions in `.github/`, and provider constraints in `infra/terraform/envs/*/backend.tf`, then let
that PR's single run — checks, both plans, a staging preview — prove it. Treat majors that need
code changes (zod, TypeScript, Vitest, Firebase, the `$ref` resolver) as their own migrations.
   - `main` protected: PRs only (admins included), required check `checks`, squash merge only,
     linear history, conversation resolution

### Turning on production deploys

`deploy.yml` does nothing unless the repository variable `PROD_DEPLOY_ENABLED` is `true` — on
since 2026-10-16. To pause prod deploys, delete it; to resume, once prod matches `main`:

```bash
gh variable set PROD_DEPLOY_ENABLED --body true
```

### Approving an infra change

A merge touching `infra/terraform/**` pauses at `production-infra`. Open the run, read the
staging apply's output (it ran first — the same modules), then approve. Approving grants a
GitHub job owner-equivalent rights on prod for that run; don't approve a run you didn't expect.

### A change that adds a secret

`deploy.yml` deploys code before Terraform, so a function that binds a brand-new secret would
deploy before the secret exists. Run **Actions → deploy → Run workflow → infra_only** first,
add the secret's value (`gcloud secrets versions add`), then merge the code.

### Staging

- Shared, single slot: the most recent PR push to deploy is what's live. Re-run that PR's
  `preview` job to put it back.
- Placeholder data only — never a prod export, never real names (the repo is public).
- Admin sign-in: sign in once on the staging URL, then
  `python infra/scripts/set_admin_claim.py <email> --project nikunjramani-in-staging`.
- Contact form is protected by staging's own App Check / reCAPTCHA Enterprise key (ADR 0020);
  email is a placeholder key, so notifications fail by design until a real Resend key exists.

---

## Rollback

**Roll back first, diagnose after.** A revert costs minutes; debugging a live broken site
costs an afternoon.

| Broken | Fix |
|---|---|
| One domain's function | Redeploy that domain from a known-good source revision (below) |
| Frontend | App Hosting console → previous release |
| Rules | `git revert` → `firebase deploy --only firestore:rules` |
| Infra | `git revert` → `terraform apply` |
| Data | Restore from the nightly export in `nikunjramani-in-backups` |

Because functions are split per domain (ADR 0011), one domain rolls back without touching
the rest.

---

### Rehearsal evidence — 2026-10-10

App Hosting rollout `phase6-rollback-rehearsal` restored build
`build-2026-10-10-003`; health returned 200. Rollout `phase6-restore-verified` then
restored `build-2026-10-10-004`; health returned 200. The latter contains ADR 0014's
cache correction and is the preferred recovery build. Repeated publish/edit/unpublish
checks passed after restoration. Do not roll back to build 003 for normal recovery:
it retains the known stale-CDN behavior. Function rollback has not been rehearsed.

### Function rollback

There is no `firebase functions:rollback` command. Record a known-good commit before
releasing, check it out in a separate worktree, run `make setup-backend`, then deploy
only the affected entrypoints with `firebase deploy --project nikunjramani-in --only
functions:api_system`. For shared-code changes, restore all affected domains and triggers.
Do not reset a working checkout with uncommitted edits. Verify `/health` and the affected
feature after redeploying. A procedure written here is not evidence of a tested rollback.

### App Hosting

The app root is `frontend`; configuration belongs in `frontend/apphosting.yaml`.
`FUNCTIONS_BASE_URL` must be available at BUILD time because Next.js serializes rewrites.
Node 22 is pinned in `frontend/package.json`. Use:

```bash
firebase deploy --only apphosting --project nikunjramani-in --non-interactive
```

The backend is in `asia-southeast1` (Mumbai is not offered for App Hosting), with
`GLOBAL_ACCESS` serving locality (`REGIONAL_STRICT` is rejected by the live API).
The custom compute identity needs `roles/firebaseapphosting.computeRunner` for builds
and artifacts, Firestore viewer for SSR, and the custom session-auth role for cookies.
It has no Firestore write permission. GitHub OAuth is optional for local-source deploys.

## Secrets

Values live in Secret Manager. Terraform creates the *containers*; values are added
out-of-band so no secret passes through Terraform state.

```bash
echo -n "value" | gcloud secrets versions add RESEND_API_KEY --data-file=- --project=nikunjramani-in
```

### Rotation

1. Add the new version
2. Redeploy the functions that bind it (`secrets=[...]` in their decorator) so they pick it up
3. Verify the dependent path (send a test email)
4. Disable the old version — don't delete until the new one is proven

### Contact form keys — required before the next functions deploy

Abuse protection is Firebase App Check with reCAPTCHA Enterprise (ADR 0020) — no secret. The
key comes from Terraform (`terraform output recaptcha_site_key`) and is set as
`NEXT_PUBLIC_RECAPTCHA_SITE_KEY` in `frontend/apphosting*.yaml`. In production the contact
service **drops every submission** without a valid App Check token (it fails closed — an
unprotected form lets anyone exhaust the rate limit).

Email is the one part that needs secrets: `on_contact_created` binds `CONTACT_EMAIL_TO` and
`RESEND_API_KEY`, and `firebase deploy` rejects a function whose bound secret has no version. So:

1. Add a Resend API key with a verified sending domain.
2. `gcloud secrets versions add` for `RESEND_API_KEY` and (if not already) `CONTACT_EMAIL_TO`.
3. Deploy functions; submit the live form and confirm the email arrives.

Until then, `RESEND_API_KEY` can hold a **single newline** (prod does, since 2026-10-16) —
Secret Manager rejects an empty version, and the settings strip whitespace, so the deploy accepts
it and `send_email` logs `RESEND_API_KEY not set — skipping send` instead of failing. Messages
are still stored in `contact_messages`.

```powershell
$f = "$env:TEMP\newline"; [IO.File]::WriteAllBytes($f, [byte[]]@(10))
gcloud secrets versions add RESEND_API_KEY --data-file="$f" --project nikunjramani-in
```

### Removing REVALIDATE_TOKEN (one-time, ADR 0015)

Deploy App Hosting with the current `apphosting.yaml` (no `REVALIDATE_TOKEN`) **before**
`terraform apply`, which destroys the secret.

### The Firebase browser API key isn't a secret, but GitHub will flag it anyway

`frontend/apphosting.yaml`'s `NEXT_PUBLIC_FIREBASE_API_KEY` is committed in plaintext
on purpose — Firebase client API keys identify the project, they don't authorize
anything, and security is enforced by Firestore/Storage rules, not by hiding this
key. GitHub's secret scanner doesn't know that and will open a "Google API Key"
alert on it regardless; resolve it as a false positive with a comment explaining why.

Still worth hardening for real, independent of the alert: check
`gcloud services api-keys list --project=nikunjramani-in` for an empty
`browserKeyRestrictions` — an unrestricted key can be embedded on *any* site and
used to call Firebase Auth against your project from there. Fix once:

```bash
gcloud services api-keys update <key-id> --project=nikunjramani-in \
  --allowed-referrers="https://nikunjramani.in/*,https://www.nikunjramani.in/*,https://nikunjramani-in--nikunjramani-in.asia-southeast1.hosted.app/*"
```

Verify: a request carrying one of those as `Referer` succeeds; one with no referrer
gets `403 API_KEY_HTTP_REFERRER_BLOCKED`.

---

## Admin access

```bash
python infra/scripts/set_admin_claim.py you@example.com
python infra/scripts/set_admin_claim.py someone@example.com --revoke
```

The claim lands in the **next** token issued — sign out and back in to pick it up.

---

## Backups

Nightly JSON export → `nikunjramani-in-backups`, 30-day lifecycle. The collection list is
`BACKED_UP_COLLECTIONS` in `shared/core/collections.py`. This is **not**
GCP's native Firestore export format; `gcloud firestore import` cannot restore it.
The format is one `<UTC timestamp>/<collection>.json` file per collection, containing
`[{"id": "document-id", "data": {...}}]`. Only the 11 named top-level collections are
included; subcollections and rate-limit counters are not backed up.

```bash
gcloud scheduler jobs run firebase-schedule-nightly_backup-asia-south1 \
  --location=asia-south1 --project=nikunjramani-in
gcloud storage ls --recursive gs://nikunjramani-in-backups/
```

Verify all 11 files for the same timestamp, valid JSON, and sensible document counts.
Restore by reading those files, applying `shared.core.timestamps.to_firestore` to each
`data` object, and writing it to the original collection/document ID using the Admin SDK.
Set `FIRESTORE_EMULATOR_HOST` explicitly and use an isolated emulator project first.
A production restore must follow a fresh backup and a reviewed collection/document diff;
it is not part of an ordinary code rollback.
**Restore into the emulator first and verify** before touching production, always.

---

## Common failures

| Symptom | Cause |
|---|---|
| Domain stuck "pending" for hours | GoDaddy parking records not deleted |
| Site renders empty, no errors | A document is missing `visibility` — the rule denies the read |
| API 404s but the function deployed fine | Missing rewrite in `next.config.ts` |
| Deploy fails on a secret | Secret read at import time instead of runtime |
| `uv` builds against Python 3.9 | System Python picked up; `make PYTHON=$(uv python find 3.13)` |
| Contact form says "Thanks" but nothing arrives | App Check rejected the submission (logs: `App Check verification failed`) — check the site key matches the project and the domain is in the reCAPTCHA key's allowed domains — or Resend isn't set up (`RESEND_API_KEY not set`) |
| Firestore query fails in prod only | Missing composite index |
| `Could not detect runtime` / `Missing virtual environment at venv directory` | Run `make setup-backend` — Firebase needs `requirements.txt` and its own `venv/`, not `.venv/` |
| A function request hangs forever, no response, no error | Something constructed `a2wsgi.ASGIMiddleware` directly instead of using `shared/wsgi_bridge.py` — see ADR 0003's implementation note |
