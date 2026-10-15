variable "project_id" { type = string }
variable "location" {
  type    = string
  default = "asia-south1" # Mumbai. Must match the functions region or every read pays a hop.
}

# NATIVE mode, always. DATASTORE_MODE is irreversible and would sink the project.
resource "google_firestore_database" "default" {
  project     = var.project_id
  name        = "(default)"
  location_id = var.location
  type        = "FIRESTORE_NATIVE"

  delete_protection_state = "DELETE_PROTECTION_ENABLED"

  lifecycle {
    prevent_destroy = true
  }
}

# Data minimisation: contact messages age out after two years.
resource "google_firestore_field" "contact_ttl" {
  project    = var.project_id
  database   = google_firestore_database.default.name
  collection = "contact_messages"
  field      = "expiresAt"

  ttl_config {}
  # Empty = no single-field indexes, matching firestore.indexes.json's fieldOverrides
  # ("indexes": []), which `firebase deploy` applies. Omitted, the two would undo each other.
  index_config {}
}

# Rate-limit windows (shared/core/rate_limit.py) carry an expiresAt; without this policy
# every window document would accumulate forever.
resource "google_firestore_field" "rate_limit_ttl" {
  project    = var.project_id
  database   = google_firestore_database.default.name
  collection = "_rate_limits"
  field      = "expiresAt"

  ttl_config {}
  index_config {} # see contact_ttl
}

output "database_name" { value = google_firestore_database.default.name }
