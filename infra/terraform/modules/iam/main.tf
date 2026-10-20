# Least-privilege service accounts. Each identity gets exactly what it needs and nothing more.

variable "project_id" { type = string }
variable "github_repo" {
  type        = string
  description = "owner/repo — scopes the WIF binding so only this repository can deploy."
}

variable "deploy_environment" {
  type        = string
  description = "GitHub environment whose jobs may act as github-deploy (code deploys)."
}

variable "infra_environment" {
  type        = string
  description = "GitHub environment whose jobs may act as github-terraform (terraform apply)."
}

# ── Functions runtime ───────────────────────────────────────────────
resource "google_service_account" "functions" {
  project      = var.project_id
  account_id   = "functions-runtime"
  display_name = "Cloud Functions runtime"
}

locals {
  functions_roles = [
    "roles/datastore.user",      # Firestore read/write
    "roles/storage.objectAdmin", # media + backups
    "roles/secretmanager.secretAccessor",
    "roles/logging.logWriter",
    "roles/eventarc.eventReceiver",
    "roles/firebaseauth.admin", # identity/admins grants and revokes the admin custom claim
  ]

  # No Firestore role at all: the site reads and writes data only through the Python API
  # (ADR 0022). App Hosting uses this identity for builds too.
  apphosting_roles = [
    "roles/firebaseapphosting.computeRunner", # required build/artifact/source access
    "roles/secretmanager.secretAccessor",
    "roles/logging.logWriter",
  ]

  # What `firebase deploy` (rules, functions, apphosting) needs from CI.
  deploy_roles = [
    "roles/cloudfunctions.admin",
    "roles/run.admin",
    "roles/firebase.admin",
    "roles/firebaseapphosting.admin",
    "roles/iam.serviceAccountUser",
    "roles/storage.admin",
    "roles/secretmanager.viewer", # deploy checks every bound secret has a version
    "roles/cloudbuild.builds.editor",
    "roles/artifactregistry.repoAdmin", # writer + setting gcf-artifacts' image cleanup policy
    "roles/cloudscheduler.admin",       # the scheduled backup
    "roles/eventarc.admin",             # Firestore/Storage triggers
    "roles/serviceusage.serviceUsageConsumer",
  ]

  # Everything this Terraform manages. Effectively owner, which is why the binding below
  # only admits jobs in the approval-gated infra environment (ADR 0019). Billing-budget
  # rights live on the billing account and are granted by hand (docs/RUNBOOK.md).
  terraform_roles = [
    "roles/resourcemanager.projectIamAdmin",
    "roles/iam.serviceAccountAdmin",
    "roles/iam.workloadIdentityPoolAdmin",
    "roles/iam.roleAdmin",
    "roles/iam.serviceAccountUser",
    "roles/serviceusage.serviceUsageAdmin",
    "roles/secretmanager.admin",
    "roles/datastore.owner",
    "roles/storage.admin",
    "roles/monitoring.admin",
    "roles/logging.configWriter",
    "roles/run.admin",
    "roles/firebase.admin",
    "roles/firebaseapphosting.admin",
    "roles/recaptchaenterprise.admin", # the App Check key; firebase.admin covers App Check itself
  ]

  # terraform plan on PRs: read everything, change nothing.
  plan_roles = [
    "roles/viewer",
    "roles/iam.securityReviewer",
    "roles/secretmanager.viewer",
    "roles/serviceusage.serviceUsageConsumer",
  ]

  pool = google_iam_workload_identity_pool.github.name
}

resource "google_project_iam_member" "functions" {
  for_each = toset(local.functions_roles)
  project  = var.project_id
  role     = each.value
  member   = "serviceAccount:${google_service_account.functions.email}"
}

# ── App Hosting (Next.js SSR) — no data access ──────────────────────
resource "google_service_account" "apphosting" {
  project      = var.project_id
  account_id   = "apphosting-runtime"
  display_name = "App Hosting runtime (no data access)"
}

# The App Hosting CLI insists its default compute account exists and creates it on deploy if
# missing — which CI can't. Our backend runs as apphosting-runtime, so this one gets no roles.
# It already existed in prod (first manual deploy); adopt it rather than fail.
resource "google_service_account" "apphosting_default" {
  project                      = var.project_id
  account_id                   = "firebase-app-hosting-compute"
  display_name                 = "Firebase App Hosting compute service account"
  description                  = "Default service account used to run builds and deploys for Firebase App Hosting"
  create_ignore_already_exists = true
}

resource "google_project_iam_member" "apphosting" {
  for_each = toset(local.apphosting_roles)
  project  = var.project_id
  role     = each.value
  member   = "serviceAccount:${google_service_account.apphosting.email}"
}

# ── GitHub Actions via Workload Identity Federation ─────────────────
# No service-account JSON key exists anywhere. GitHub exchanges its OIDC token for a
# short-lived GCP token, and the attribute condition means only this repo can do it.
resource "google_iam_workload_identity_pool" "github" {
  project                   = var.project_id
  workload_identity_pool_id = "github-pool"
  display_name              = "GitHub Actions"
}

