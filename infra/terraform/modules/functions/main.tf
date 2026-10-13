# Per-domain function configuration — ADR 0011.
#
# The functions themselves are deployed by the Firebase CLI
# (`firebase deploy --only functions`), which is what compiles the Python and wires the
# triggers. This module owns the surrounding configuration Terraform is better at:
# IAM and public/event invoker bindings. Runtime limits and secret bindings are
# owned by the Python Firebase decorators, not by this module.

variable "project_id" { type = string }
variable "region" {
  type    = string
  default = "asia-south1"
}

variable "services_deployed" {
  description = <<-EOT
    The IAM invoker binding below targets a Cloud Run service by name, and that
    service doesn't exist until `firebase deploy --only functions` has run at least
    once (2nd-gen Functions deploy as Cloud Run under the hood) — so this stays false
    for the first `terraform apply`, then flips to true for a second apply right
    after the first functions deploy. False keeps this module a no-op instead of
    failing the whole apply on a service that isn't there yet.
  EOT
  type        = bool
  default     = false
}

variable "service_account" {
  description = "Runtime identity Eventarc delivers trigger events as."
  type        = string
}

variable "http_functions" {
  description = <<-EOT
    Every deployed HTTP function. All are reachable at the Cloud Run IAM layer — admin
    routes authenticate in-process with Depends(require_admin), and media needs to be
    reachable for signed-upload URLs to be requested at all. Memory and instance limits
    live in the Python decorators, not here. tests/test_domain_registry.py checks this
    list against backend/functions/main.py.
  EOT
  type        = set(string)
  default = [
    "api_system",
    "api_contact",
    "api_projects",
    "api_skills",
    "api_experience",
    "api_education",
    "api_certifications",
    "api_posts",
    "api_profile",
    "api_settings",
    "api_media",
    "api_messages",
  ]
}

# Public endpoints (contact, health) need unauthenticated invocation.
# Admin endpoints do their own auth in-process, but still need to be reachable.
#
# 2nd-gen Cloud Functions deploy as Cloud Run v2 services, not v1 — the v1 IAM
# resource (google_cloud_run_service_iam_member) 404s against them even though the
# service genuinely exists, because it's querying the wrong API generation.
resource "google_cloud_run_v2_service_iam_member" "public_invoker" {
  for_each = var.services_deployed ? var.http_functions : toset([])

  project  = var.project_id
  location = var.region
  # Cloud Run service names must be DNS-safe — Firebase deploys function id
  # "api_system" as Cloud Run service "api-system" (underscore -> hyphen).
  name   = replace(each.key, "_", "-")
  role   = "roles/run.invoker"
  member = "allUsers"
}

output "configured_domains" { value = sort(tolist(var.http_functions)) }

# Eventarc delivers authenticated events as the configured runtime identity.
resource "google_cloud_run_v2_service_iam_member" "event_invoker" {
  for_each = var.services_deployed ? toset(["on-contact-created", "on-media-uploaded"]) : toset([])
  project  = var.project_id
  location = var.region
  name     = each.value
  role     = "roles/run.invoker"
  member   = "serviceAccount:${var.service_account}"
}
