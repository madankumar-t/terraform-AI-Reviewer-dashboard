# EventBridge rule for scheduled trend aggregation

resource "aws_cloudwatch_event_rule" "trend_aggregation_schedule" {
  name                = "${local.project_name}-trend-aggregation-${var.environment}"
  description         = "Daily trend aggregation schedule"
  schedule_expression = "cron(0 2 * * ? *)"  # Run daily at 2 AM UTC

  tags = local.common_tags
}

resource "aws_cloudwatch_event_target" "trend_aggregation_target" {
  rule      = aws_cloudwatch_event_rule.trend_aggregation_schedule.name
  target_id = "TrendAggregationTarget"
  arn       = aws_lambda_function.trend_aggregation_handler.arn
}

