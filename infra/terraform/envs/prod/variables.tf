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

variable "functions_deployed" {
  description = <<-EOT
    False until the first `firebase deploy --only functions` has run. Flip to true
    (terraform.tfvars) for the follow-up apply that wires the Cloud Run invoker
    bindings — see modules/functions/main.tf.
  EOT
  type        = bool
  default     = false
}

variable "apphosting_github_connection_id" {
  description = <<-EOT
    Set only after the App Hosting GitHub connection is authorised in the Firebase
    Console (Part E of docs/plan/09-deploy-cicd-implementation.md). Null keeps the
    app-hosting module a no-op until then.
  EOT
  type        = string
  default     = null
}
