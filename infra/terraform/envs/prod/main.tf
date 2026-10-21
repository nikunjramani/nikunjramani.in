locals {
  # Browser origins the site is served from — the custom domains plus App Hosting's own
  # URL, which keeps working before (and independently of) DNS.
  site_origins = [
    "https://nikunjramani.in",
    "https://www.nikunjramani.in",
    "https://${var.apphosting_backend_host}",
    "http://localhost:3000",
  ]
}

provider "google" {
  project = var.project_id
  region  = var.region

  # google_billing_budget is scoped to the billing account, not a project, so the
  # provider has no project argument on that resource to infer quota from. Without
  # this override it falls back to the ADC OAuth client's own project (not ours) and
  # billingbudgets.googleapis.com calls fail with a misleading SERVICE_DISABLED error.
  user_project_override = true
  billing_project       = var.project_id
}

provider "google-beta" {
  project = var.project_id
  region  = var.region

  user_project_override = true
  billing_project       = var.project_id
}

module "project" {
  source          = "../../modules/project"
  project_id      = var.project_id
  billing_account = var.billing_account
  budget_amount   = var.budget_amount
}

module "iam" {
  source             = "../../modules/iam"
  project_id         = var.project_id
  github_repo        = var.github_repo
  deploy_environment = "production"
  infra_environment  = "production-infra"

  depends_on = [module.project]
}

module "firestore" {
  source     = "../../modules/firestore"
  project_id = var.project_id
  location   = var.region

  depends_on = [module.project]
}

module "storage" {
  source       = "../../modules/storage"
  project_id   = var.project_id
  cors_origins = local.site_origins

  depends_on = [module.project]
}

module "secrets" {
  source     = "../../modules/secrets"
  project_id = var.project_id

  # Only the API reads secrets. App Hosting needs none since the revalidation webhook was
  # removed (ADR 0015).
  accessor_service_accounts = [module.iam.functions_sa]

  depends_on = [module.project]
}

module "monitoring" {
  source      = "../../modules/monitoring"
  project_id  = var.project_id
  alert_email = var.alert_email
  health_url  = var.health_host

  depends_on = [module.project]
}

module "api" {
  source          = "../../modules/api"
  project_id      = var.project_id
  region          = var.region
  service_account = module.iam.functions_sa
  media_bucket    = module.storage.media_bucket

  depends_on = [module.project, module.iam]
}

module "app-hosting" {
  source               = "../../modules/app-hosting"
  project_id           = var.project_id
  region               = var.apphosting_region
  service_account      = module.iam.apphosting_sa
  github_connection_id = var.apphosting_github_connection_id
  custom_domain        = "nikunjramani.in"

  depends_on = [module.project, module.iam]
}

module "app-check" {
  source     = "../../modules/app-check"
  project_id = var.project_id
  web_app_id = module.app-hosting.web_app_id
  allowed_domains = [
    "nikunjramani.in",
    "www.nikunjramani.in",
    var.apphosting_backend_host,
  ]

  depends_on = [module.project]
}
