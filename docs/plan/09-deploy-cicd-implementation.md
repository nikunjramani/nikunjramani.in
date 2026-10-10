# 09 · Deploy & CI/CD Implementation Plan

A concrete, step-by-step execution plan for taking Phase 6 (Deploy & DNS) and Phase 7
(CI/CD Hardening) from "designed" to "done" — grounded in what's actually in the repo
today, not just what the phase checklists say. Written before execution starts, per the
decision to review the full sequence first. Supersedes nothing in
[Phase 6](./phases/phase-6-deploy.md) or [Phase 7](./phases/phase-7-cicd.md) — it's the
detailed "how" underneath their checklists.

**Billing confirmed live** on `nikunjramani-in` (Blaze, billing account
`XXXXXX-XXXXXX-XXXXXX`) as of 2026-10-10. That's what unblocks everything below.

---

## 0 · Reality check — what's already built vs. what's still a stub

Phase 6/7's checklists were written before most of the Terraform existed. Re-reading the
actual module source now, most of the hard part is **already written code** — what's
missing is narrower than the checklists suggest:

| Module | State |
|---|---|
| `modules/project` | ✅ Written — enables every required API (including `firestore.googleapis.com` and `billingbudgets.googleapis.com`, both currently disabled), creates the ₹500 budget alert |
| `modules/iam` | ✅ Written — functions SA, App Hosting SA (read-only), **and the full WIF pool + GitHub deploy SA that Phase 7.1 asks for** |
| `modules/firestore` | ✅ Written — database, indexes, rules release |
| `modules/storage` | ✅ Written — buckets, CORS, lifecycle |
| `modules/secrets` | ✅ Written — 4 Secret Manager containers (`RESEND_API_KEY`, `CONTACT_EMAIL_TO`, `TURNSTILE_SECRET_KEY`, `REVALIDATE_TOKEN`) + accessor bindings |
| `modules/monitoring` | ✅ Written — uptime check, error-rate alert |
| `modules/functions` | 🟡 Written (per-domain memory/`max_instances`/public-invoker map, all 12 domains) but **not referenced in `envs/prod/main.tf`** — the module exists, nothing calls it |
| `modules/app-hosting` | 🔴 Genuine stub — just variables and a note. Needs the actual backend resource, and it needs the GitHub OAuth connection authorised in console *first* (Terraform can't do that handshake) |
| `envs/prod/main.tf` | 🟡 Wires `project`, `iam`, `firestore`, `storage`, `secrets`, `monitoring` — **missing `functions` and `app-hosting` module blocks entirely** |
| `.github/workflows/` | 🟡 Only `schemas.yml` exists. `ci-frontend.yml`, `ci-backend.yml`, `infra-plan.yml`, `preview.yml`, `deploy.yml`, `backup-verify.yml` all need writing |
| `apphosting.yaml` | 🔴 Doesn't exist |
| Terraform state bucket | 🔴 Doesn't exist |
| `terraform.tfvars` | 🔴 Doesn't exist (only `.example`) |

So the real remaining work is: two Terraform module-wiring gaps, one genuine module to
write (`app-hosting`), the bootstrap/apply/deploy sequence itself, five workflow files,
and the console-only steps nothing can script.

---

## 1 · Division of labour

Claude Code's own safety layer blocks real-infrastructure commands (bucket creation,
`terraform apply`, `firebase deploy`, anything that spends money or touches a live
service) and asks for your explicit approval on each one as it comes up — this is
intentional, not a bug to route around. So the execution model is:

- **Code changes** (Terraform `.tf` files, workflow YAML, `apphosting.yaml`,
  documentation) — I write and you review in the diff, same as everything so far.
- **Provisioning commands** (`gsutil`, `terraform apply`, `firebase deploy`, `gh` CLI
  for repo settings) — I run them, Claude Code prompts you per command, you approve
  each as we go. No permission rule needed; this just means more prompts during this
  phase than usual.
- **Console-only steps** (OAuth consent screen, enabling the Google sign-in provider,
  authorising the GitHub connection for App Hosting, GoDaddy DNS edits) — only you can
  click these. I'll tell you exactly when and give the exact link/values.

---

## 2 · Sequence

Each part is independently checkpointable — we verify one before moving to the next,
rather than running the whole thing blind.

### Part A · Console prerequisites (you, ~10 min)

Nothing after this works without these three:

1. **OAuth consent screen** — console link I'll hand you at the time. External, your
   email as support contact.
2. **Enable the Google sign-in provider** — Firebase Console → Authentication →
   Sign-in method.
