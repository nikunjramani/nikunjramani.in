variable "project_id" { type = string }
variable "location" {
  type    = string
  default = "ASIA-SOUTH1"
}
variable "cors_origins" {
  description = "Origins allowed to PUT to signed upload URLs from the browser."
  type        = list(string)
}

# Media: public assets served to the site.
resource "google_storage_bucket" "media" {
  project                     = var.project_id
  name                        = "${var.project_id}-media"
  location                    = var.location
  uniform_bucket_level_access = true
  force_destroy               = false

  cors {
    origin          = var.cors_origins
    method          = ["GET", "HEAD", "PUT", "POST"]
    response_header = ["Content-Type", "Authorization"]
    max_age_seconds = 3600
  }

  # Versioning guards against an accidental overwrite; deleted or replaced media is
  # recoverable for 30 days, then actually gone (otherwise a delete never frees anything).
  versioning { enabled = true }

  lifecycle_rule {
    condition { days_since_noncurrent_time = 30 }
    action { type = "Delete" }
  }
}

# Backups: nightly Firestore exports, aged out so growth stays bounded.
resource "google_storage_bucket" "backups" {
  project                     = var.project_id
  name                        = "${var.project_id}-backups"
  location                    = var.location
  uniform_bucket_level_access = true

  lifecycle_rule {
    condition { age = 30 }
    action { type = "Delete" }
  }
}

output "media_bucket" { value = google_storage_bucket.media.name }
output "backups_bucket" { value = google_storage_bucket.backups.name }

# A managed folder scopes public reads to public/ without exposing private objects.
resource "google_storage_managed_folder" "public_media" {
  bucket = google_storage_bucket.media.name
  name   = "public/"
}

resource "google_storage_managed_folder_iam_member" "public_media" {
  bucket         = google_storage_bucket.media.name
  managed_folder = google_storage_managed_folder.public_media.name
  role           = "roles/storage.objectViewer"
  member         = "allUsers"
}
