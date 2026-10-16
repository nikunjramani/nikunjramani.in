# Staging: the same modules as prod, pointed at a separate project (ADR 0018). No custom
# domain, no monitoring (an uptime alert on a scale-to-zero preview is noise), smaller budget.

locals {
  site_origins = [
    "https://${var.apphosting_backend_host}",
    "http://localhost:3000",
  ]
}

provider "google" {
  project = var.project_id
  region  = var.region

  # See envs/prod/main.tf — the billing budget needs an explicit quota project.
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
  deploy_environment = "staging"
  infra_environment  = "staging-infra"

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
  source                    = "../../modules/secrets"
  project_id                = var.project_id
  accessor_service_accounts = [module.iam.functions_sa]

  depends_on = [module.project]
}

module "functions" {
  source            = "../../modules/functions"
  project_id        = var.project_id
  region            = var.region
  services_deployed = var.functions_deployed
  service_account   = module.iam.functions_sa

  depends_on = [module.project, module.iam]
}

module "app-hosting" {
  source          = "../../modules/app-hosting"
  project_id      = var.project_id
  region          = var.apphosting_region
  service_account = module.iam.apphosting_sa
  environment     = "staging"

  depends_on = [module.project, module.iam]
}

module "app-check" {
  source          = "../../modules/app-check"
  project_id      = var.project_id
  web_app_id      = module.app-hosting.web_app_id
  allowed_domains = [var.apphosting_backend_host]

  depends_on = [module.project]
}
