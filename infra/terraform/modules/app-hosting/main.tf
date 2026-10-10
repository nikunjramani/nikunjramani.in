# Firebase App Hosting backend for the Next.js app.
#
# The GitHub connection itself is a one-time OAuth/Developer-Connect handshake done in
# the Firebase Console — Terraform cannot perform it (see docs/plan/04-infrastructure.md).
# This module creates the Firebase Web App registration unconditionally (that part is
# scriptable), but the actual backend resource only once the connection exists —
# github_connection_id is null until then, so `count` keeps that half a no-op in the
# meantime rather than failing the whole apply.

variable "project_id" { type = string }
variable "region" {
  type    = string
  default = "asia-south1"
}
variable "service_account" { type = string }

variable "github_connection_id" {
  description = <<-EOT
    Full resource name of the Developer Connect gitRepositoryLink created by the
    console "connect repository" step, in the form:
    projects/{project}/locations/{location}/connections/{connection}/gitRepositoryLinks/{link}
    Null until that console step is done — the backend resource creates nothing until
    it's set (Part E of docs/plan/09-deploy-cicd-implementation.md).
  EOT
  type        = string
  default     = null
}

variable "root_dir" {
  description = "Repo-relative path to the Next.js app Terraform should build from."
  type        = string
  default     = "frontend"
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
  count    = var.github_connection_id == null ? 0 : 1

  project          = var.project_id
  location         = var.region
  backend_id       = "nikunjramani-in"
  app_id           = google_firebase_web_app.site.app_id
  service_account  = var.service_account
  serving_locality = "REGIONAL_STRICT" # keep everything in asia-south1, same as Firestore

  codebase {
    repository     = var.github_connection_id
    root_directory = var.root_dir
  }
}

output "web_app_id" { value = google_firebase_web_app.site.app_id }

output "note" {
  value = var.github_connection_id == null ? "Web app registered. Backend waiting on the console GitHub connection — see Part E of docs/plan/09-deploy-cicd-implementation.md." : "Backend created."
}

output "backend_id" {
  value = length(google_firebase_app_hosting_backend.site) > 0 ? google_firebase_app_hosting_backend.site[0].backend_id : null
}
