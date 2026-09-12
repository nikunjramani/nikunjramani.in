# Runbook

Operational procedures. Deploy, rollback, and the things that go wrong.

---

## Local development

**Prerequisites:** Node 22 · Python 3.13 (Homebrew, *not* system 3.9) · Terraform 1.9+ ·
Firebase CLI · gcloud · uv

```bash
make setup     # install both sides
make dev       # Next.js on :3000 + emulators (UI on :4040 — moved off the default :4000, which collides on macOS)
```

| Command | Does |
|---|---|
| `make gen` | Regenerate models from `architecture/schemas` |
| `make validate` | Validate schemas + example fixtures |
| `make lint` | ruff · mypy --strict · import-linter · eslint · tsc · terraform fmt |
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

## Deploy

Order is not optional — each step depends on the one before.

```bash
make deploy
# 1. terraform apply     infra, IAM, secrets, indexes
# 2. firebase deploy     rules + indexes
# 3. firebase deploy     functions (needs secrets to exist)
# 4. App Hosting         auto-builds from the git push
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
| One domain's function | `firebase functions:rollback` |
| Frontend | App Hosting console → previous release |
| Rules | `git revert` → `firebase deploy --only firestore:rules` |
| Infra | `git revert` → `terraform apply` |
| Data | Restore from the nightly export in `nikunjramani-in-backups` |

Because functions are split per domain (ADR 0011), one domain rolls back without touching
the rest.

---

## Secrets

Values live in Secret Manager. Terraform creates the *containers*; values are added
out-of-band so no secret passes through Terraform state.

```bash
echo -n "value" | gcloud secrets versions add RESEND_API_KEY --data-file=- --project=nikunjramani-in
```

### Rotation

1. Add the new version
2. Redeploy functions so they pick it up
3. Verify the dependent path (send a test email)
4. Disable the old version — don't delete until the new one is proven

---

## Admin access

```bash
python infra/scripts/set_admin_claim.py you@example.com
python infra/scripts/set_admin_claim.py someone@example.com --revoke
```

The claim lands in the **next** token issued — sign out and back in to pick it up.

---

## Backups

Nightly Firestore export → `nikunjramani-in-backups`, 30-day lifecycle.
**Restore into the emulator first and verify** before touching production, always.

---

## Common failures

| Symptom | Cause |
|---|---|
| Domain stuck "pending" for hours | GoDaddy parking records not deleted |
| Site renders empty, no errors | A document is missing `visibility` — the rule denies the read |
| API 404s but the function deployed fine | Missing rewrite in `next.config.ts` |
| Deploy fails on a secret | Secret read at import time instead of runtime |
| `uv` builds against Python 3.9 | System Python picked up; force the Homebrew 3.13 |
| Firestore query fails in prod only | Missing composite index |
