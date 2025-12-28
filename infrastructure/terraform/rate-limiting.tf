# Rate Limiting Configuration

# API Gateway Throttling
resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.main.id
  name        = var.environment
  auto_deploy = true

  # Rate limiting
  default_route_settings {
    throttling_burst_limit = var.api_throttle_burst_limit
    throttling_rate_limit  = var.api_throttle_rate_limit
  }

  # Access logging
  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway[0].arn
    format = jsonencode({
      requestId      = "$context.requestId"
      ip             = "$context.identity.sourceIp"
      requestTime    = "$context.requestTime"
      httpMethod     = "$context.httpMethod"
      routeKey       = "$context.routeKey"
      status         = "$context.status"
      protocol       = "$context.protocol"
      responseLength = "$context.responseLength"
      userAgent      = "$context.identity.userAgent"
      error          = "$context.error.message"
      integrationError = "$context.integration.error"
    })
  }

  tags = local.common_tags
}

# Per-route rate limiting
resource "aws_apigatewayv2_route_settings" "api_routes" {
  api_id    = aws_apigatewayv2_api.main.id
  stage_id  = aws_apigatewayv2_stage.default.id
  route_key = "GET /api/reviews"

  throttling_burst_limit = var.api_throttle_burst_limit
  throttling_rate_limit  = var.api_throttle_rate_limit
}

resource "aws_apigatewayv2_route_settings" "api_review_create" {
  api_id    = aws_apigatewayv2_api.main.id
  stage_id  = aws_apigatewayv2_stage.default.id
  route_key = "POST /api/reviews"

  throttling_burst_limit = var.api_throttle_burst_limit / 2  # Stricter for write operations
  throttling_rate_limit  = var.api_throttle_rate_limit / 2
}

resource "aws_apigatewayv2_route_settings" "webhook_routes" {
  api_id    = aws_apigatewayv2_api.main.id
  stage_id  = aws_apigatewayv2_stage.default.id
  route_key = "POST /webhook/*"

  throttling_burst_limit = 100  # Higher for webhooks
  throttling_rate_limit  = 50
}

# Lambda Reserved Concurrency (Rate Limiting)
resource "aws_lambda_function_event_invoke_config" "api_handler" {
  function_name = aws_lambda_function.api_handler.function_name

  maximum_retry_attempts = 2
  maximum_event_age_in_seconds = 60

  destination_config {
    on_failure {
      destination = aws_sqs_queue.lambda_dlq.arn
    }
  }
}

resource "aws_lambda_provisioned_concurrency_config" "api_handler" {
  count = var.enable_provisioned_concurrency ? 1 : 0

  function_name                     = aws_lambda_function.api_handler.function_name
  provisioned_concurrent_executions = var.provisioned_concurrency_count
  qualifier                         = aws_lambda_function.api_handler.version
}

# Dead Letter Queue for failed Lambda invocations
resource "aws_sqs_queue" "lambda_dlq" {
  name                      = "${local.project_name}-lambda-dlq-${var.environment}"
  message_retention_seconds = 1209600  # 14 days
  receive_wait_time_seconds = 20

  tags = merge(
    local.common_tags,
    {
      Name = "${local.project_name}-lambda-dlq-${var.environment}"
    }
  )
}

# CloudWatch Log Group for API Gateway
resource "aws_cloudwatch_log_group" "api_gateway" {
  count = var.enable_api_gateway_logs ? 1 : 0

  name              = "/aws/apigateway/${local.project_name}-${var.environment}"
  retention_in_days = var.log_retention_days

  tags = local.common_tags
}

