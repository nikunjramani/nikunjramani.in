# Staging state lives in the staging project's own bucket, so no staging identity ever needs
# access to anything in prod (ADR 0018). Created once by infra/scripts/bootstrap.sh with
# PROJECT_ID=nikunjramani-in-staging.

terraform {
  required_version = ">= 1.9"

  backend "gcs" {
    bucket = "nikunjramani-in-staging-tfstate"
    prefix = "envs/staging"
  }

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 6.0"
    }
  }
}
