provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

module "project" {
  source          = "../../modules/project"
  project_id      = var.project_id
  billing_account = var.billing_account
  budget_amount   = var.budget_amount
}

module "iam" {
  source      = "../../modules/iam"
  project_id  = var.project_id
  github_repo = var.github_repo

  depends_on = [module.project]
}

module "firestore" {
  source     = "../../modules/firestore"
  project_id = var.project_id
  location   = var.region

  depends_on = [module.project]
}

module "storage" {
  source     = "../../modules/storage"
  project_id = var.project_id

  depends_on = [module.project]
}

module "secrets" {
  source     = "../../modules/secrets"
  project_id = var.project_id

  accessor_service_accounts = [
    module.iam.functions_sa,
    module.iam.apphosting_sa,
  ]

  depends_on = [module.project]
}

module "monitoring" {
  source      = "../../modules/monitoring"
  project_id  = var.project_id
  alert_email = var.alert_email

  depends_on = [module.project]
}
