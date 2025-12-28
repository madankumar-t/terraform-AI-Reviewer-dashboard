# Scaling Strategy Configuration

# Lambda Reserved Concurrency (Prevent over-scaling)
resource "aws_lambda_function_event_invoke_config" "reserved_concurrency" {
  for_each = var.lambda_reserved_concurrency

  function_name = each.key

  reserved_concurrent_executions = each.value
}

# Lambda Provisioned Concurrency (Warm starts)
resource "aws_lambda_provisioned_concurrency_config" "critical_functions" {
  for_each = var.lambda_provisioned_concurrency

  function_name                     = each.key
  provisioned_concurrent_executions = each.value
  qualifier                         = "$LATEST"
}

# Application Auto Scaling for API Gateway
resource "aws_appautoscaling_target" "api_gateway" {
  count = var.enable_api_gateway_auto_scaling ? 1 : 0

  max_capacity       = var.api_gateway_max_capacity
  min_capacity       = var.api_gateway_min_capacity
  resource_id        = "api/${aws_apigatewayv2_api.main.id}"
  scalable_dimension = "apigateway:api:count"
  service_namespace  = "apigateway"
}

# DynamoDB On-Demand (Auto-scaling)
# DynamoDB on-demand mode automatically scales, but we can set limits
resource "aws_dynamodb_table" "reviews" {
  # ... existing configuration ...
  
  billing_mode = var.dynamodb_billing_mode
  
  # On-demand mode automatically scales
  # Provisioned mode uses auto-scaling (see cost-optimization.tf)
}

# CloudFront Cache Policies (Performance scaling)
resource "aws_cloudfront_cache_policy" "api_cache" {
  name        = "${local.project_name}-api-cache-${var.environment}"
  comment     = "Cache policy for API responses"
  default_ttl = 0
  max_ttl     = 31536000
  min_ttl     = 0

  parameters_in_cache_key_and_forwarded_to_origin {
    enable_accept_encoding_brotli = true
    enable_accept_encoding_gzip    = true

    cookies_config {
      cookie_behavior = "none"
    }

    headers_config {
      header_behavior = "whitelist"
      headers {
        items = ["authorization", "x-api-key"]
      }
    }

    query_strings_config {
      query_string_behavior = "none"
    }
  }
}

# Auto Scaling Group for EC2 (if needed for future)
# Currently serverless, but prepared for EC2 scaling if required

# Step Functions for Long-Running Processes (Scaling alternative)
resource "aws_sfn_state_machine" "review_processing" {
  count = var.enable_step_functions ? 1 : 0

  name     = "${local.project_name}-review-processing-${var.environment}"
  role_arn = aws_iam_role.step_functions[0].arn

  definition = jsonencode({
    Comment = "Review Processing Workflow"
    StartAt = "ProcessReview"
    States = {
      ProcessReview = {
        Type = "Task"
        Resource = aws_lambda_function.ai_reviewer.arn
        End = true
      }
    }
  })

  tags = local.common_tags
}

# IAM Role for Step Functions
resource "aws_iam_role" "step_functions" {
  count = var.enable_step_functions ? 1 : 0

  name = "${local.project_name}-step-functions-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "states.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

# CloudWatch Alarms for Scaling Triggers
resource "aws_cloudwatch_metric_alarm" "lambda_concurrency_high" {
  for_each = var.lambda_scaling_alarms

  alarm_name          = "${local.project_name}-${each.key}-concurrency-high-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "ConcurrentExecutions"
  namespace           = "AWS/Lambda"
  period               = 60
  statistic           = "Average"
  threshold           = each.value
  alarm_description   = "This metric monitors lambda concurrency for scaling"

  dimensions = {
    FunctionName = each.key
  }

  tags = local.common_tags
}

# DynamoDB Read/Write Capacity Alarms (for provisioned mode)
resource "aws_cloudwatch_metric_alarm" "dynamodb_read_capacity" {
  count = var.dynamodb_billing_mode == "PROVISIONED" ? 1 : 0

  alarm_name          = "${local.project_name}-dynamodb-read-capacity-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "ConsumedReadCapacityUnits"
  namespace           = "AWS/DynamoDB"
  period               = 300
  statistic           = "Sum"
  threshold           = var.dynamodb_read_capacity_threshold
  alarm_description   = "This metric monitors DynamoDB read capacity for scaling"

  dimensions = {
    TableName = aws_dynamodb_table.reviews.name
  }

  tags = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "dynamodb_write_capacity" {
  count = var.dynamodb_billing_mode == "PROVISIONED" ? 1 : 0

  alarm_name          = "${local.project_name}-dynamodb-write-capacity-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "ConsumedWriteCapacityUnits"
  namespace           = "AWS/DynamoDB"
  period               = 300
  statistic           = "Sum"
  threshold           = var.dynamodb_write_capacity_threshold
  alarm_description   = "This metric monitors DynamoDB write capacity for scaling"

  dimensions = {
    TableName = aws_dynamodb_table.reviews.name
  }

  tags = local.common_tags
}

