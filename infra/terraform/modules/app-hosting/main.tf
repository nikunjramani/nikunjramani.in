# Firebase App Hosting backend. Local source deployments do not require GitHub.
# A Developer Connect repository can be attached later for automatic rollouts.

variable "project_id" { type = string }
variable "region" {
  type    = string
  default = "asia-southeast1"
}
variable "service_account" { type = string }

variable "github_connection_id" {
  description = <<-EOT
    Full resource name of the Developer Connect gitRepositoryLink created by the
    console "connect repository" step, in the form:
    projects/{project}/locations/{location}/connections/{connection}/gitRepositoryLinks/{link}
    Optional: leave null for Firebase CLI local-source deployments.
  EOT
  type        = string
  default     = null
}

variable "root_dir" {
  description = "Repo-relative path to the Next.js app Terraform should build from."
  type        = string
  default     = "frontend"
}

variable "custom_domain" {
  description = "Apex domain to serve, with www redirecting to it. Null serves only the hosted.app URL."
  type        = string
  default     = null
}

variable "environment" {
  description = "App Hosting environment name; selects frontend/apphosting.<environment>.yaml."
  type        = string
  default     = null
}

# One Web App registration per Firebase project — this is what gives App Hosting an
# app_id to attach to. Pure API call, nothing console-only about it.
resource "google_firebase_web_app" "site" {
  provider     = google-beta
  project      = var.project_id
  display_name = "nikunjramani.in"
}

resource "google_firebase_app_hosting_backend" "site" {
  provider = google-beta

  project          = var.project_id
  location         = var.region
  backend_id       = "nikunjramani-in"
  app_id           = google_firebase_web_app.site.app_id
  service_account  = var.service_account
  serving_locality = "GLOBAL_ACCESS" # REGIONAL_STRICT is rejected by the live API.
  environment      = var.environment

  dynamic "codebase" {
    for_each = var.github_connection_id == null ? [] : [var.github_connection_id]
    content {
      repository     = codebase.value
      root_directory = var.root_dir
    }
  }
}

output "web_app_id" { value = google_firebase_web_app.site.app_id }

output "note" {
  value = var.github_connection_id == null ? "Deploy local source with firebase deploy --only apphosting." : "GitHub repository connected."
}

output "backend_id" {
  value = google_firebase_app_hosting_backend.site.backend_id
}

resource "google_firebase_app_hosting_domain" "apex" {
  count     = var.custom_domain == null ? 0 : 1
  provider  = google-beta
  project   = var.project_id
  location  = var.region
  backend   = google_firebase_app_hosting_backend.site.backend_id
  domain_id = var.custom_domain
}

resource "google_firebase_app_hosting_domain" "www" {
  count     = var.custom_domain == null ? 0 : 1
  provider  = google-beta
  project   = var.project_id
  location  = var.region
  backend   = google_firebase_app_hosting_backend.site.backend_id
  domain_id = "www.${var.custom_domain}"
  serve {
    redirect {
      uri    = "https://${var.custom_domain}"
      status = "301"
    }
  }
}

moved {
  from = google_firebase_app_hosting_domain.apex
  to   = google_firebase_app_hosting_domain.apex[0]
}

moved {
  from = google_firebase_app_hosting_domain.www
  to   = google_firebase_app_hosting_domain.www[0]
}

output "uri" { value = google_firebase_app_hosting_backend.site.uri }
output "domain_status" {
  value = var.custom_domain == null ? null : {
    apex = google_firebase_app_hosting_domain.apex[0].custom_domain_status
    www  = google_firebase_app_hosting_domain.www[0].custom_domain_status
  }
}