3. Nothing else is console-gated at this stage — Firestore's database creation is
   actually a `gcloud firestore databases create` call (scriptable), not console-only,
   contrary to `bootstrap.sh`'s current checklist text. I'll fold that into Part B.

### Part B · Bootstrap + Terraform apply (me running commands, you approving each)

1. `infra/scripts/bootstrap.sh` — creates the `nikunjramani-in-tfstate` GCS bucket
   (versioned, uniform bucket-level access). This is the exact command that was blocked
   earlier; first thing we re-run once you say go.
2. `terraform.tfvars` (gitignored, never committed):
   ```hcl
   billing_account = "XXXXXX-XXXXXX-XXXXXX"
   alert_email     = "<your real inbox>"
   ```
3. **Fill the two Terraform gaps** before `apply`:
   - Add `module "functions"` and `module "app-hosting"` blocks to
     `envs/prod/main.tf`, wired the same way the other five already are
     (`depends_on = [module.project]`, outputs passed where needed).
   - Write `modules/app-hosting/main.tf` for real: a `google_apphosting_backend`
     (beta) resource, taking the GitHub connection as a variable rather than creating
     it — the connection itself is console-only (step below) and Terraform just
     references it once it exists.
4. `cd infra/terraform/envs/prod && terraform init` — binds to the now-existing state
   bucket.
5. `terraform plan` — reviewed together before anything applies. This is where we
   confirm: budget ₹500/mo (adjustable — say now if you want a different number),
   `max_instances = 3` on every domain except `api_media` (`2`, it does image
   processing), nothing unexpected gets created.
6. `terraform apply` — creates: enabled APIs (including Firestore and billing-budgets,
   currently disabled), the budget alert, Firestore database, Storage buckets, 4 Secret
   Manager containers (empty — values added next), the 3 service accounts, the WIF pool
   + provider, uptime check, error-rate alert.
7. Verify: `gcloud firestore databases describe`, budget alert visible in console,
   `terraform output` shows `functions_sa`, `apphosting_sa`, `deploy_sa`,
   `wif_provider`.

### Part C · Secrets (you provide values, I load them)

The 4 secret containers exist after `apply` but are empty — Terraform deliberately never
touches secret *values* (ADR-aligned: no secret ever passes through state).

- `REVALIDATE_TOKEN` — I generate a random token, you don't need an account for this one.
- `CONTACT_EMAIL_TO` — your real inbox, just a value, not a third-party account.
- `RESEND_API_KEY`, `TURNSTILE_SECRET_KEY` — **need real third-party accounts only you
  can create.** Per the earlier question that got interrupted: my recommendation is to
  **defer both** for the first deploy. `shared/services/email.py` and
  `src/contact/turnstile.py` both have a documented dev-mode skip when the key is unset
  — the contact form still accepts submissions, it just doesn't send an email or check
  Turnstile yet. Nothing about launch is blocked on signing up for Resend/Cloudflare; add
  real keys later with `gcloud secrets versions add`, no redeploy of code required.
  Say now if you'd rather set these up first.

```bash
echo -n "<value>" | gcloud secrets versions add REVALIDATE_TOKEN --data-file=-
# repeat per secret
```

### Part D · Backend deploy

1. `firebase deploy --only firestore:rules,firestore:indexes` — ships the generated
   `infra/rules/firestore.rules` (including the new required-field assertions from
   §1.6) and indexes.
2. `firebase deploy --only functions` — all 12 domains. Confirm the deploy log lists
   every one; a silently-skipped domain is the exact failure mode CLAUDE.md's gotchas
   warn about.
3. `curl https://<region>-nikunjramani-in.cloudfunctions.net/api_system/health` directly
   (bypassing any rewrite) to confirm the raw function responds before touching DNS/
   rewrites.
