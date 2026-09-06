variable "project_id" { type = string }
variable "alert_email" { type = string }
variable "health_url" {
  type    = string
  default = ""
}

resource "google_monitoring_notification_channel" "email" {
  project      = var.project_id
  display_name = "Owner email"
  type         = "email"

  labels = {
    email_address = var.alert_email
  }
}

# You should hear about an outage before a visitor does.
resource "google_monitoring_uptime_check_config" "health" {
  count = var.health_url == "" ? 0 : 1

  project      = var.project_id
  display_name = "API health"
  timeout      = "10s"
  period       = "300s"

  http_check {
    path         = "/health"
    port         = 443
    use_ssl      = true
    validate_ssl = true
  }

  monitored_resource {
    type = "uptime_url"
    labels = {
      project_id = var.project_id
      host       = var.health_url
    }
  }
}

# Catches a bad deploy before the logs are read by accident.
resource "google_monitoring_alert_policy" "error_rate" {
  project      = var.project_id
  display_name = "Function error rate"
  combiner     = "OR"

  conditions {
    display_name = "Errors > 5/min"
    condition_threshold {
      filter          = "resource.type = \"cloud_run_revision\" AND severity = \"ERROR\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 5

      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_COUNT"
      }
    }
  }

  notification_channels = [google_monitoring_notification_channel.email.id]
}
