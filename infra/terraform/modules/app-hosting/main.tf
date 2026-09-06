# Firebase App Hosting backend for the Next.js app.
#
# Stub until Phase 6. The GitHub connection requires a one-time OAuth handshake in the
# console that Terraform cannot perform — see docs/plan/04-infrastructure.md.

variable "project_id" { type = string }
variable "region" {
  type    = string
  default = "asia-south1"
}
variable "service_account" { type = string }

output "note" {
  value = "Filled in Phase 6, after the GitHub connection is authorised in the console."
}
