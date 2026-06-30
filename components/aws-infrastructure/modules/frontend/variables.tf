variable "name_prefix" {
  type = string
}

variable "api_url" {
  type        = string
  description = "API Gateway base URL written into the SPA config.json (apiBaseUrl)."
}

# --- reused networking (existing VPC) -------------------------------------- #

variable "subnet_id" {
  type        = string
  description = "Existing public subnet to launch the instance in."
}

variable "security_group_id" {
  type        = string
  description = "Existing security group to attach (must allow inbound on var.port)."
}

# --- instance -------------------------------------------------------------- #

variable "instance_type" {
  type    = string
  default = "t3.small"
}

variable "key_name" {
  type        = string
  default     = ""
  description = "Optional EC2 key pair name for SSH. Empty = no key."
}

variable "port" {
  type        = number
  default     = 8443
  description = "Port the SPA is served on; must be open in the reused security group."
}

# --- source ---------------------------------------------------------------- #

variable "frontend_repo_url" {
  type        = string
  description = "Git URL to clone for the frontend source (monorepo or frontend repo)."
}

variable "frontend_subdir" {
  type        = string
  default     = "components/frontend"
  description = "Path within the cloned repo that holds the frontend (package.json, start.sh)."
}
