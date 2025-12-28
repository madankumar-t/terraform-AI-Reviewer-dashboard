# Monitoring and Logging Configuration

module "monitoring" {
  source = "./modules/monitoring"

  name = "${local.project_name}-${var.environment}"

  lambda_functions = {
    api_handler              = aws_lambda_function.api_handler.function_name
    ai_reviewer              = aws_lambda_function.ai_reviewer.function_name
    pr_review_handler        = aws_lambda_function.pr_review_handler.function_name
    webhook_handler          = aws_lambda_function.webhook_handler.function_name
    github_webhook_handler   = aws_lambda_function.github_webhook_handler.function_name
    historical_analysis      = aws_lambda_function.historical_analysis_handler.function_name
    trend_aggregation        = aws_lambda_function.trend_aggregation_handler.function_name
    jwt_authorizer           = aws_lambda_function.jwt_authorizer.function_name
  }

  api_gateway_name         = aws_apigatewayv2_api.main.name
  enable_api_gateway_logs = true
  log_retention_days       = var.log_retention_days
  lambda_duration_threshold = 5000

  enable_dashboard     = true
  create_sns_topic     = var.create_sns_topic
  sns_topic_arn       = var.sns_topic_arn
  sns_email_subscriptions = var.sns_email_subscriptions

  tags = local.common_tags
}

