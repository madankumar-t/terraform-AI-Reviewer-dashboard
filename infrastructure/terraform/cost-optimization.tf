# Cost Optimization Configuration

# DynamoDB Auto-Scaling (if using provisioned capacity)
resource "aws_appautoscaling_target" "dynamodb_read" {
  count = var.dynamodb_billing_mode == "PROVISIONED" ? 1 : 0

  max_capacity       = var.dynamodb_max_read_capacity
  min_capacity       = var.dynamodb_min_read_capacity
  resource_id        = "table/${aws_dynamodb_table.reviews.name}"
  scalable_dimension = "dynamodb:table:ReadCapacityUnits"
  service_namespace  = "dynamodb"
}

resource "aws_appautoscaling_policy" "dynamodb_read" {
  count = var.dynamodb_billing_mode == "PROVISIONED" ? 1 : 0

  name               = "${local.project_name}-dynamodb-read-scaling-${var.environment}"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.dynamodb_read[0].resource_id
  scalable_dimension = aws_appautoscaling_target.dynamodb_read[0].scalable_dimension
  service_namespace  = aws_appautoscaling_target.dynamodb_read[0].service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "DynamoDBReadCapacityUtilization"
    }
    target_value = 70.0
  }
}

resource "aws_appautoscaling_target" "dynamodb_write" {
  count = var.dynamodb_billing_mode == "PROVISIONED" ? 1 : 0

  max_capacity       = var.dynamodb_max_write_capacity
  min_capacity       = var.dynamodb_min_write_capacity
  resource_id        = "table/${aws_dynamodb_table.reviews.name}"
  scalable_dimension = "dynamodb:table:WriteCapacityUnits"
  service_namespace  = "dynamodb"
}

resource "aws_appautoscaling_policy" "dynamodb_write" {
  count = var.dynamodb_billing_mode == "PROVISIONED" ? 1 : 0

  name               = "${local.project_name}-dynamodb-write-scaling-${var.environment}"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.dynamodb_write[0].resource_id
  scalable_dimension = aws_appautoscaling_target.dynamodb_write[0].scalable_dimension
  service_namespace  = aws_appautoscaling_target.dynamodb_write[0].service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "DynamoDBWriteCapacityUtilization"
    }
    target_value = 70.0
  }
}

# S3 Lifecycle Policies for Cost Optimization
resource "aws_s3_bucket_lifecycle_configuration" "frontend" {
  bucket = module.frontend.s3_bucket_id

  rule {
    id     = "transition-to-ia"
    status = "Enabled"

    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }
  }

  rule {
    id     = "transition-to-glacier"
    status = "Enabled"

    transition {
      days          = 90
      storage_class = "GLACIER"
    }
  }

  rule {
    id     = "delete-old-versions"
    status = "Enabled"

    noncurrent_version_expiration {
      noncurrent_days = 30
    }
  }
}

# CloudWatch Logs Retention (Cost Optimization)
resource "aws_cloudwatch_log_group" "lambda_logs" {
  for_each = toset([
    "api-handler",
    "ai-reviewer",
    "pr-review-handler",
    "webhook-handler",
    "github-webhook-handler",
    "historical-analysis",
    "trend-aggregation",
    "jwt-authorizer"
  ])

  name              = "/aws/lambda/${local.project_name}-${each.key}-${var.environment}"
  retention_in_days = var.log_retention_days

  tags = local.common_tags
}

# Cost Anomaly Detection
resource "aws_ce_anomaly_detector" "main" {
  count = var.enable_cost_anomaly_detection ? 1 : 0

  name              = "${local.project_name}-cost-anomaly-${var.environment}"
  monitor_type      = "DIMENSIONAL"
  monitor_dimension = "SERVICE"

  specification = jsonencode({
    Dimension = "SERVICE"
    MatchOptions = ["EQUALS"]
    Values = [
      "Amazon DynamoDB",
      "AWS Lambda",
      "Amazon API Gateway",
      "Amazon CloudFront",
      "Amazon S3"
    ]
  })
}

# Budget Alert
resource "aws_budgets_budget" "main" {
  count = var.enable_budget_alerts ? 1 : 0

  name              = "${local.project_name}-budget-${var.environment}"
  budget_type       = "COST"
  limit_amount      = var.monthly_budget_limit
  limit_unit        = "USD"
  time_period_start = "2024-01-01_00:00"
  time_unit         = "MONTHLY"

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                 = 80
    threshold_type            = "PERCENTAGE"
    notification_type         = "ACTUAL"
    subscriber_email_addresses = var.budget_alert_emails
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                 = 100
    threshold_type            = "PERCENTAGE"
    notification_type         = "ACTUAL"
    subscriber_email_addresses = var.budget_alert_emails
  }
}

# Lambda Reserved Concurrency (Cost Control)
resource "aws_lambda_function_event_invoke_config" "cost_control" {
  for_each = {
    api_handler = aws_lambda_function.api_handler.function_name
    ai_reviewer = aws_lambda_function.ai_reviewer.function_name
  }

  function_name = each.value

  maximum_retry_attempts = 2
  maximum_event_age_in_seconds = 60
}

# NAT Gateway Cost Optimization (Use single NAT for cost savings)
# Note: This reduces high availability but saves costs
resource "aws_nat_gateway" "single" {
  count = var.use_single_nat_gateway ? 1 : length(module.vpc.private_subnet_ids)

  allocation_id = aws_eip.nat[count.index].id
  subnet_id      = module.vpc.public_subnet_ids[0]

  tags = merge(
    local.common_tags,
    {
      Name = "${local.project_name}-nat-${var.environment}"
    }
  )

  depends_on = [aws_internet_gateway.main]
}