4. Confirm `/docs` (FastAPI's auto-generated Swagger UI) is disabled in the deployed
   build — it should already be gated by an environment check; verify it 404s.

### Part E · Frontend / App Hosting

1. **Console step (you):** Firebase Console → App Hosting → connect the
   `nikunjramani/nikunjramani.in` GitHub repo. This is the OAuth handshake Terraform
   cannot do.
2. Write `apphosting.yaml` at the repo root — build command, Node version, env vars
   (`NEXT_PUBLIC_*` Firebase config, which is public by design; nothing secret goes
   here).
3. `terraform apply` again, now that the GitHub connection exists, to create the actual
   `google_apphosting_backend` resource referencing it.
4. First build triggers automatically from the `main` branch push (or a manual trigger
   in console). Confirm it succeeds and the site is reachable on the default
   `*.web.app` / App Hosting URL before touching DNS.
5. Confirm server-side env vars (Admin SDK credentials, secret values) are **not**
   present in the client bundle — `curl` the deployed HTML/JS and grep for them.

### Part F · DNS (you + me together, per [07 · Domain Setup](./07-domain-setup.md))

This is the one genuinely hard-to-reverse-cleanly step (GoDaddy parking/forwarding
deletion), so we do it deliberately, on a weekday morning per the existing gotcha, not
folded into a larger batch:

1. Add custom domain in Firebase App Hosting console for apex + `www` → gives you the
   TXT and two A records.
2. You add those at GoDaddy, delete the default parking `A` record and any conflicting
   `CNAME www`, turn off Domain Forwarding.
3. `dig nikunjramani.in +short` / `dig www.nikunjramani.in +short` to confirm — not the
   browser, which caches.
4. Wait for verification + SSL (minutes to ~an hour typically).

### Part G · SEO + smoke tests

Follow Phase 6 §6.5/§6.6 as written — Search Console, sitemap, robots.txt, Rich Results
Test, link-preview checks on LinkedIn/WhatsApp, and the full smoke-test list ending in a
**production** Lighthouse run (the only kind that counts).

### Part H · CI/CD (Phase 7, now actually buildable)

The WIF pool, deploy SA, and its IAM bindings already exist from Part B's `apply` — 7.1
is mostly just **reading `terraform output wif_provider` and `terraform output
deploy_sa`** into GitHub repo variables, not new Terraform.

1. `gh variable set WIF_PROVIDER --body "$(terraform output -raw wif_provider)"`
   `gh variable set DEPLOY_SA --body "$(terraform output -raw deploy_sa)"`
2. Write the five missing workflows (`ci-frontend.yml`, `ci-backend.yml`,
   `infra-plan.yml`, `preview.yml`, `deploy.yml`, `backup-verify.yml`) per the shapes
   already specified in [05 · CI/CD](./05-cicd.md) — path filters, Makefile targets,
   WIF auth block, the domain-scoped `firebase deploy --only functions:api_x,api_y` for
   changed domains only.
3. Verify one workflow authenticates via WIF with no JSON key before writing the rest
   (05's own gotcha — WIF's attribute condition is fiddly to get right the first time).
4. Branch protection on `main` via `gh api` or console: required checks, no direct
   pushes, linear history, conversation resolution required.
5. `backup-verify.yml` nightly cron, Dependabot config for npm/pip/Actions.
6. Deliberately trigger the error-rate alert once (e.g. a function that intentionally
   500s behind a throwaway route) to confirm monitoring actually fires, not just that
   it's configured.

### Part I · Runbook + rollback rehearsal

`docs/RUNBOOK.md` gets the deploy/rollback/rotate-secrets/restore-a-backup sections
filled in with the *actual* commands used above, not generic placeholders. Then we
deliberately roll back one function domain (`firebase functions:rollback`) to prove the
runbook works before calling Phase 6 done — per its own definition-of-done #9.

---

## 3 · Cost guardrails in effect (your "not unlimited budget" ask)

Already designed in, confirmed against the live Terraform source in §0:

- **Budget alert**: ₹500/month, notifies at 50/90/100% — a smoke alarm, not a cap. Say
  now if you want a different number; it's a one-line variable (`budget_amount` in
  `envs/prod/variables.tf`).
- **The actual spend ceiling**: `max_instances` per function — 3 for every domain, 2 for
  `api_media`. A runaway loop physically cannot scale past this.
- Storage lifecycle rules delete backups after 30 days.
- Firestore TTL on `contact_messages` after 2 years.
- Everything is sized to fit comfortably inside free-tier allowances at the traffic this
  site will realistically see (see [08 · Costs & Risks](./08-costs-and-risks.md) — the
  honest worst case without a traffic surge is ₹0).

---

## 4 · Open decisions before we start

1. Budget alert amount — keep ₹500, or a different number?
2. Resend/Turnstile — defer (recommended) or set up accounts first?
3. Alert email for budget/uptime/error-rate notifications — which inbox?

Everything else above has a concrete default already chosen and justified; flag any of
them you want changed before Part A starts.

---

**Back to:** [Plan index](./README.md) · **Detailed checklists:**
[Phase 6](./phases/phase-6-deploy.md) · [Phase 7](./phases/phase-7-cicd.md)
