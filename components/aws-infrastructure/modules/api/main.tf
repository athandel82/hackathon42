# api module (ARCHITECTURE.md §3)
# HTTP API with Lambda proxy integrations, no authorizer (open prototype),
# CORS `*` (§S1, breaks the EC2<->API cycle).

resource "aws_apigatewayv2_api" "http" {
  name          = "${var.name_prefix}-api"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["*"]
    allow_headers = ["*"]
    max_age       = 3600
  }
}

# --- integrations (AWS_PROXY, payload format 2.0) -------------------------- #

resource "aws_apigatewayv2_integration" "ingest" {
  api_id                 = aws_apigatewayv2_api.http.id
  integration_type       = "AWS_PROXY"
  integration_uri        = var.ingest_invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_integration" "analyze" {
  api_id                 = aws_apigatewayv2_api.http.id
  integration_type       = "AWS_PROXY"
  integration_uri        = var.analyze_invoke_arn
  payload_format_version = "2.0"
}

# --- routes (§3) ----------------------------------------------------------- #
# POST /ingest, GET /status -> Ingest λ ; POST /analyze -> Analyze λ.

resource "aws_apigatewayv2_route" "post_ingest" {
  api_id    = aws_apigatewayv2_api.http.id
  route_key = "POST /ingest"
  target    = "integrations/${aws_apigatewayv2_integration.ingest.id}"
}

resource "aws_apigatewayv2_route" "get_status" {
  api_id    = aws_apigatewayv2_api.http.id
  route_key = "GET /status"
  target    = "integrations/${aws_apigatewayv2_integration.ingest.id}"
}

resource "aws_apigatewayv2_route" "post_analyze" {
  api_id    = aws_apigatewayv2_api.http.id
  route_key = "POST /analyze"
  target    = "integrations/${aws_apigatewayv2_integration.analyze.id}"
}

# --- stage ($default, auto-deploy: base URL has no stage path) ------------- #

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.http.id
  name        = "$default"
  auto_deploy = true
}

# --- permissions: allow API Gateway to invoke each Lambda ------------------ #

resource "aws_lambda_permission" "ingest" {
  statement_id  = "AllowApiGatewayInvokeIngest"
  action        = "lambda:InvokeFunction"
  function_name = var.ingest_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http.execution_arn}/*/*"
}

resource "aws_lambda_permission" "analyze" {
  statement_id  = "AllowApiGatewayInvokeAnalyze"
  action        = "lambda:InvokeFunction"
  function_name = var.analyze_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http.execution_arn}/*/*"
}
