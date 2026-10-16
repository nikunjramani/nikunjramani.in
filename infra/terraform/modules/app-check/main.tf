# Firebase App Check for the public contact form (ADR 0020): a score-based (invisible)
# reCAPTCHA Enterprise key, registered as the web app's App Check provider. The contact
# function verifies the resulting tokens itself — no secret anywhere.

variable "project_id" { type = string }

variable "web_app_id" {
  description = "The Firebase web app the frontend initializes (module.app-hosting.web_app_id)."
  type        = string
}

variable "allowed_domains" {
  description = "Hostnames the reCAPTCHA key accepts — the site's own domains, no scheme."
  type        = list(string)
}

resource "google_recaptcha_enterprise_key" "web" {
  project      = var.project_id
  display_name = "Contact form (App Check)"

  web_settings {
    integration_type  = "SCORE" # invisible — no challenge shown to visitors
    allowed_domains   = var.allowed_domains
    allow_amp_traffic = false
  }
}

resource "google_firebase_app_check_recaptcha_enterprise_config" "web" {
  project   = var.project_id
  app_id    = var.web_app_id
  site_key  = google_recaptcha_enterprise_key.web.name
  token_ttl = "3600s"
}

# Public by design — goes in apphosting*.yaml as NEXT_PUBLIC_RECAPTCHA_SITE_KEY.
output "site_key" { value = google_recaptcha_enterprise_key.web.name }
