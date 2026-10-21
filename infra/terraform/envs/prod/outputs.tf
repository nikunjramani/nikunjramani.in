output "functions_service_account" { value = module.iam.functions_sa }
output "apphosting_service_account" { value = module.iam.apphosting_sa }
output "deploy_service_account" { value = module.iam.deploy_sa }
output "terraform_service_account" { value = module.iam.terraform_sa }
output "plan_service_account" { value = module.iam.plan_sa }

output "wif_provider" {
  description = "Pass to google-github-actions/auth as workload_identity_provider."
  value       = module.iam.wif_provider
}

output "media_bucket" { value = module.storage.media_bucket }
output "backups_bucket" { value = module.storage.backups_bucket }

output "apphosting_backend_note" { value = module.app-hosting.note }
output "api_url" { value = module.api.service_url }

output "apphosting_uri" { value = module.app-hosting.uri }
output "domain_status" { value = module.app-hosting.domain_status }

output "recaptcha_site_key" { value = module.app-check.site_key }
