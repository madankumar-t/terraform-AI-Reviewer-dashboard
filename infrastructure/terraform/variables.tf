variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "openai_api_key" {
  description = "OpenAI API key (stored in Secrets Manager)"
  type        = string
  sensitive   = true
  default     = ""
}

variable "anthropic_api_key" {
  description = "Anthropic API key (stored in Secrets Manager)"
  type        = string
  sensitive   = true
  default     = ""
}

variable "spacelift_webhook_secret" {
  description = "Spacelift webhook secret for validation"
  type        = string
  sensitive   = true
  default     = ""
}

variable "github_webhook_secret" {
  description = "GitHub webhook secret for validation"
  type        = string
  sensitive   = true
  default     = ""
}

variable "allowed_origins" {
  description = "Allowed CORS origins for API Gateway"
  type        = list(string)
  default     = ["*"]
}

variable "custom_domain_name" {
  description = "Custom domain name for API Gateway (optional)"
  type        = string
  default     = ""
}

variable "application_account_id" {
  description = "Application account ID for SSO assignments"
  type        = string
  default     = ""
}

variable "azure_admin_group_id" {
  description = "Azure Entra ID admin group object ID"
  type        = string
  default     = ""
}

variable "azure_reviewer_group_id" {
  description = "Azure Entra ID reviewer group object ID"
  type        = string
  default     = ""
}

variable "azure_readonly_group_id" {
  description = "Azure Entra ID read-only group object ID"
  type        = string
  default     = ""
}

variable "azure_entra_metadata_xml" {
  description = "Azure Entra ID SAML metadata XML"
  type        = string
  sensitive   = true
  default     = ""
}

variable "cognito_callback_urls" {
  description = "Cognito OAuth callback URLs"
  type        = list(string)
  default     = ["http://localhost:3000/auth/callback"]
}

variable "cognito_logout_urls" {
  description = "Cognito OAuth logout URLs"
  type        = list(string)
  default     = ["http://localhost:3000"]
}

variable "management_account_id" {
  description = "Management account ID for cross-account access"
  type        = string
  default     = ""
}

variable "cross_account_external_id" {
  description = "External ID for cross-account role assumption"
  type        = string
  sensitive   = true
  default     = ""
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.11.0/24", "10.0.12.0/24"]
}

variable "frontend_custom_domain" {
  description = "Custom domain for frontend (optional)"
  type        = string
  default     = ""
}

variable "frontend_acm_certificate_arn" {
  description = "ACM certificate ARN for frontend custom domain"
  type        = string
  default     = ""
}

variable "enable_frontend_waf" {
  description = "Enable WAF for CloudFront"
  type        = bool
  default     = true
}

variable "cloudfront_price_class" {
  description = "CloudFront price class"
  type        = string
  default     = "PriceClass_100"
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 30
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

# Rate Limiting
variable "api_throttle_burst_limit" {
  description = "API Gateway throttle burst limit"
  type        = number
  default     = 100
}

variable "api_throttle_rate_limit" {
  description = "API Gateway throttle rate limit"
  type        = number
  default     = 50
}

# WAF
variable "waf_rate_limit" {
  description = "WAF rate limit (requests per 5 minutes)"
  type        = number
  default     = 2000
}

variable "blocked_countries" {
  description = "List of country codes to block"
  type        = list(string)
  default     = []
}

variable "allowed_ip_ranges" {
  description = "List of IP ranges to allow"
  type        = list(string)
  default     = []
}

# Secrets Rotation
variable "enable_secrets_rotation" {
  description = "Enable automatic secrets rotation"
  type        = bool
  default     = true
}

variable "secrets_rotation_days" {
  description = "Number of days between secret rotations"
  type        = number
  default     = 30
}

# Disaster Recovery
variable "enable_aws_backup" {
  description = "Enable AWS Backup service"
  type        = bool
  default     = true
}

variable "enable_scheduled_backups" {
  description = "Enable scheduled backups"
  type        = bool
  default     = true
}

variable "enable_cross_region_replication" {
  description = "Enable cross-region replication for S3"
  type        = bool
  default     = false
}

variable "dr_region" {
  description = "Disaster recovery region"
  type        = string
  default     = "us-west-2"
}

# Cost Optimization
variable "dynamodb_billing_mode" {
  description = "DynamoDB billing mode (PAY_PER_REQUEST or PROVISIONED)"
  type        = string
  default     = "PAY_PER_REQUEST"
}

variable "dynamodb_min_read_capacity" {
  description = "Minimum DynamoDB read capacity (for provisioned mode)"
  type        = number
  default     = 5
}

variable "dynamodb_max_read_capacity" {
  description = "Maximum DynamoDB read capacity (for provisioned mode)"
  type        = number
  default     = 100
}

variable "dynamodb_min_write_capacity" {
  description = "Minimum DynamoDB write capacity (for provisioned mode)"
  type        = number
  default     = 5
}

variable "dynamodb_max_write_capacity" {
  description = "Maximum DynamoDB write capacity (for provisioned mode)"
  type        = number
  default     = 100
}

variable "dynamodb_read_capacity_threshold" {
  description = "DynamoDB read capacity threshold for alarms"
  type        = number
  default     = 80
}

variable "dynamodb_write_capacity_threshold" {
  description = "DynamoDB write capacity threshold for alarms"
  type        = number
  default     = 80
}

variable "use_single_nat_gateway" {
  description = "Use single NAT Gateway for cost savings (reduces HA)"
  type        = bool
  default     = false
}

variable "enable_cost_anomaly_detection" {
  description = "Enable AWS Cost Anomaly Detection"
  type        = bool
  default     = true
}

variable "enable_budget_alerts" {
  description = "Enable AWS Budget alerts"
  type        = bool
  default     = true
}

variable "monthly_budget_limit" {
  description = "Monthly budget limit in USD"
  type        = number
  default     = 500
}

variable "budget_alert_emails" {
  description = "Email addresses for budget alerts"
  type        = list(string)
  default     = []
}

# Scaling
variable "enable_provisioned_concurrency" {
  description = "Enable Lambda provisioned concurrency"
  type        = bool
  default     = false
}

variable "provisioned_concurrency_count" {
  description = "Number of provisioned concurrent executions"
  type        = number
  default     = 2
}

variable "lambda_reserved_concurrency" {
  description = "Map of Lambda function names to reserved concurrency limits"
  type        = map(number)
  default     = {}
}

variable "lambda_provisioned_concurrency" {
  description = "Map of Lambda function names to provisioned concurrency"
  type        = map(number)
  default     = {}
}

variable "lambda_scaling_alarms" {
  description = "Map of Lambda function names to concurrency thresholds for scaling alarms"
  type        = map(number)
  default     = {}
}

variable "enable_api_gateway_auto_scaling" {
  description = "Enable API Gateway auto-scaling"
  type        = bool
  default     = false
}

variable "api_gateway_min_capacity" {
  description = "Minimum API Gateway capacity"
  type        = number
  default     = 10
}

variable "api_gateway_max_capacity" {
  description = "Maximum API Gateway capacity"
  type        = number
  default     = 1000
}

variable "enable_step_functions" {
  description = "Enable Step Functions for long-running processes"
  type        = bool
  default     = false
}

