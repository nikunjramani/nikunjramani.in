# Deploy progress — live status

A running log of the actual execution of [09 · Deploy & CI/CD Implementation](./09-deploy-cicd-implementation.md),
kept up to date as each part completes. If you're picking this up, **read "Right now"
first** — it tells you exactly what to run next.

---

## Decisions made (per your "decide the rest yourself")

- **Budget alert: ₹100/month**, not the plan's original ₹500 default. Notifies at
  50/90/100% (₹50 / ₹90 / ₹100). One variable if you ever want it different:
  `budget_amount` in `infra/terraform/envs/prod/variables.tf`.
- **Alert email**: your Google account (the one `gcloud`/Terraform are authenticated
  as). Budget, uptime and error-rate notifications all go there.
- **Resend / Turnstile**: deferred, as recommended in the plan. The contact form works
  without them — it just skips sending a confirmation email and skips the spam check
  until you add real keys later (`gcloud secrets versions add`, no redeploy needed).

---

## Right now — one command you need to run

I hit a wall: Claude Code's own safety layer (a classifier that guards infrastructure
changes) is declining to run `terraform apply` and even some read-only `gcloud` checks
in this session, regardless of retries. This is intentional on their end — it's not
something I should route around, and I haven't tried to. It means **you need to run
one command yourself.**

Everything up to this point already happened successfully:

- ✅ Terraform state bucket created (`gs://nikunjramani-in-tfstate`)
- ✅ `terraform init` against that real backend
- ✅ `terraform.tfvars` written (billing account, alert email, budget = ₹100) — never
  committed, it's gitignored
- ✅ All 17 required Google Cloud APIs enabled on `nikunjramani-in` (Firestore, Cloud
  Functions, Cloud Run, Secret Manager, Billing Budgets, App Hosting, etc.) — confirmed
  in Terraform state
- 🟡 **One resource failed and stopped the apply**: the ₹100 budget alert itself. The
  error was `SERVICE_DISABLED` for `billingbudgets.googleapis.com` — not a real
  problem, just the normal lag between "API enabled" and "API actually live" (seconds
  to a couple of minutes). A retry should just work.

**Run this:**

```bash
cd "infra/terraform/envs/prod"
terraform apply
```

Terraform will show a plan (budget alert, 3 service accounts + Workload Identity
Federation pool for GitHub Actions, the Firestore database, 2 Storage buckets, 4 empty
Secret Manager containers, the monitoring notification channel + error-rate alert
policy, and a Firebase Web App registration — **no App Hosting backend yet**, that
part stays a no-op until Part E's console step). Type `yes` when it asks.

If it fails again with the same `SERVICE_DISABLED` message, just run `terraform apply`
once more — it's idempotent, nothing already created gets touched twice.

**Tell me once it's applied successfully** (or paste me the error if it isn't) and
I'll pick up from Part C (loading the non-third-party secrets) onward.

---

## What's already done in code (this session)

- `infra/terraform/modules/app-hosting/main.tf` — was a stub, now creates the Firebase
  Web App registration and (once a GitHub connection exists) the real
  `google_firebase_app_hosting_backend` resource.
- `infra/terraform/modules/functions/main.tf` — added a `services_deployed` gate on the
  Cloud Run invoker IAM binding, defaulting to `false`. The binding targets a Cloud Run
  service by name, and that service doesn't exist until `firebase deploy --only
  functions` has run once — so this module is a deliberate no-op on the *first* apply,
  then gets flipped to `true` for a second apply right after the first functions
  deploy (Part D → a follow-up apply).
- `infra/terraform/envs/prod/main.tf` — wired both modules in, matching the pattern of
  the other five.
- `infra/terraform/envs/prod/variables.tf` — added `functions_deployed` and
  `apphosting_github_connection_id`, both default to the "nothing happens yet" state;
  `budget_amount` default changed 500 → 100.
- `infra/terraform/envs/prod/outputs.tf` — added `apphosting_backend_note` and
  `configured_function_domains`.
- `.gitignore` — added `*.tfplan` / `tfplan.out` (Terraform plan files can contain
  resource details; they're local artifacts, never committed).
- All of the above passed `terraform validate` and `make lint-infra` before this was
  written.

---

## What's next, in order (unchanged from the main plan)

1. **You**: run the `terraform apply` above.
2. **Me**: load `REVALIDATE_TOKEN` and `CONTACT_EMAIL_TO` into Secret Manager (no
   third-party accounts needed for either).
3. **Me**: `firebase deploy --only firestore:rules,firestore:indexes`, then
   `firebase deploy --only functions` — all 12 domains.
4. **Me**: flip `functions_deployed = true` in `terraform.tfvars`, re-apply, to wire
   the public-invoker IAM bindings now that the Cloud Run services exist.
5. **You** (console, ~2 min): Firebase Console → App Hosting → connect the
   `nikunjramani/nikunjramani.in` GitHub repo. I'll hand you the exact link when we get
   here.
6. **Me**: write `apphosting.yaml`, set `apphosting_github_connection_id` from the
   connection's resource name, re-apply to create the actual backend.
7. **You + me**: DNS cutover at GoDaddy (Part F) — deliberately its own step, done on a
   weekday morning per the plan's own gotcha.
8. **Me**: the five missing GitHub Actions workflow files (Part H), branch protection,
   Dependabot.
9. **Both**: fill in `docs/RUNBOOK.md` for real and rehearse one rollback before
   calling Phase 6 done.

Full detail on every step above is in
[09 · Deploy & CI/CD Implementation](./09-deploy-cicd-implementation.md).
