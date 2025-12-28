output "sns_topic_arn" {
  description = "SNS topic ARN for alerts"
  value       = var.create_sns_topic ? aws_sns_topic.alerts[0].arn : var.sns_topic_arn
}

output "dashboard_url" {
  description = "CloudWatch dashboard URL"
  value       = var.enable_dashboard ? "https://${data.aws_region.current.name}.console.aws.amazon.com/cloudwatch/home?region=${data.aws_region.current.name}#dashboards:name=${aws_cloudwatch_dashboard.main[0].dashboard_name}" : ""
}

