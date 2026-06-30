output "api_url" {
  description = "Base invoke URL of the HTTP API ($default stage, no stage path). Used as the frontend apiBaseUrl."
  value       = aws_apigatewayv2_stage.default.invoke_url
}

output "api_id" {
  value = aws_apigatewayv2_api.http.id
}
