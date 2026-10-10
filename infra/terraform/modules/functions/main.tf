# Per-domain function configuration — ADR 0011.
#
# The functions themselves are deployed by the Firebase CLI
# (`firebase deploy --only functions`), which is what compiles the Python and wires the
# triggers. This module owns the surrounding configuration Terraform is better at:
# IAM and public/event invoker bindings. Runtime limits and secret bindings are
# owned by the Python Firebase decorators, not this Terraform domain map.

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

variable "domains" {
  description = "One entry per domain. Limits are per domain, not shared — that is the point of the split."
  type = map(object({
    memory        = string
    max_instances = number
    public        = bool
  }))
  default = {
    api_system         = { memory = "256Mi", max_instances = 3, public = true }
    api_contact        = { memory = "256Mi", max_instances = 3, public = true }
    api_projects       = { memory = "256Mi", max_instances = 3, public = true }
    api_skills         = { memory = "256Mi", max_instances = 3, public = true }
    api_experience     = { memory = "256Mi", max_instances = 3, public = true }
    api_education      = { memory = "256Mi", max_instances = 3, public = true }
    api_certifications = { memory = "256Mi", max_instances = 3, public = true }
    api_posts          = { memory = "256Mi", max_instances = 3, public = true }
    api_profile        = { memory = "256Mi", max_instances = 3, public = true }
    api_settings       = { memory = "256Mi", max_instances = 3, public = true }
    api_media          = { memory = "1Gi", max_instances = 2, public = true }
    api_messages       = { memory = "256Mi", max_instances = 3, public = true }
  }
  # public = true here means "reachable" at the Cloud Run IAM layer, not "unauthenticated" —
  # every admin route still gates on Depends(require_admin) inside the app. media, in
  # particular, needs public=true even though almost every route it holds is admin-only,
  # because signed-upload URLs alone don't help if the function itself can't be reached.
}

# Public endpoints (contact, health) need unauthenticated invocation.
# Admin endpoints do their own auth in-process, but still need to be reachable.
#
# 2nd-gen Cloud Functions deploy as Cloud Run v2 services, not v1 — the v1 IAM
# resource (google_cloud_run_service_iam_member) 404s against them even though the
# service genuinely exists, because it's querying the wrong API generation.
resource "google_cloud_run_v2_service_iam_member" "public_invoker" {
  for_each = var.services_deployed ? { for k, v in var.domains : k => v if v.public } : {}

  project  = var.project_id
  location = var.region
  # Cloud Run service names must be DNS-safe — Firebase deploys function id
  # "api_system" as Cloud Run service "api-system" (underscore -> hyphen).
  # Confirmed against the real deploy: `gcloud run services list` only knows the
  # hyphenated form, and the underscored name 404s even though the service exists.
  name   = replace(each.key, "_", "-")
  role   = "roles/run.invoker"
  member = "allUsers"
}

output "configured_domains" { value = keys(var.domains) }

# Eventarc delivers authenticated events as the configured runtime identity.
resource "google_cloud_run_v2_service_iam_member" "event_invoker" {
  for_each = var.services_deployed ? toset(["on-contact-created", "on-media-uploaded"]) : toset([])
  project  = var.project_id
  location = var.region
  name     = each.value
  role     = "roles/run.invoker"
  member   = "serviceAccount:functions-runtime@${var.project_id}.iam.gserviceaccount.com"
}
