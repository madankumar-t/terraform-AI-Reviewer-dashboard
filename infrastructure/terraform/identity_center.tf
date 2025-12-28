# AWS IAM Identity Center Configuration
# Note: IAM Identity Center must be enabled manually in the AWS Console first
# This configuration assumes it's already enabled

# Data source to get existing IAM Identity Center instance
data "aws_ssoadmin_instances" "main" {}

locals {
  sso_instance_arn = tolist(data.aws_ssoadmin_instances.main.arns)[0]
}

# Permission Sets
resource "aws_ssoadmin_permission_set" "admin" {
  name             = "AdminAccess"
  description      = "Full administrative access"
  instance_arn     = local.sso_instance_arn
  session_duration = "PT1H"

  tags = local.common_tags
}

resource "aws_ssoadmin_permission_set" "reviewer" {
  name             = "ReviewerAccess"
  description      = "Reviewer access - can create and view reviews"
  instance_arn     = local.sso_instance_arn
  session_duration = "PT1H"

  tags = local.common_tags
}

resource "aws_ssoadmin_permission_set" "readonly" {
  name             = "ReadOnlyAccess"
  description      = "Read-only access to reviews and analytics"
  instance_arn     = local.sso_instance_arn
  session_duration = "PT1H"

  tags = local.common_tags
}

# Admin Permission Set Policy
resource "aws_ssoadmin_managed_policy_attachment" "admin" {
  instance_arn       = local.sso_instance_arn
  managed_policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess"
  permission_set_arn = aws_ssoadmin_permission_set.admin.arn
}

# Reviewer Permission Set Policy (Custom)
resource "aws_ssoadmin_permission_set_inline_policy" "reviewer" {
  instance_arn       = local.sso_instance_arn
  permission_set_arn = aws_ssoadmin_permission_set.reviewer.arn

  inline_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:Query",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "lambda:InvokeFunction"
        ]
        Resource = [
          aws_dynamodb_table.reviews.arn,
          "${aws_dynamodb_table.reviews.arn}/index/*",
          aws_lambda_function.api_handler.arn,
          aws_lambda_function.pr_review_handler.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel"
        ]
        Resource = [
          "arn:aws:bedrock:${var.aws_region}::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0",
          "arn:aws:bedrock:${var.aws_region}::foundation-model/anthropic.claude-3-opus-20240229-v1:0",
          "arn:aws:bedrock:${var.aws_region}::foundation-model/meta.llama3-70b-instruct-v1:0"
        ]
      }
    ]
  })
}

# ReadOnly Permission Set Policy
resource "aws_ssoadmin_managed_policy_attachment" "readonly" {
  instance_arn       = local.sso_instance_arn
  managed_policy_arn = "arn:aws:iam::aws:policy/ReadOnlyAccess"
  permission_set_arn = aws_ssoadmin_permission_set.readonly.arn
}

# Account Assignment - Admin (Management Account)
resource "aws_ssoadmin_account_assignment" "admin_management" {
  count            = var.azure_admin_group_id != "" ? 1 : 0
  instance_arn      = local.sso_instance_arn
  permission_set_arn = aws_ssoadmin_permission_set.admin.arn

  principal_id   = var.azure_admin_group_id
  principal_type = "GROUP"

  target_id   = data.aws_caller_identity.current.account_id
  target_type = "AWS_ACCOUNT"
}

# Account Assignment - Reviewer (Application Account)
resource "aws_ssoadmin_account_assignment" "reviewer_app" {
  count            = var.azure_reviewer_group_id != "" && var.application_account_id != "" ? 1 : 0
  instance_arn     = local.sso_instance_arn
  permission_set_arn = aws_ssoadmin_permission_set.reviewer.arn

  principal_id   = var.azure_reviewer_group_id
  principal_type  = "GROUP"

  target_id   = var.application_account_id
  target_type = "AWS_ACCOUNT"
}

# Account Assignment - ReadOnly (Application Account)
resource "aws_ssoadmin_account_assignment" "readonly_app" {
  count            = var.azure_readonly_group_id != "" && var.application_account_id != "" ? 1 : 0
  instance_arn     = local.sso_instance_arn
  permission_set_arn = aws_ssoadmin_permission_set.readonly.arn

  principal_id   = var.azure_readonly_group_id
  principal_type  = "GROUP"

  target_id   = var.application_account_id
  target_type = "AWS_ACCOUNT"
}

data "aws_caller_identity" "current" {}

