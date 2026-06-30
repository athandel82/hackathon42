# compute module (ARCHITECTURE.md §6, §7, §5)
# ECR x2 + image build/push + the two Lambdas + IAM + env vars.

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

locals {
  account_id = data.aws_caller_identity.current.account_id
  region     = var.region

  ingest_fn_name  = "${var.name_prefix}-ingest"
  analyze_fn_name = "${var.name_prefix}-analyze"

  # Constructed ARNs (used in env vars / IAM) so we avoid resource cycles with
  # the functions themselves (e.g. the ingest self-invoke grant).
  ingest_fn_arn  = "arn:aws:lambda:${local.region}:${local.account_id}:function:${local.ingest_fn_name}"
  analyze_fn_arn = "arn:aws:lambda:${local.region}:${local.account_id}:function:${local.analyze_fn_name}"

  # Content hashes of each build context → image tag. Changing any source file
  # produces a new tag, so Terraform rebuilds/pushes and updates the function.
  ingest_files  = fileset(var.ingest_context, "**")
  analyze_files = fileset(var.analyze_context, "**")
  ingest_hash   = substr(sha1(join("", [for f in local.ingest_files : filesha1("${var.ingest_context}/${f}")])), 0, 12)
  analyze_hash  = substr(sha1(join("", [for f in local.analyze_files : filesha1("${var.analyze_context}/${f}")])), 0, 12)

  ingest_image_uri  = "${aws_ecr_repository.ingest.repository_url}:${local.ingest_hash}"
  analyze_image_uri = "${aws_ecr_repository.analyze.repository_url}:${local.analyze_hash}"

  bedrock_region = var.bedrock_region != "" ? var.bedrock_region : var.region

  # Per-agent model selection (fall back to the shared default).
  ingest_model_id  = var.ingest_model_id != "" ? var.ingest_model_id : var.bedrock_model_id
  analyze_model_id = var.analyze_model_id != "" ? var.analyze_model_id : var.bedrock_model_id

  # Image build platform follows the chosen Lambda architecture (native build
  # on a matching host, e.g. linux/arm64 on Graviton/arm).
  docker_platform = var.lambda_architecture == "arm64" ? "linux/arm64" : "linux/amd64"

  # Bedrock invoke is scoped to foundation models + inference profiles rather
  # than "*" (prototype least-privilege, §5).
  bedrock_resources = [
    "arn:aws:bedrock:*::foundation-model/*",
    "arn:aws:bedrock:*:${local.account_id}:inference-profile/*",
  ]
}

# --------------------------------------------------------------------------- #
# ECR registries (G1)
# --------------------------------------------------------------------------- #

resource "aws_ecr_repository" "ingest" {
  name                 = "${var.name_prefix}-ingest"
  image_tag_mutability = "MUTABLE"
  force_delete         = true
  image_scanning_configuration {
    scan_on_push = false
  }
}

resource "aws_ecr_repository" "analyze" {
  name                 = "${var.name_prefix}-analyze"
  image_tag_mutability = "MUTABLE"
  force_delete         = true
  image_scanning_configuration {
    scan_on_push = false
  }
}

# --------------------------------------------------------------------------- #
# Image build + push (TF-driven docker build, §7)
# --------------------------------------------------------------------------- #

resource "null_resource" "ingest_image" {
  triggers = {
    image_uri = local.ingest_image_uri
  }
  provisioner "local-exec" {
    command = "${path.module}/scripts/build_and_push.sh ${var.ingest_context} ${var.ingest_context}/Dockerfile ${local.ingest_image_uri} ${local.region} ${local.docker_platform}"
  }
  depends_on = [aws_ecr_repository.ingest]
}

resource "null_resource" "analyze_image" {
  triggers = {
    image_uri = local.analyze_image_uri
  }
  provisioner "local-exec" {
    command = "${path.module}/scripts/build_and_push.sh ${var.analyze_context} ${var.analyze_context}/Dockerfile ${local.analyze_image_uri} ${local.region} ${local.docker_platform}"
  }
  depends_on = [aws_ecr_repository.analyze]
}

# --------------------------------------------------------------------------- #
# CloudWatch log groups
# --------------------------------------------------------------------------- #

resource "aws_cloudwatch_log_group" "ingest" {
  name              = "/aws/lambda/${local.ingest_fn_name}"
  retention_in_days = 14
}

resource "aws_cloudwatch_log_group" "analyze" {
  name              = "/aws/lambda/${local.analyze_fn_name}"
  retention_in_days = 14
}

# --------------------------------------------------------------------------- #
# IAM — Ingest Lambda role (§5, ingestion-agent §11.4)
# --------------------------------------------------------------------------- #

data "aws_iam_policy_document" "lambda_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "ingest" {
  name               = "${local.ingest_fn_name}-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
}

