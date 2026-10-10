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
    path         = "/api/v1/system/health"
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

# A Monitoring alert condition can't filter on raw log fields like `severity` —
# it needs a metric. This log-based metric counts ERROR-severity Cloud Run log
# entries, and the alert policy below threshold-checks that metric.
resource "google_logging_metric" "function_errors" {
  project = var.project_id
  name    = "function-error-count"
  filter  = "resource.type=\"cloud_run_revision\" AND severity=\"ERROR\""

  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
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
      filter          = "resource.type = \"cloud_run_revision\" AND metric.type = \"logging.googleapis.com/user/${google_logging_metric.function_errors.name}\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 5

      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_SUM"
      }
    }
  }

  notification_channels = [google_monitoring_notification_channel.email.id]
}

resource "google_monitoring_alert_policy" "uptime" {
  count        = var.health_url == "" ? 0 : 1
  project      = var.project_id
  display_name = "Public API health unavailable"
  combiner     = "OR"
  conditions {
    display_name = "Health check failing for five minutes"
    condition_threshold {
      filter          = "metric.type = \"monitoring.googleapis.com/uptime_check/check_passed\" AND resource.type = \"uptime_url\" AND metric.label.check_id = \"${google_monitoring_uptime_check_config.health[0].uptime_check_id}\""
      comparison      = "COMPARISON_GT"
      threshold_value = 1
      duration        = "300s"
      aggregations {
        alignment_period     = "60s"
        per_series_aligner   = "ALIGN_NEXT_OLDER"
        cross_series_reducer = "REDUCE_COUNT_FALSE"
        group_by_fields      = ["resource.label.host"]
      }
    }
  }
  notification_channels = [google_monitoring_notification_channel.email.id]
}
