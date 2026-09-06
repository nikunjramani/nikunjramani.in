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
  default = 500
}