resource "aws_iam_role_policy_attachment" "ingest_logs" {
  role       = aws_iam_role.ingest.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

data "aws_iam_policy_document" "ingest" {
  # S3 RW on the KB bucket (<repo_id>/*).
  statement {
    sid       = "S3ReadWrite"
    actions   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"]
    resources = ["${var.kb_bucket_arn}/*"]
  }
  statement {
    sid       = "S3List"
    actions   = ["s3:ListBucket"]
    resources = [var.kb_bucket_arn]
  }
  # repos table RW.
  statement {
    sid       = "ReposReadWrite"
    actions   = ["dynamodb:PutItem", "dynamodb:UpdateItem", "dynamodb:GetItem"]
    resources = [var.repos_table_arn]
  }
  # Bedrock invoke (+ stream).
  statement {
    sid       = "BedrockInvoke"
    actions   = ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"]
    resources = local.bedrock_resources
  }
  # Async self-invoke of the worker (§5a) — scoped to own ARN.
  statement {
    sid       = "SelfInvoke"
    actions   = ["lambda:InvokeFunction"]
    resources = [local.ingest_fn_arn]
  }
}

resource "aws_iam_role_policy" "ingest" {
  name   = "${local.ingest_fn_name}-policy"
  role   = aws_iam_role.ingest.id
  policy = data.aws_iam_policy_document.ingest.json
}

# Secrets read only when a GitHub token secret is configured (private repos).
data "aws_iam_policy_document" "ingest_secret" {
  count = var.github_token_secret_arn != "" ? 1 : 0
  statement {
    actions   = ["secretsmanager:GetSecretValue"]
    resources = [var.github_token_secret_arn]
  }
}

resource "aws_iam_role_policy" "ingest_secret" {
  count  = var.github_token_secret_arn != "" ? 1 : 0
  name   = "${local.ingest_fn_name}-secret"
  role   = aws_iam_role.ingest.id
  policy = data.aws_iam_policy_document.ingest_secret[0].json
}

# --------------------------------------------------------------------------- #
# IAM — Analyze Lambda role (§5, analyze-agent §11.4) — S3 READ-ONLY
# --------------------------------------------------------------------------- #

resource "aws_iam_role" "analyze" {
  name               = "${local.analyze_fn_name}-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
}

resource "aws_iam_role_policy_attachment" "analyze_logs" {
  role       = aws_iam_role.analyze.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

data "aws_iam_policy_document" "analyze" {
  # S3 read-only on the KB tree (<repo_id>/kb/*). No PutObject — hard safety property.
  statement {
    sid       = "S3ReadOnly"
    actions   = ["s3:GetObject"]
    resources = ["${var.kb_bucket_arn}/*"]
  }
  statement {
    sid       = "S3List"
    actions   = ["s3:ListBucket"]
    resources = [var.kb_bucket_arn]
  }
  # results table RW (cache + sessions).
  statement {
    sid       = "ResultsReadWrite"
    actions   = ["dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:UpdateItem", "dynamodb:Query"]
    resources = [var.results_table_arn]
  }
  # repos read for the /analyze 409 readiness check (§5b, G7).
  statement {
    sid       = "ReposRead"
    actions   = ["dynamodb:GetItem"]
    resources = [var.repos_table_arn]
  }
  # Bedrock invoke (+ stream).
  statement {
    sid       = "BedrockInvoke"
    actions   = ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"]
    resources = local.bedrock_resources
  }
}

resource "aws_iam_role_policy" "analyze" {
  name   = "${local.analyze_fn_name}-policy"
  role   = aws_iam_role.analyze.id
  policy = data.aws_iam_policy_document.analyze.json
}

# --------------------------------------------------------------------------- #
# Lambda functions (container images, §7)
# --------------------------------------------------------------------------- #

resource "aws_lambda_function" "ingest" {
  function_name = local.ingest_fn_name
  role          = aws_iam_role.ingest.arn
  package_type  = "Image"
  image_uri     = local.ingest_image_uri
  architectures = [var.lambda_architecture]
  memory_size   = 10240 # max (≈6 vCPU) — fastest XML parse + orchestration
  timeout       = 900   # max

  reserved_concurrent_executions = var.ingest_reserved_concurrency

  ephemeral_storage {
    size = 10240 # max /tmp for tarball + extracted ARXML + KB tree
  }

  environment {
    variables = {
      KB_BUCKET            = var.kb_bucket
      REPOS_TABLE          = var.repos_table
      BEDROCK_MODEL_ID     = local.ingest_model_id
      BEDROCK_REGION       = local.bedrock_region
      WORKER_FUNCTION_NAME = local.ingest_fn_name
      KB_WORKDIR           = "/tmp"
      LOG_LEVEL            = var.log_level
      # Optional: only set when a secret is configured.
      GITHUB_TOKEN_SECRET_ARN = var.github_token_secret_arn
    }
  }

  depends_on = [
    null_resource.ingest_image,
    aws_cloudwatch_log_group.ingest,
    aws_iam_role_policy.ingest,
  ]
}

resource "aws_lambda_function" "analyze" {
  function_name = local.analyze_fn_name
  role          = aws_iam_role.analyze.arn
  package_type  = "Image"
  image_uri     = local.analyze_image_uri
  architectures = [var.lambda_architecture]
  memory_size   = 10240 # max (≈6 vCPU) — fastest KB reads + model synthesis
  timeout       = 900   # max (NOTE: sync /analyze is still capped by API GW at 30s)

  reserved_concurrent_executions = var.analyze_reserved_concurrency

  ephemeral_storage {
    size = 10240 # max /tmp — largest KB cache + in-run staging headroom
  }

  environment {
    variables = {
      KB_BUCKET        = var.kb_bucket
      RESULTS_TABLE    = var.results_table
      REPOS_TABLE      = var.repos_table
      BEDROCK_MODEL_ID = local.analyze_model_id
      BEDROCK_REGION   = local.bedrock_region
      KB_CACHE_DIR     = "/tmp"
      LOG_LEVEL        = var.log_level
    }
  }

  depends_on = [
    null_resource.analyze_image,
    aws_cloudwatch_log_group.analyze,
    aws_iam_role_policy.analyze,
  ]
}
