resource "aws_secretsmanager_secret" "openai_api_key" {
  name                    = "${local.project_name}/openai-api-key/${var.environment}"
  description             = "OpenAI API key for AI review service"
  recovery_window_in_days = 7

  tags = local.common_tags
}

resource "aws_secretsmanager_secret_version" "openai_api_key" {
  count         = var.openai_api_key != "" ? 1 : 0
  secret_id     = aws_secretsmanager_secret.openai_api_key.id
  secret_string = var.openai_api_key
}

resource "aws_secretsmanager_secret" "anthropic_api_key" {
  name                    = "${local.project_name}/anthropic-api-key/${var.environment}"
  description             = "Anthropic API key for AI review service"
  recovery_window_in_days = 7

  tags = local.common_tags
}

resource "aws_secretsmanager_secret_version" "anthropic_api_key" {
  count         = var.anthropic_api_key != "" ? 1 : 0
  secret_id     = aws_secretsmanager_secret.anthropic_api_key.id
  secret_string = var.anthropic_api_key
}

resource "aws_secretsmanager_secret" "spacelift_webhook_secret" {
  name                    = "${local.project_name}/spacelift-webhook-secret/${var.environment}"
  description             = "Spacelift webhook secret for validation"
  recovery_window_in_days = 7

  tags = local.common_tags
}

resource "aws_secretsmanager_secret_version" "spacelift_webhook_secret" {
  count         = var.spacelift_webhook_secret != "" ? 1 : 0
  secret_id     = aws_secretsmanager_secret.spacelift_webhook_secret.id
  secret_string = var.spacelift_webhook_secret
}

resource "aws_secretsmanager_secret" "github_webhook_secret" {
  name                    = "${local.project_name}/github-webhook-secret/${var.environment}"
  description             = "GitHub webhook secret for validation"
  recovery_window_in_days = 7

  tags = local.common_tags
}

resource "aws_secretsmanager_secret_version" "github_webhook_secret" {
  count         = var.github_webhook_secret != "" ? 1 : 0
  secret_id     = aws_secretsmanager_secret.github_webhook_secret.id
  secret_string = var.github_webhook_secret
}