resource "google_iam_workload_identity_pool_provider" "github" {
  project                            = var.project_id
  workload_identity_pool_id          = google_iam_workload_identity_pool.github.workload_identity_pool_id
  workload_identity_pool_provider_id = "github-provider"

  # `environment` is only present for jobs that declare one; GitHub mints it only after
  # that environment's branch policy and required reviewers have passed.
  attribute_mapping = {
    "google.subject"        = "assertion.sub"
    "attribute.repository"  = "assertion.repository"
    "attribute.environment" = "has(assertion.environment) ? assertion.environment : ''"
  }

  # Without this condition ANY GitHub repository could impersonate the deploy account.
  attribute_condition = "assertion.repository == '${var.github_repo}'"

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

resource "google_service_account" "deploy" {
  project      = var.project_id
  account_id   = "github-deploy"
  display_name = "GitHub Actions deployer"
}

resource "google_project_iam_member" "deploy" {
  for_each = toset(local.deploy_roles)
  project  = var.project_id
  role     = each.value
  member   = "serviceAccount:${google_service_account.deploy.email}"
}

# Bound to an environment, not the repository: a workflow on a PR branch can't enter a
# main-only environment, so it can't deploy here at all.
resource "google_service_account_iam_member" "deploy_wif" {
  service_account_id = google_service_account.deploy.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${local.pool}/attribute.environment/${var.deploy_environment}"
}

resource "google_service_account" "terraform" {
  project      = var.project_id
  account_id   = "github-terraform"
  display_name = "GitHub Actions terraform apply"
}

resource "google_project_iam_member" "terraform" {
  for_each = toset(local.terraform_roles)
  project  = var.project_id
  role     = each.value
  member   = "serviceAccount:${google_service_account.terraform.email}"
}

resource "google_service_account_iam_member" "terraform_wif" {
  service_account_id = google_service_account.terraform.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${local.pool}/attribute.environment/${var.infra_environment}"
}

resource "google_service_account" "plan" {
  project      = var.project_id
  account_id   = "github-plan"
  display_name = "GitHub Actions terraform plan (read-only)"
}

resource "google_project_iam_member" "plan" {
  for_each = toset(local.plan_roles)
  project  = var.project_id
  role     = each.value
  member   = "serviceAccount:${google_service_account.plan.email}"
}

# Plan takes the state lock, so it needs object write on the state bucket — nothing else.
resource "google_storage_bucket_iam_member" "plan_state" {
  bucket = "${var.project_id}-tfstate"
  role   = "roles/storage.objectUser"
  member = "serviceAccount:${google_service_account.plan.email}"
}

# Read-only, so any workflow in this repository may use it (fork PRs get no OIDC token).
resource "google_service_account_iam_member" "plan_wif" {
  service_account_id = google_service_account.plan.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${local.pool}/attribute.repository/${var.github_repo}"
}

output "functions_sa" { value = google_service_account.functions.email }
output "apphosting_sa" { value = google_service_account.apphosting.email }
output "deploy_sa" { value = google_service_account.deploy.email }
output "terraform_sa" { value = google_service_account.terraform.email }
output "plan_sa" { value = google_service_account.plan.email }
output "wif_provider" { value = google_iam_workload_identity_pool_provider.github.name }

# ── Service-agent bindings for event-triggered functions ────────────
# A project's first functions deploy grants these itself — which needs project IAM admin.
# Declaring them here means CI's github-deploy never needs that: the CLI finds them present
# and skips its own setIamPolicy (firebase-tools checkIam.ensureServiceAgentRoles).
data "google_project" "this" {
  project_id = var.project_id
}

# Google creates these agents lazily; asking for them makes sure they exist before binding.
resource "google_project_service_identity" "pubsub" {
  provider = google-beta
  project  = var.project_id
  service  = "pubsub.googleapis.com"
}

data "google_storage_project_service_account" "gcs" {
  project = var.project_id
}

locals {
  compute_default_sa = "${data.google_project.this.number}-compute@developer.gserviceaccount.com"
  service_agent_bindings = {
    "gcs-pubsub-publisher"   = { role = "roles/pubsub.publisher", member = data.google_storage_project_service_account.gcs.member }
    "pubsub-token-creator"   = { role = "roles/iam.serviceAccountTokenCreator", member = google_project_service_identity.pubsub.member }
    "compute-run-invoker"    = { role = "roles/run.invoker", member = "serviceAccount:${local.compute_default_sa}" }
    "compute-event-receiver" = { role = "roles/eventarc.eventReceiver", member = "serviceAccount:${local.compute_default_sa}" }
  }
}

resource "google_project_iam_member" "service_agents" {
  for_each = local.service_agent_bindings
  project  = var.project_id
  role     = each.value.role
  member   = each.value.member
}

# Keyless signed upload URLs: the runtime may sign only as itself.
resource "google_service_account_iam_member" "functions_sign_blob" {
  service_account_id = google_service_account.functions.name
  role               = "roles/iam.serviceAccountTokenCreator"
  member             = "serviceAccount:${google_service_account.functions.email}"
}

# Session cookies require this Auth permission, not Firestore write access.
resource "google_project_iam_custom_role" "apphosting_auth" {
  project     = var.project_id
  role_id     = "apphostingSessionAuth"
  title       = "App Hosting session authentication"
  permissions = ["firebaseauth.users.createSession", "firebaseauth.users.get"]
}

resource "google_project_iam_member" "apphosting_auth" {
  project = var.project_id
  role    = google_project_iam_custom_role.apphosting_auth.name
  member  = "serviceAccount:${google_service_account.apphosting.email}"
}
