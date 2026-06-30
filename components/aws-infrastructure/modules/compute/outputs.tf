output "ingest_function_name" {
  value = aws_lambda_function.ingest.function_name
}

output "ingest_invoke_arn" {
  description = "ARN used by API Gateway AWS_PROXY integration for the ingest Lambda."
  value       = aws_lambda_function.ingest.invoke_arn
}

output "ingest_function_arn" {
  value = aws_lambda_function.ingest.arn
}

output "analyze_function_name" {
  value = aws_lambda_function.analyze.function_name
}

output "analyze_invoke_arn" {
  value = aws_lambda_function.analyze.invoke_arn
}

output "analyze_function_arn" {
  value = aws_lambda_function.analyze.arn
}

output "ingest_ecr_repository_url" {
  value = aws_ecr_repository.ingest.repository_url
}

output "analyze_ecr_repository_url" {
  value = aws_ecr_repository.analyze.repository_url
}
