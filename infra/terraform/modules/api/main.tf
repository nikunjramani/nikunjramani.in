# The `api` Cloud Run service's event and job wiring (ADR 0023).
#
# The service itself — image, env, secrets, sizing, public invoke — is deployed by CI
# (`make deploy-api`, .github/actions/cloud-run-deploy), the way the Firebase CLI used to own
# its functions: a PR preview can create it in staging before anything here has been applied.
# This module adds what points *at* it, so it needs the service to exist — deploy.yml runs the
# code deploy before Terraform for exactly that reason.
#
# Every call below is signed as the runtime account the service runs as, for the service's
# own URL; kernel/events.py rejects anything else on /internal/*.

variable "project_id" { type = string }
variable "region" {
  type    = string
  default = "asia-south1"
}
variable "service_account" {
  description = "Runtime identity: the service runs as it, and Eventarc and Scheduler sign as it."
  type        = string
}
variable "media_bucket" {
  description = "Bucket whose object.finalized events start image processing."
  type        = string
}

data "google_project" "this" {
  project_id = var.project_id
}

locals {
  service = "api"
  # Cloud Run's deterministic URL — the same value as SERVICE_URL in backend/deploy/<project>.yaml.
  service_url = "https://${local.service}-${data.google_project.this.number}.${var.region}.run.app"
}

# Storage event → image processing. Eventarc's Storage triggers live in the bucket's region.
resource "google_eventarc_trigger" "media_uploaded" {
  project         = var.project_id
  name            = "media-uploaded"
  location        = var.region
  service_account = var.service_account

  matching_criteria {
    attribute = "type"
    value     = "google.cloud.storage.object.v1.finalized"
  }
  matching_criteria {
    attribute = "bucket"
    value     = var.media_bucket
  }

  destination {
    cloud_run_service {
      service = local.service
      region  = var.region
      path    = "/internal/events/media-uploaded"
    }
  }
}

# Firestore event → owner email. Must be in the database's location; payload is protobuf.
resource "google_eventarc_trigger" "contact_created" {
  project                 = var.project_id
  name                    = "contact-created"
  location                = var.region
  service_account         = var.service_account
  event_data_content_type = "application/protobuf"

  matching_criteria {
    attribute = "type"
    value     = "google.cloud.firestore.document.v1.created"
  }
  matching_criteria {
    attribute = "database"
    value     = "(default)"
  }
  matching_criteria {
    attribute = "document"
    value     = "contact_messages/{message}"
    operator  = "match-path-pattern"
  }

  destination {
    cloud_run_service {
      service = local.service
      region  = var.region
      path    = "/internal/events/contact-created"
    }
  }
}

# Daily backup (ops/backup). The export takes well under a minute today.
resource "google_cloud_scheduler_job" "backup" {
  project          = var.project_id
  name             = "nightly-backup"
  region           = var.region
  schedule         = "0 2 * * *"
  time_zone        = "Asia/Kolkata"
  attempt_deadline = "600s"

  http_target {
    http_method = "POST"
    uri         = "${local.service_url}/internal/jobs/backup"
    oidc_token {
      service_account_email = var.service_account
      audience              = local.service_url
    }
  }
}

output "service_url" { value = local.service_url }
