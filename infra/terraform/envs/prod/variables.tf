variable "project_id" {
  type    = string
  default = "nikunjramani-in"
}

variable "billing_account" {
  type        = string
  description = "Billing account id. Set in terraform.tfvars — never committed."
}

variable "region" {
  type    = string
  default = "asia-south1"
}

variable "alert_email" {
  type        = string
  description = "Where budget and error alerts go. Set in terraform.tfvars."
}

variable "github_repo" {
  type    = string
  default = "nikunjramani/nikunjramani.in"
}

variable "budget_amount" {
  type    = number
  default = 100
}

variable "apphosting_github_connection_id" {
  description = <<-EOT
    Set only after the App Hosting GitHub connection is authorised in the Firebase
    Console. Null uses local-source deployment without a GitHub connection (ADR 0013).
  EOT
  type        = string
  default     = null
}

variable "apphosting_region" {
  description = <<-EOT
    App Hosting does not support every region Firestore/Functions do — confirmed via
    the real API (`GET v1beta/.../locations`), asia-south1 (Mumbai, used everywhere
    else) 403s with "Location ... is not found or access is unauthorized". The
    supported set is asia-east1, asia-southeast1, europe-west4, us-central1, us-east4,
    us-east5 — asia-southeast1 (Singapore) is the closest to India.
  EOT
  type        = string
  default     = "asia-southeast1"
}


variable "apphosting_backend_host" {
  description = "App Hosting's default hostname for the backend (no scheme)."
  type        = string
  default     = "nikunjramani-in--nikunjramani-in.asia-southeast1.hosted.app"
}

variable "health_host" {
  description = "Public hostname for HTTPS health monitoring."
  type        = string
  default     = "nikunjramani-in--nikunjramani-in.asia-southeast1.hosted.app"
}
