output "functions_service_account" { value = module.iam.functions_sa }
output "apphosting_service_account" { value = module.iam.apphosting_sa }
output "deploy_service_account" { value = module.iam.deploy_sa }

output "wif_provider" {
  description = "Pass to google-github-actions/auth as workload_identity_provider."
  value       = module.iam.wif_provider
}

output "media_bucket" { value = module.storage.media_bucket }
output "backups_bucket" { value = module.storage.backups_bucket }
