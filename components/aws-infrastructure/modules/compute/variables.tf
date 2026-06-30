variable "name_prefix" {
  type        = string
  description = "Prefix for resource names (e.g. sdv-dev)."
}

variable "region" {
  type        = string
  description = "AWS region for the Lambdas / ECR."
}

variable "lambda_architecture" {
  type        = string
  default     = "arm64"
  description = "Lambda/image CPU architecture: arm64 (default, native on Graviton/arm hosts) or x86_64 (ARCHITECTURE.md §S7)."
  validation {
    condition     = contains(["arm64", "x86_64"], var.lambda_architecture)
    error_message = "lambda_architecture must be \"arm64\" or \"x86_64\"."
  }
}

# --- build contexts (component repos, §7) ---------------------------------- #

variable "ingest_context" {
  type        = string
  description = "Path to the ingestion-agent build context (contains Dockerfile)."
}

variable "analyze_context" {
  type        = string
  description = "Path to the analyze-agent build context (contains Dockerfile)."
}

# --- storage wiring (from the storage module) ------------------------------ #

variable "kb_bucket" {
  type = string
}
variable "kb_bucket_arn" {
  type = string
}
variable "repos_table" {
  type = string
}
variable "repos_table_arn" {
  type = string
}
variable "results_table" {
  type = string
}
variable "results_table_arn" {
  type = string
}

# --- compute variables (§7 env vars) --------------------------------------- #

variable "bedrock_model_id" {
  type        = string
  description = "Claude model id / inference profile id for Bedrock (shared default)."
}

variable "ingest_model_id" {
  type        = string
  default     = ""
  description = "Override model for the ingest Lambda; empty = use bedrock_model_id."
}

variable "analyze_model_id" {
  type        = string
  default     = ""
  description = "Override model for the analyze Lambda; empty = use bedrock_model_id."
}

variable "bedrock_region" {
  type        = string
  default     = ""
  description = "Bedrock region; defaults to var.region when empty."
}

variable "github_token_secret_arn" {
  type        = string
  default     = ""
  description = "Secrets Manager ARN for the GitHub token (private repos only). Empty disables the grant and env var."
}

variable "log_level" {
  type    = string
  default = "INFO"
}

variable "ingest_reserved_concurrency" {
  type        = number
  default     = 2
  description = "Bounds ingest self-invoke fan-out (§7: 1-2)."
}

variable "analyze_reserved_concurrency" {
  type        = number
  default     = 5
  description = "Bounds concurrent Bedrock calls (§7: 2-5)."
}
