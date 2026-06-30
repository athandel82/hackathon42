variable "name_prefix" {
  type = string
}

variable "ingest_invoke_arn" {
  type        = string
  description = "invoke_arn of the ingest Lambda (POST /ingest, GET /status)."
}

variable "ingest_function_name" {
  type = string
}

variable "analyze_invoke_arn" {
  type        = string
  description = "invoke_arn of the analyze Lambda (POST /analyze)."
}

variable "analyze_function_name" {
  type = string
}
