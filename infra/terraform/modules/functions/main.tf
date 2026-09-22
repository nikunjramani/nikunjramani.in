# Per-domain function configuration — ADR 0011.
#
# Stub until Phase 6. The functions themselves are deployed by the Firebase CLI
# (`firebase deploy --only functions`), which is what compiles the Python and wires the
# triggers. This module owns the surrounding configuration Terraform is better at:
# per-domain limits, IAM and public invoker bindings.

variable "project_id" { type = string }
variable "region" {
  type    = string
  default = "asia-south1"
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
  }
  # public = true here means "reachable" at the Cloud Run IAM layer, not "unauthenticated" —
  # every admin route still gates on Depends(require_admin) inside the app. media, in
  # particular, needs public=true even though almost every route it holds is admin-only,
  # because signed-upload URLs alone don't help if the function itself can't be reached.
}

# Public endpoints (contact, health) need unauthenticated invocation.
# Admin endpoints do their own auth in-process, but still need to be reachable.
resource "google_cloud_run_service_iam_member" "public_invoker" {
  for_each = { for k, v in var.domains : k => v if v.public }

  project  = var.project_id
  location = var.region
  service  = each.key
  role     = "roles/run.invoker"
  member   = "allUsers"
}

output "configured_domains" { value = keys(var.domains) }
