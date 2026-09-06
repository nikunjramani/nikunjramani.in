# Secret *containers* are created here. Their values are added out-of-band with
# `gcloud secrets versions add`, so no secret ever passes through Terraform state.

variable "project_id" { type = string }
variable "accessor_service_accounts" {
  type    = list(string)
  default = []
}

locals {
  secrets = [
    "RESEND_API_KEY",
    "CONTACT_EMAIL_TO",
    "TURNSTILE_SECRET_KEY",
    "REVALIDATE_TOKEN",
  ]
}

resource "google_secret_manager_secret" "this" {
  for_each  = toset(local.secrets)
  project   = var.project_id
  secret_id = each.value

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_iam_member" "accessors" {
  for_each = {
    for pair in setproduct(local.secrets, var.accessor_service_accounts) :
    "${pair[0]}:${pair[1]}" => { secret = pair[0], sa = pair[1] }
  }

  project   = var.project_id
  secret_id = google_secret_manager_secret.this[each.value.secret].secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${each.value.sa}"
}

output "secret_ids" { value = [for s in google_secret_manager_secret.this : s.secret_id] }
