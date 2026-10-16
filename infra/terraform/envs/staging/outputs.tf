output "functions_service_account" { value = module.iam.functions_sa }
output "apphosting_service_account" { value = module.iam.apphosting_sa }
output "deploy_service_account" { value = module.iam.deploy_sa }
output "terraform_service_account" { value = module.iam.terraform_sa }
output "plan_service_account" { value = module.iam.plan_sa }
output "wif_provider" { value = module.iam.wif_provider }

output "media_bucket" { value = module.storage.media_bucket }
output "web_app_id" { value = module.app-hosting.web_app_id }
output "apphosting_uri" { value = module.app-hosting.uri }

output "recaptcha_site_key" { value = module.app-check.site_key }
