# --- general --------------------------------------------------------------- #

variable "region" {
  type        = string
  default     = "us-east-1"
  description = "AWS region for all resources."
}

variable "project" {
  type    = string
  default = "sdv"
}

variable "env" {
  type    = string
  default = "dev"
}

# --- compute / bedrock (§7) ------------------------------------------------ #

variable "bedrock_model_id" {
  type        = string
  default     = "us.anthropic.claude-opus-4-5-20251101-v1:0"
  description = "Claude model id / cross-region inference profile for Bedrock. Default = most powerful Opus profile available in the target account (us-east-1)."
}

variable "bedrock_region" {
  type        = string
  default     = ""
  description = "Bedrock invocation region; defaults to var.region when empty."
}

variable "ingest_model_id" {
  type        = string
  default     = ""
  description = "Override model for the ingest Lambda; empty = bedrock_model_id."
}

variable "analyze_model_id" {
  type        = string
  default     = ""
  description = "Override model for the analyze Lambda; empty = bedrock_model_id."
}

variable "github_token_secret_arn" {
  type        = string
  default     = ""
  description = "Secrets Manager ARN for the GitHub token (private repos only). Empty disables it."
}

variable "log_level" {
  type    = string
  default = "INFO"
}

variable "ingest_reserved_concurrency" {
  type    = number
  default = 2
}

variable "analyze_reserved_concurrency" {
  type    = number
  default = 5
}

# --- frontend (reused VPC networking) -------------------------------------- #

variable "deploy_frontend" {
  type        = bool
  default     = true
  description = "Whether to launch the frontend EC2 instance."
}

variable "frontend_subnet_id" {
  type        = string
  description = "Existing public subnet id for the frontend instance."
}

variable "frontend_security_group_id" {
  type        = string
  description = "Existing security group id to attach to the frontend instance."
}

variable "frontend_instance_type" {
  type    = string
  default = "t3.small"
}

variable "frontend_key_name" {
  type    = string
  default = ""
}

variable "frontend_port" {
  type        = number
  default     = 8443
  description = "Port the SPA is served on; must be open in the reused security group."
}

variable "frontend_repo_url" {
  type        = string
  description = "Git URL cloned by the frontend instance to fetch the SPA source."
}

variable "frontend_subdir" {
  type    = string
  default = "components/frontend"
}
