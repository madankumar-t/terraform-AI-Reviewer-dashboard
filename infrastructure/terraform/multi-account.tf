# Multi-Account Configuration
# This file defines resources that need to be aware of multiple accounts

# Data sources for account IDs
data "aws_caller_identity" "current" {}

variable "management_account_id" {
  description = "Management account ID"
  type        = string
  default     = ""
}

variable "shared_services_account_id" {
  description = "Shared services account ID"
  type        = string
  default     = ""
}

variable "application_account_id" {
  description = "Application account ID (current account)"
  type        = string
  default     = ""
}

# Cross-Account IAM Role for Management Account Access
resource "aws_iam_role" "cross_account_management" {
  count = var.management_account_id != "" ? 1 : 0

  name = "${local.project_name}-cross-account-management-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${var.management_account_id}:root"
        }
        Action = "sts:AssumeRole"
        Condition = {
          StringEquals = {
            "sts:ExternalId" = var.cross_account_external_id
          }
        }
      }
    ]
  })

  tags = local.common_tags
}

# Policy for cross-account access (read-only for management)
resource "aws_iam_role_policy" "cross_account_management" {
  count = var.management_account_id != "" ? 1 : 0

  name = "${local.project_name}-cross-account-management-policy-${var.environment}"
  role = aws_iam_role.cross_account_management[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "cloudwatch:GetMetricStatistics",
          "cloudwatch:ListMetrics",
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams",
          "logs:GetLogEvents",
          "dynamodb:DescribeTable",
          "dynamodb:ListTables"
        ]
        Resource = "*"
      }
    ]
  })
}

# Resource Sharing (if using AWS Resource Access Manager)
# Note: This requires RAM to be enabled and proper permissions

# VPC Peering (if needed between accounts)
# Note: VPC peering should be configured separately or via AWS Organizations

