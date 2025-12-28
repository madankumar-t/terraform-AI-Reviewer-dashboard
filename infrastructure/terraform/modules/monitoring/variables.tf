variable "name" {
  description = "Name prefix for resources"
  type        = string
}

variable "lambda_functions" {
  description = "Map of Lambda function names to monitor"
  type        = map(string)
  default     = {}
}

variable "api_gateway_name" {
  description = "API Gateway name"
  type        = string
  default     = ""
}

variable "enable_api_gateway_logs" {
  description = "Enable API Gateway logging"
  type        = bool
  default     = true
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 30
}

variable "lambda_duration_threshold" {
  description = "Lambda duration threshold in milliseconds"
  type        = number
  default     = 5000
}

variable "enable_dashboard" {
  description = "Enable CloudWatch dashboard"
  type        = bool
  default     = true
}

variable "create_sns_topic" {
  description = "Create SNS topic for alerts"
  type        = bool
  default     = false
}

variable "sns_topic_arn" {
  description = "SNS topic ARN for alarm notifications (optional)"
  type        = string
  default     = ""
}

variable "sns_email_subscriptions" {
  description = "List of email addresses for SNS subscriptions"
  type        = list(string)
  default     = []
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}

