output "api_url" {
  description = "Base URL of the HTTP API (frontend apiBaseUrl)."
  value       = module.api.api_url
}

output "kb_bucket" {
  value = module.storage.kb_bucket
}

output "repos_table" {
  value = module.storage.repos_table
}

output "results_table" {
  value = module.storage.results_table
}

output "ingest_ecr_repository_url" {
  value = module.compute.ingest_ecr_repository_url
}

output "analyze_ecr_repository_url" {
  value = module.compute.analyze_ecr_repository_url
}

output "frontend_url" {
  description = "URL to reach the SPA (null when deploy_frontend = false)."
  value       = var.deploy_frontend ? module.frontend[0].url : null
}

output "frontend_public_dns" {
  value = var.deploy_frontend ? module.frontend[0].public_dns : null
}
