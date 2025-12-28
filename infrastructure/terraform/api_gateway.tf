resource "aws_apigatewayv2_api" "main" {
  name          = "${local.project_name}-api-${var.environment}"
  protocol_type = "HTTP"
  description   = "API Gateway for Terraform Spacelift AI Reviewer"

  cors_configuration {
    allow_origins = var.allowed_origins
    allow_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allow_headers = ["content-type", "authorization", "x-api-key"]
    max_age       = 300
  }

  tags = local.common_tags
}

# JWT Authorizer
resource "aws_apigatewayv2_authorizer" "jwt" {
  api_id           = aws_apigatewayv2_api.main.id
  authorizer_type  = "REQUEST"
  authorizer_uri   = aws_lambda_function.jwt_authorizer.invoke_arn
  identity_sources = ["$request.header.Authorization"]
  name             = "jwt-authorizer"
  
  authorizer_payload_format_version = "2.0"
  
  enable_simple_responses = true
}

resource "aws_apigatewayv2_integration" "api_handler" {
  api_id           = aws_apigatewayv2_api.main.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.api_handler.invoke_arn
}

resource "aws_apigatewayv2_integration" "webhook_handler" {
  api_id           = aws_apigatewayv2_api.main.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.webhook_handler.invoke_arn
}

resource "aws_apigatewayv2_integration" "pr_review" {
  api_id           = aws_apigatewayv2_api.main.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.pr_review_handler.invoke_arn
}

resource "aws_apigatewayv2_integration" "github_webhook" {
  api_id           = aws_apigatewayv2_api.main.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.github_webhook_handler.invoke_arn
}

resource "aws_apigatewayv2_integration" "historical_analysis" {
  api_id           = aws_apigatewayv2_api.main.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.historical_analysis_handler.invoke_arn
}

resource "aws_apigatewayv2_route" "api_routes" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "GET /api/reviews"
  target    = "integrations/${aws_apigatewayv2_integration.api_handler.id}"
  authorizer_id = aws_apigatewayv2_authorizer.jwt.id
  authorization_type = "CUSTOM"
}

resource "aws_apigatewayv2_route" "api_review_by_id" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "GET /api/reviews/{reviewId}"
  target    = "integrations/${aws_apigatewayv2_integration.api_handler.id}"
}

resource "aws_apigatewayv2_route" "api_review_create" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "POST /api/reviews"
  target    = "integrations/${aws_apigatewayv2_integration.api_handler.id}"
  authorizer_id = aws_apigatewayv2_authorizer.jwt.id
  authorization_type = "CUSTOM"
}

resource "aws_apigatewayv2_route" "api_review_update" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "PUT /api/reviews/{reviewId}"
  target    = "integrations/${aws_apigatewayv2_integration.api_handler.id}"
  authorizer_id = aws_apigatewayv2_authorizer.jwt.id
  authorization_type = "CUSTOM"
}

resource "aws_apigatewayv2_route" "api_analytics" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "GET /api/analytics"
  target    = "integrations/${aws_apigatewayv2_integration.api_handler.id}"
  authorizer_id = aws_apigatewayv2_authorizer.jwt.id
  authorization_type = "CUSTOM"
}

resource "aws_apigatewayv2_route" "api_historical_analysis" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "GET /api/analytics/historical"
  target    = "integrations/${aws_apigatewayv2_integration.historical_analysis.id}"
  authorizer_id = aws_apigatewayv2_authorizer.jwt.id
  authorization_type = "CUSTOM"
}

resource "aws_apigatewayv2_route" "api_pr_review" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "POST /api/reviews/pr"
  target    = "integrations/${aws_apigatewayv2_integration.pr_review.id}"
  authorizer_id = aws_apigatewayv2_authorizer.jwt.id
  authorization_type = "CUSTOM"
}

resource "aws_apigatewayv2_route" "webhook_route" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "POST /webhook/spacelift"
  target    = "integrations/${aws_apigatewayv2_integration.webhook_handler.id}"
}

resource "aws_apigatewayv2_route" "webhook_github" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "POST /webhook/github"
  target    = "integrations/${aws_apigatewayv2_integration.github_webhook.id}"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.main.id
  name        = "$default"
  auto_deploy = true

  default_route_settings {
    throttling_rate_limit  = 100
    throttling_burst_limit = 200
  }

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      ip             = "$context.identity.sourceIp"
      requestTime    = "$context.requestTime"
      httpMethod     = "$context.httpMethod"
      routeKey       = "$context.routeKey"
      status         = "$context.status"
      protocol       = "$context.protocol"
      responseLength = "$context.responseLength"
    })
  }
}

resource "aws_cloudwatch_log_group" "api_gateway" {
  name              = "/aws/apigateway/${local.project_name}-${var.environment}"
  retention_in_days = 30

  tags = local.common_tags
}

resource "aws_apigatewayv2_api_mapping" "custom_domain" {
  count       = var.custom_domain_name != "" ? 1 : 0
  api_id      = aws_apigatewayv2_api.main.id
  domain_name = var.custom_domain_name
  stage       = aws_apigatewayv2_stage.default.id
}

