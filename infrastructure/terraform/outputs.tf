output "api_gateway_url" {
  description = "API Gateway endpoint URL"
  value       = aws_apigatewayv2_api.main.api_endpoint
}

output "dynamodb_table_name" {
  description = "DynamoDB table name"
  value       = aws_dynamodb_table.reviews.name
}

output "lambda_function_names" {
  description = "Lambda function names"
  value = {
    api_handler              = aws_lambda_function.api_handler.function_name
    ai_reviewer              = aws_lambda_function.ai_reviewer.function_name
    webhook_handler          = aws_lambda_function.webhook_handler.function_name
    pr_review_handler        = aws_lambda_function.pr_review_handler.function_name
    github_webhook_handler   = aws_lambda_function.github_webhook_handler.function_name
    historical_analysis_handler = aws_lambda_function.historical_analysis_handler.function_name
    trend_aggregation_handler = aws_lambda_function.trend_aggregation_handler.function_name
  }
}

output "api_endpoint" {
  description = "Full API endpoint URL"
  value       = "${aws_apigatewayv2_api.main.api_endpoint}/${aws_apigatewayv2_stage.default.name}"
}

output "cloudfront_url" {
  description = "CloudFront distribution URL"
  value       = module.frontend.cloudfront_url
}

output "cloudfront_domain" {
  description = "CloudFront distribution domain name"
  value       = module.frontend.cloudfront_domain_name
}

output "s3_bucket_name" {
  description = "S3 bucket name for frontend"
  value       = module.frontend.s3_bucket_id
}

output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = module.vpc.private_subnet_ids
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = module.vpc.public_subnet_ids
}

output "dynamodb_table_arn" {
  description = "DynamoDB table ARN"
  value       = aws_dynamodb_table.reviews.arn
}

output "sns_topic_arn" {
  description = "SNS topic ARN for alerts"
  value       = module.monitoring.sns_topic_arn
}

output "cloudwatch_dashboard_url" {
  description = "CloudWatch dashboard URL"
  value       = module.monitoring.dashboard_url
}

