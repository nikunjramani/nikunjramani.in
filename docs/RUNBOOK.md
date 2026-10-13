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

`api_contact` binds `TURNSTILE_SECRET_KEY`; `on_contact_created` binds `CONTACT_EMAIL_TO` and
`RESEND_API_KEY`. `firebase deploy` rejects a function whose bound secret has no version, and in
production the contact service **drops every submission** while Turnstile is unconfigured
(it fails closed — an unprotected form lets anyone exhaust the rate limit). So, in order:

1. Create a Turnstile widget for `nikunjramani.in`; add a Resend API key with a verified
   sending domain.
2. `gcloud secrets versions add` for `TURNSTILE_SECRET_KEY`, `RESEND_API_KEY` and (if not
   already) `CONTACT_EMAIL_TO`.
3. Set `NEXT_PUBLIC_TURNSTILE_SITE_KEY` in `frontend/apphosting.yaml` and deploy App Hosting.
4. Deploy functions; submit the live form and confirm the email arrives.

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
| Contact form says "Thanks" but nothing arrives | Turnstile or Resend key missing — function logs show `TURNSTILE_SECRET_KEY not set in production` or `RESEND_API_KEY not set` |
| Firestore query fails in prod only | Missing composite index |
| `Could not detect runtime` / `Missing virtual environment at venv directory` | Run `make setup-backend` — Firebase needs `requirements.txt` and its own `venv/`, not `.venv/` |
| A function request hangs forever, no response, no error | Something constructed `a2wsgi.ASGIMiddleware` directly instead of using `shared/wsgi_bridge.py` — see ADR 0003's implementation note |
