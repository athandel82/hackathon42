output "kb_bucket" {
  description = "Name of the KB S3 bucket."
  value       = aws_s3_bucket.kb.id
}

output "kb_bucket_arn" {
  description = "ARN of the KB S3 bucket."
  value       = aws_s3_bucket.kb.arn
}

output "repos_table" {
  description = "Name of the repos (status) DynamoDB table."
  value       = aws_dynamodb_table.repos.name
}

output "repos_table_arn" {
  value = aws_dynamodb_table.repos.arn
}

output "results_table" {
  description = "Name of the results (cache/session) DynamoDB table."
  value       = aws_dynamodb_table.results.name
}

output "results_table_arn" {
  value = aws_dynamodb_table.results.arn
}
