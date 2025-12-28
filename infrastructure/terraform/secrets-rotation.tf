# Secrets Rotation Configuration

# Lambda function for secrets rotation
resource "aws_lambda_function" "secrets_rotation" {
  filename         = data.archive_file.secrets_rotation_zip.output_path
  function_name    = "${local.project_name}-secrets-rotation-${var.environment}"
  role             = aws_iam_role.secrets_rotation.arn
  handler          = "secrets_rotation.handler"
  source_code_hash = data.archive_file.secrets_rotation_zip.output_base64sha256
  runtime          = "python3.11"
  timeout          = 300
  memory_size      = 256

  environment {
    variables = {
      ENVIRONMENT = var.environment
    }
  }

  tags = local.common_tags
}

# Archive for secrets rotation Lambda
data "archive_file" "secrets_rotation_zip" {
  type        = "zip"
  source_file = "${path.module}/../lambda/secrets_rotation.py"
  output_path = "${path.module}/secrets-rotation.zip"
}

# IAM Role for Secrets Rotation
resource "aws_iam_role" "secrets_rotation" {
  name = "${local.project_name}-secrets-rotation-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = [
            "lambda.amazonaws.com",
            "secretsmanager.amazonaws.com"
          ]
        }
      }
    ]
  })

  tags = local.common_tags
}

# IAM Policy for Secrets Rotation
resource "aws_iam_role_policy" "secrets_rotation" {
  name = "${local.project_name}-secrets-rotation-policy-${var.environment}"
  role = aws_iam_role.secrets_rotation.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:DescribeSecret",
          "secretsmanager:GetSecretValue",
          "secretsmanager:PutSecretValue",
          "secretsmanager:UpdateSecretVersionStage"
        ]
        Resource = [
          aws_secretsmanager_secret.openai_api_key.arn,
          aws_secretsmanager_secret.anthropic_api_key.arn,
          aws_secretsmanager_secret.spacelift_webhook_secret.arn,
          aws_secretsmanager_secret.github_webhook_secret.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetRandomPassword"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

# EventBridge Rule for Secrets Rotation
resource "aws_cloudwatch_event_rule" "secrets_rotation" {
  name                = "${local.project_name}-secrets-rotation-${var.environment}"
  description         = "Trigger secrets rotation"
  schedule_expression = "rate(30 days)"  # Rotate every 30 days

  tags = local.common_tags
}

resource "aws_cloudwatch_event_target" "secrets_rotation" {
  rule      = aws_cloudwatch_event_rule.secrets_rotation.name
  target_id = "SecretsRotationTarget"
  arn       = aws_lambda_function.secrets_rotation.arn
}

resource "aws_lambda_permission" "secrets_rotation_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.secrets_rotation.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.secrets_rotation.arn
}

# Secrets Rotation Configuration
resource "aws_secretsmanager_secret_rotation" "openai_api_key" {
  count = var.enable_secrets_rotation ? 1 : 0

  secret_id           = aws_secretsmanager_secret.openai_api_key.id
  rotation_lambda_arn = aws_lambda_function.secrets_rotation.arn

  rotation_rules {
    automatically_after_days = var.secrets_rotation_days
  }
}

resource "aws_secretsmanager_secret_rotation" "anthropic_api_key" {
  count = var.enable_secrets_rotation ? 1 : 0

  secret_id           = aws_secretsmanager_secret.anthropic_api_key.id
  rotation_lambda_arn = aws_lambda_function.secrets_rotation.arn

  rotation_rules {
    automatically_after_days = var.secrets_rotation_days
  }
}

resource "aws_secretsmanager_secret_rotation" "spacelift_webhook_secret" {
  count = var.enable_secrets_rotation ? 1 : 0

  secret_id           = aws_secretsmanager_secret.spacelift_webhook_secret.id
  rotation_lambda_arn = aws_lambda_function.secrets_rotation.arn

  rotation_rules {
    automatically_after_days = var.secrets_rotation_days
  }
}

resource "aws_secretsmanager_secret_rotation" "github_webhook_secret" {
  count = var.enable_secrets_rotation ? 1 : 0

  secret_id           = aws_secretsmanager_secret.github_webhook_secret.id
  rotation_lambda_arn = aws_lambda_function.secrets_rotation.arn

  rotation_rules {
    automatically_after_days = var.secrets_rotation_days
  }
}

