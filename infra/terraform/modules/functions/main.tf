# Per-subdomain function configuration — ADR 0017.
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
    Every deployed HTTP function — one per backend subdomain, api_<domain>_<subdomain>
    (ADR 0017). All are reachable at the Cloud Run IAM layer; admin routes authenticate
    in-process with AdminClaims. Memory and instance limits live in each subdomain's
    main.py, not here. tests/test_domain_registry.py checks this list against the code.
  EOT
  type        = set(string)
  default = [
    "api_content_profile",
    "api_content_projects",
    "api_content_skills",
    "api_content_experience",
    "api_content_education",
    "api_content_certifications",
    "api_content_posts",
    "api_content_settings",
    "api_identity_admins",
    "api_inbox_contact",
    "api_inbox_messages",
    "api_media_upload",
    "api_media_library",
    "api_ops_health",
    "api_ops_audit",
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
