# storage module (ARCHITECTURE.md §4, §6)
# Provisions the KB S3 bucket and the two application DynamoDB tables
# (`repos` for ingest status, `results` for analyze cache + sessions).

data "aws_caller_identity" "current" {}

locals {
  # Bucket names are globally unique; suffix with the account id.
  bucket_name = "${var.name_prefix}-kb-${data.aws_caller_identity.current.account_id}"
}

# --- S3: KB tree (<repo_id>/kb/, raw/ optional) ----------------------------- #

resource "aws_s3_bucket" "kb" {
  bucket        = local.bucket_name
  force_destroy = true # prototype: allow `terraform destroy` to remove objects
}

resource "aws_s3_bucket_public_access_block" "kb" {
  bucket                  = aws_s3_bucket.kb.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "kb" {
  bucket = aws_s3_bucket.kb.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# --- DynamoDB: repos (status, written by Ingest, read by /status) ----------- #

resource "aws_dynamodb_table" "repos" {
  name         = "${var.name_prefix}-repos"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "repo_id"

  attribute {
    name = "repo_id"
    type = "S"
  }
}

# --- DynamoDB: results (analyze cache + sessions, single-table §S4) ---------- #
# Schema matches analyze-agent cache.py (DdbCache): a single partition key
# `result_id` = "<repo_id>#<sha256(repo_id+request)>"; no sort key.

resource "aws_dynamodb_table" "results" {
  name         = "${var.name_prefix}-results"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "result_id"

  attribute {
    name = "result_id"
    type = "S"
  }
}
