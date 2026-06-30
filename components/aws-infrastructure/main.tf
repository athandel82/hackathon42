# Root configuration (ARCHITECTURE.md §6) — provider, backend, module wiring.
# Apply order is acyclic: storage -> compute -> api -> frontend.
# `api` does not depend on `frontend` (CORS `*`, §S1), breaking the cycle.

terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.0"
    }
  }

  # Partial config — values supplied via envs/dev/backend.hcl:
  #   terraform init -backend-config=envs/dev/backend.hcl
  backend "s3" {}
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project   = var.project
      Env       = var.env
      ManagedBy = "terraform"
    }
  }
}

locals {
  name_prefix = "${var.project}-${var.env}"

  # Build contexts live in sibling component folders. This root module sits at
  # components/aws-infrastructure, so ../<component> resolves correctly.
  ingest_context  = abspath("${path.module}/../ingestion-agent")
  analyze_context = abspath("${path.module}/../analyze-agent")
}

module "storage" {
  source      = "./modules/storage"
  name_prefix = local.name_prefix
}

module "compute" {
  source      = "./modules/compute"
  name_prefix = local.name_prefix
  region      = var.region

  ingest_context  = local.ingest_context
  analyze_context = local.analyze_context

  kb_bucket         = module.storage.kb_bucket
  kb_bucket_arn     = module.storage.kb_bucket_arn
  repos_table       = module.storage.repos_table
  repos_table_arn   = module.storage.repos_table_arn
  results_table     = module.storage.results_table
  results_table_arn = module.storage.results_table_arn

  bedrock_model_id        = var.bedrock_model_id
  ingest_model_id         = var.ingest_model_id
  analyze_model_id        = var.analyze_model_id
  bedrock_region          = var.bedrock_region
  github_token_secret_arn = var.github_token_secret_arn
  log_level               = var.log_level

  ingest_reserved_concurrency  = var.ingest_reserved_concurrency
  analyze_reserved_concurrency = var.analyze_reserved_concurrency
}

module "api" {
  source      = "./modules/api"
  name_prefix = local.name_prefix

  ingest_invoke_arn     = module.compute.ingest_invoke_arn
  ingest_function_name  = module.compute.ingest_function_name
  analyze_invoke_arn    = module.compute.analyze_invoke_arn
  analyze_function_name = module.compute.analyze_function_name
}

module "frontend" {
  source      = "./modules/frontend"
  count       = var.deploy_frontend ? 1 : 0
  name_prefix = local.name_prefix

  api_url = module.api.api_url

  subnet_id         = var.frontend_subnet_id
  security_group_id = var.frontend_security_group_id
  instance_type     = var.frontend_instance_type
  key_name          = var.frontend_key_name
  port              = var.frontend_port

  frontend_repo_url = var.frontend_repo_url
  frontend_subdir   = var.frontend_subdir
}
