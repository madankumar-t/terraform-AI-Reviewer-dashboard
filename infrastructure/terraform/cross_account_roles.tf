# Cross-Account Role Assumption for Multi-Account Access

# Role in Application Account (trusted by Management Account)
resource "aws_iam_role" "cross_account_sso" {
  name = "${local.project_name}-cross-account-sso-${var.environment}"

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
      },
      {
        Effect = "Allow"
        Principal = {
          Federated = "arn:aws:iam::${var.management_account_id}:saml-provider/AzureAD"
        }
        Action = "sts:AssumeRoleWithSAML"
        Condition = {
          StringEquals = {
            "SAML:aud" = "https://signin.aws.amazon.com/saml"
          }
        }
      }
    ]
  })

  tags = local.common_tags
}

# Policy for cross-account access
resource "aws_iam_role_policy" "cross_account_sso" {
  name = "${local.project_name}-cross-account-sso-policy-${var.environment}"
  role = aws_iam_role.cross_account_sso.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:Query",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem"
        ]
        Resource = [
          aws_dynamodb_table.reviews.arn,
          "${aws_dynamodb_table.reviews.arn}/index/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = [
          aws_lambda_function.api_handler.arn,
          aws_lambda_function.ai_reviewer.arn
        ]
      }
    ]
  })
}

# Role for Admin access (cross-account)
resource "aws_iam_role" "cross_account_admin" {
  name = "${local.project_name}-cross-account-admin-${var.environment}"

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
          StringLike = {
            "aws:PrincipalTag/Role" = "Admin"
          }
        }
      }
    ]
  })

  tags = merge(local.common_tags, {
    Role = "Admin"
  })
}

resource "aws_iam_role_policy_attachment" "cross_account_admin" {
  role       = aws_iam_role.cross_account_admin.name
  policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess"
}

# Role for Reviewer access (cross-account)
resource "aws_iam_role" "cross_account_reviewer" {
  name = "${local.project_name}-cross-account-reviewer-${var.environment}"

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
          StringLike = {
            "aws:PrincipalTag/Role" = "Reviewer"
          }
        }
      }
    ]
  })

  tags = merge(local.common_tags, {
    Role = "Reviewer"
  })
}

resource "aws_iam_role_policy" "cross_account_reviewer" {
  name = "${local.project_name}-cross-account-reviewer-policy-${var.environment}"
  role = aws_iam_role.cross_account_reviewer.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:Query",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem"
        ]
        Resource = [
          aws_dynamodb_table.reviews.arn,
          "${aws_dynamodb_table.reviews.arn}/index/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = [
          aws_lambda_function.api_handler.arn,
          aws_lambda_function.pr_review_handler.arn
        ]
      }
    ]
  })
}

# Role for ReadOnly access (cross-account)
resource "aws_iam_role" "cross_account_readonly" {
  name = "${local.project_name}-cross-account-readonly-${var.environment}"

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
          StringLike = {
            "aws:PrincipalTag/Role" = "ReadOnly"
          }
        }
      }
    ]
  })

  tags = merge(local.common_tags, {
    Role = "ReadOnly"
  })
}

resource "aws_iam_role_policy_attachment" "cross_account_readonly" {
  role       = aws_iam_role.cross_account_readonly.name
  policy_arn = "arn:aws:iam::aws:policy/ReadOnlyAccess"
}

