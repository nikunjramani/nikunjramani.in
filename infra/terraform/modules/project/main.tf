# Enables the APIs everything else depends on, and puts a spending guardrail in place
# before anything can spend.

variable "project_id" { type = string }
variable "billing_account" { type = string }
variable "budget_amount" {
  type        = number
  description = "Monthly budget in INR. Alerts only — this does not cap spend."
  default     = 500
}

locals {
  services = [
    "firebase.googleapis.com",
    "firestore.googleapis.com",
    "firebasestorage.googleapis.com",
    "firebaserules.googleapis.com",
    "identitytoolkit.googleapis.com",
    "cloudfunctions.googleapis.com",
    "run.googleapis.com",
    "cloudbuild.googleapis.com",
    "artifactregistry.googleapis.com",
    "eventarc.googleapis.com",
    "cloudscheduler.googleapis.com",
    "secretmanager.googleapis.com",
    "monitoring.googleapis.com",
    "logging.googleapis.com",
    "billingbudgets.googleapis.com",
    "iamcredentials.googleapis.com",
    "firebaseapphosting.googleapis.com",
    # `firebase deploy` checks these are on and would otherwise try to enable them itself,
    # which CI's github-deploy can't (and shouldn't) do.
    "developerconnect.googleapis.com", # App Hosting
    "iam.googleapis.com",              # App Hosting
    "pubsub.googleapis.com",           # event-triggered functions
    "firebaseappcheck.googleapis.com", # contact form abuse protection (ADR 0020)
    "recaptchaenterprise.googleapis.com",
  ]
}

resource "google_project_service" "enabled" {
  for_each = toset(local.services)

  project = var.project_id
  service = each.value

  # Leave APIs on if the module is removed — disabling them can orphan live resources.
  disable_on_destroy = false
}

# A budget alert is a smoke alarm, not a sprinkler: it notifies, it does not cap.
# The real spend ceiling is max_instances on each function.
data "google_project" "current" {
  project_id = var.project_id
}

resource "google_billing_budget" "monthly" {
  billing_account = var.billing_account
  display_name    = "${var.project_id} monthly budget"

  budget_filter {
    projects = ["projects/${data.google_project.current.number}"]
  }

  amount {
    specified_amount {
      currency_code = "INR"
      units         = tostring(var.budget_amount)
    }
  }

  dynamic "threshold_rules" {
    for_each = [0.5, 0.9, 1.0]
    content {
      threshold_percent = threshold_rules.value
    }
  }
}

output "services_enabled" { value = [for s in google_project_service.enabled : s.service] }
