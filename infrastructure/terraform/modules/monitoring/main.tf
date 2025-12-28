# Monitoring Module - CloudWatch, Alarms, Dashboards

# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "lambda" {
  for_each = var.lambda_functions

  name              = "/aws/lambda/${each.value}"
  retention_in_days = var.log_retention_days

  tags = merge(
    var.tags,
    {
      Name = "${var.name}-${each.key}-logs"
    }
  )
}

# CloudWatch Log Group for API Gateway
resource "aws_cloudwatch_log_group" "api_gateway" {
  count = var.enable_api_gateway_logs ? 1 : 0

  name              = "/aws/apigateway/${var.name}"
  retention_in_days = var.log_retention_days

  tags = merge(
    var.tags,
    {
      Name = "${var.name}-api-gateway-logs"
    }
  )
}

# CloudWatch Alarms - Lambda Errors
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  for_each = var.lambda_functions

  alarm_name          = "${var.name}-${each.key}-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period               = 300
  statistic           = "Sum"
  threshold           = 5
  alarm_description   = "This metric monitors lambda errors for ${each.key}"
  alarm_actions       = var.sns_topic_arn != "" ? [var.sns_topic_arn] : []

  dimensions = {
    FunctionName = each.value
  }

  tags = var.tags
}

# CloudWatch Alarms - Lambda Duration
resource "aws_cloudwatch_metric_alarm" "lambda_duration" {
  for_each = var.lambda_functions

  alarm_name          = "${var.name}-${each.key}-duration"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "Duration"
  namespace           = "AWS/Lambda"
  period               = 300
  statistic           = "Average"
  threshold           = var.lambda_duration_threshold
  alarm_description   = "This metric monitors lambda duration for ${each.key}"
  alarm_actions       = var.sns_topic_arn != "" ? [var.sns_topic_arn] : []

  dimensions = {
    FunctionName = each.value
  }

  tags = var.tags
}

# CloudWatch Alarms - API Gateway 4xx Errors
resource "aws_cloudwatch_metric_alarm" "api_gateway_4xx" {
  count = var.enable_api_gateway_logs ? 1 : 0

  alarm_name          = "${var.name}-api-gateway-4xx-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "4XXError"
  namespace           = "AWS/ApiGateway"
  period               = 300
  statistic           = "Sum"
  threshold           = 50
  alarm_description   = "This metric monitors API Gateway 4xx errors"
  alarm_actions       = var.sns_topic_arn != "" ? [var.sns_topic_arn] : []

  dimensions = {
    ApiName = var.api_gateway_name
  }

  tags = var.tags
}

# CloudWatch Alarms - API Gateway 5xx Errors
resource "aws_cloudwatch_metric_alarm" "api_gateway_5xx" {
  count = var.enable_api_gateway_logs ? 1 : 0

  alarm_name          = "${var.name}-api-gateway-5xx-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "5XXError"
  namespace           = "AWS/ApiGateway"
  period               = 300
  statistic           = "Sum"
  threshold           = 1
  alarm_description   = "This metric monitors API Gateway 5xx errors"
  alarm_actions       = var.sns_topic_arn != "" ? [var.sns_topic_arn] : []

  dimensions = {
    ApiName = var.api_gateway_name
  }

  tags = var.tags
}

# CloudWatch Dashboard
resource "aws_cloudwatch_dashboard" "main" {
  count = var.enable_dashboard ? 1 : 0

  dashboard_name = "${var.name}-dashboard"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6

        properties = {
          metrics = [
            for func_name in values(var.lambda_functions) : [
              "AWS/Lambda",
              "Invocations",
              "FunctionName",
              func_name
            ]
          ]
          period = 300
          stat   = "Sum"
          region = data.aws_region.current.name
          title  = "Lambda Invocations"
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6

        properties = {
          metrics = [
            for func_name in values(var.lambda_functions) : [
              "AWS/Lambda",
              "Errors",
              "FunctionName",
              func_name
            ]
          ]
          period = 300
          stat   = "Sum"
          region = data.aws_region.current.name
          title  = "Lambda Errors"
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6

        properties = {
          metrics = [
            for func_name in values(var.lambda_functions) : [
              "AWS/Lambda",
              "Duration",
              "FunctionName",
              func_name
            ]
          ]
          period = 300
          stat   = "Average"
          region = data.aws_region.current.name
          title  = "Lambda Duration"
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 6
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/ApiGateway", "Count", "ApiName", var.api_gateway_name],
            [".", "4XXError", ".", "."],
            [".", "5XXError", ".", "."]
          ]
          period = 300
          stat   = "Sum"
          region = data.aws_region.current.name
          title  = "API Gateway Metrics"
        }
      }
    ]
  })

  tags = var.tags
}

# SNS Topic for Alarms (optional)
resource "aws_sns_topic" "alerts" {
  count = var.create_sns_topic ? 1 : 0

  name = "${var.name}-alerts"

  tags = merge(
    var.tags,
    {
      Name = "${var.name}-alerts"
    }
  )
}

resource "aws_sns_topic_subscription" "email" {
  for_each = var.create_sns_topic && length(var.sns_email_subscriptions) > 0 ? toset(var.sns_email_subscriptions) : []

  topic_arn = aws_sns_topic.alerts[0].arn
  protocol  = "email"
  endpoint  = each.value
}

data "aws_region" "current" {}

