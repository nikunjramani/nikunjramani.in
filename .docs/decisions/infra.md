# Infrastructure decisions

Terraform (`google` + `google-beta`), Firestore rules, GCP. Root: [infra/](../../infra/).
Flow: [CODE_FLOW §11](../CODE_FLOW.md#11--infrastructure). Entries IN-01…IN-14 were backfilled on
2026-10-16 from the code and its history.

### IN-01 · Two projects, two Terraform roots, one set of modules

- **Where:** [infra/terraform/envs/{prod,staging}](../../infra/terraform/envs/), [modules/](../../infra/terraform/modules/)
- **Decision:** `nikunjramani-in` (prod) and `nikunjramani-in-staging` (PR previews); each env is a
  thin root wiring the same modules with its own tfvars and state bucket (`<project>-tfstate`).
- **Why:** a preview deploy in the prod project would overwrite prod's functions — there's no
  per-function isolation inside one project. Staging state lives in staging, so no staging identity
  can touch prod state.
- **Related:** ADR 0018

### IN-02 · Terraform creates secret containers; people add the values

- **Where:** [modules/secrets](../../infra/terraform/modules/secrets/main.tf)
- **Decision:** `google_secret_manager_secret` + accessor bindings only; values via `gcloud secrets versions add`.
- **Why:** a value in Terraform is a value in state. Cost: a manual step, and a deploy-order trap
  (a function binding a new secret needs the value first — `infra_only` run).
- **Related:** BE-25, CI-11

### IN-03 · The media bucket is plain GCS guarded by IAM, not Firebase Storage

- **Where:** [modules/storage](../../infra/terraform/modules/storage/main.tf)
- **Decision:** uniform bucket-level access; a managed folder makes only `public/` world-readable;
  uploads arrive by signed URL (BE-26); versioning with non-current versions deleted after 30 days.
  `infra/rules/storage.rules` exists for the emulator only.
- **Why:** IAM expresses "public prefix, everything else private" without Storage rules; versioning
  makes an accidental overwrite recoverable without keeping deletes forever.
- **Outcome:** `firebase deploy --only storage` fails on prod ("Firebase Storage has not been set
  up") — it's never deployed.
- **Since:** storage-rules removal 2026-10-16 · **Related:** lessons-learned

### IN-04 · Backups bucket keeps 30 days

- **Where:** `google_storage_bucket.backups` — lifecycle `age = 30`
- **Why:** bounded cost; a month covers noticing a bad edit.

### IN-05 · Functions get their invoker binding from Terraform, after they exist

- **Where:** [modules/functions](../../infra/terraform/modules/functions/main.tf)
- **Decision:** `allUsers` `roles/run.invoker` on each HTTP function via
  `google_cloud_run_v2_service_iam_member`, names with `_` → `-`; gated by `services_deployed`.
- **Why:** 2nd-gen functions are Cloud Run **v2** services (the v1 resource 404s); the service must
  exist first. Admin routes authenticate in-process (BE-16).
- **Outcome:** CI deploys code before Terraform (CI-11).

### IN-06 · Runtime limits and secret bindings live in the Python decorators

- **Where:** `make_function(...)`, trigger decorators; not in Terraform
- **Why:** `firebase deploy` owns the function resource; two owners of one setting drift.

### IN-07 · Least-privilege identities; CI identities bound to GitHub environments

- **Where:** [modules/iam](../../infra/terraform/modules/iam/main.tf)
- **Decision:** `functions-runtime` and `apphosting-runtime` (Firestore *viewer*) at runtime; for CI,
  `github-plan` (read), `github-deploy` (only jobs in the `staging`/`production` environment) and
  `github-terraform` (only `staging-infra`/`production-infra`), via WIF `attribute.environment`.
- **Why:** a PR branch can't enter a main-only environment, so it can't get a prod token at all;
  the owner-equivalent Terraform identity is reachable only through an approval.
- **Related:** ADR 0019

### IN-08 · The Terraform apply identity must hold every role its resources need — even to read them

- **Where:** `terraform_roles` in modules/iam
- **Decision:** includes `roles/recaptchaenterprise.admin` for the App Check key.
- **Why:** refresh reads every resource before applying; a missing read permission 403s the whole
  apply, so Terraform can't grant itself the fix. PR plans pass regardless (they run as `roles/viewer`).
- **Outcome:** existing projects need a one-time manual grant when a new resource type arrives.
- **Since:** 2026-10-16 · **Related:** lessons-learned

### IN-09 · The billing budget needs `user_project_override`

- **Where:** provider blocks in `envs/*/main.tf`
- **Why:** budgets live on the billing account, not a project; without a billing project the API
  call bills the ADC client's own project and fails with a misleading `SERVICE_DISABLED`.

### IN-10 · App Hosting runs in `asia-southeast1`; everything else in `asia-south1`

- **Where:** `apphosting_region` in `envs/*/variables.tf`
- **Why:** App Hosting doesn't offer Mumbai (the live API returns "location not found"). Its
  backend uses `GLOBAL_ACCESS` serving (`REGIONAL_STRICT` is rejected).

### IN-11 · App Hosting's default compute account is adopted, not created

- **Where:** `google_service_account.apphosting_default` (`create_ignore_already_exists`)
- **Why:** the CLI insists that account exists and tries to create it on deploy, which CI can't do;
  the backend actually runs as `apphosting-runtime`, so this one gets no roles.

### IN-12 · App Check is a score-based reCAPTCHA Enterprise key per project

- **Where:** [modules/app-check](../../infra/terraform/modules/app-check/main.tf)
- **Decision:** `integration_type = SCORE` (invisible), domains restricted to the site's hosts,
  registered as the web app's App Check provider, 1-hour tokens.
- **Why:** no challenge for visitors, no secret anywhere (the function verifies tokens with Google's
  public keys). The site key is public by design.
- **Related:** ADR 0020

### IN-13 · Firestore rules deny every client write and default-deny unknown collections

- **Where:** [infra/rules/firestore.rules](../../infra/rules/firestore.rules) (public-read block generated, SC-03)
- **Decision:** public read only for listed collections where `visibility == "public"`; `allow write: if false` everywhere.
- **Why:** a new collection is private until consciously exposed; every write goes through the API
  so validation, rate limits and audit can't be bypassed.
- **Related:** ADR 0007, plan/03-security.md

### IN-14 · TTL policies clean up rate-limit windows and old messages

- **Where:** `google_firestore_field` `contact_ttl`, `rate_limit_ttl` in [modules/firestore](../../infra/terraform/modules/firestore/main.tf)
- **Why:** both collections grow forever otherwise; nothing depends on the deletion timing for correctness.
