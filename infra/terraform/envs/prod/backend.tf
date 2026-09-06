# Remote state in GCS, with versioning on the bucket.
# The bucket is created by infra/scripts/bootstrap.sh — it must exist before `terraform init`,
# which is why Terraform cannot manage it (chicken-and-egg).

terraform {
  required_version = ">= 1.9"

  backend "gcs" {
    bucket = "nikunjramani-in-tfstate"
    prefix = "envs/prod"
  }

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
    # Firebase resources live in the beta provider. Expected, not a workaround.
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 6.0"
    }
  }
}
