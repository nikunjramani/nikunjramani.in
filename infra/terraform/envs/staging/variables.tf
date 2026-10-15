variable "project_id" {
  type    = string
  default = "nikunjramani-in-staging"
}

variable "billing_account" {
  type        = string
  description = "Same billing account as prod. Set in terraform.tfvars — never committed."
}

variable "region" {
  type    = string
  default = "asia-south1"
}

variable "github_repo" {
  type    = string
  default = "nikunjramani/nikunjramani.in"
}

variable "budget_amount" {
  type    = number
  default = 50
}

variable "functions_deployed" {
  description = "False until the first functions deploy to staging has run; see envs/prod."
  type        = bool
  default     = false
}

variable "apphosting_region" {
  type    = string
  default = "asia-southeast1"
}

variable "apphosting_backend_host" {
  description = "App Hosting's default hostname for the staging backend (no scheme)."
  type        = string
  default     = "nikunjramani-in--nikunjramani-in-staging.asia-southeast1.hosted.app"
}
