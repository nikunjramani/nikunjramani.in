# Least-privilege service accounts. Each identity gets exactly what it needs and nothing more.

variable "project_id" { type = string }
variable "github_repo" {
  type        = string
  description = "owner/repo — scopes the WIF binding so only this repository can deploy."
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
  ]

  # App Hosting renders pages, so it reads content. It must never write.
  apphosting_roles = [
    "roles/datastore.viewer",
    "roles/secretmanager.secretAccessor",
    "roles/logging.logWriter",
  ]

  deploy_roles = [
    "roles/cloudfunctions.admin",
    "roles/run.admin",
    "roles/firebase.admin",
    "roles/iam.serviceAccountUser",
    "roles/storage.admin",
  ]
}

resource "google_project_iam_member" "functions" {
  for_each = toset(local.functions_roles)
  project  = var.project_id
  role     = each.value
  member   = "serviceAccount:${google_service_account.functions.email}"
}

# ── App Hosting (Next.js SSR) — read-only ───────────────────────────
resource "google_service_account" "apphosting" {
  project      = var.project_id
  account_id   = "apphosting-runtime"
  display_name = "App Hosting runtime (read-only)"
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

  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.repository" = "assertion.repository"
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

resource "google_service_account_iam_member" "deploy_wif" {
  service_account_id = google_service_account.deploy.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github.name}/attribute.repository/${var.github_repo}"
}

output "functions_sa" { value = google_service_account.functions.email }
output "apphosting_sa" { value = google_service_account.apphosting.email }
output "deploy_sa" { value = google_service_account.deploy.email }
output "wif_provider" { value = google_iam_workload_identity_pool_provider.github.name }
