resource "aws_iam_role" "lambda_execution_role" {
  name = "${local.project_name}-lambda-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

# VPC Access Policy for Lambda
resource "aws_iam_role_policy" "lambda_vpc_access" {
  name = "${local.project_name}-lambda-vpc-access-${var.environment}"
  role = aws_iam_role.lambda_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ec2:CreateNetworkInterface",
          "ec2:DescribeNetworkInterfaces",
          "ec2:DeleteNetworkInterface",
          "ec2:AssignPrivateIpAddresses",
          "ec2:UnassignPrivateIpAddresses"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy" "lambda_dynamodb" {
  name = "${local.project_name}-lambda-dynamodb-${var.environment}"
  role = aws_iam_role.lambda_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:BatchGetItem",
          "dynamodb:BatchWriteItem"
        ]
        Resource = [
          aws_dynamodb_table.reviews.arn,
          "${aws_dynamodb_table.reviews.arn}/index/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy" "lambda_secrets" {
  name = "${local.project_name}-lambda-secrets-${var.environment}"
  role = aws_iam_role.lambda_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = [
          aws_secretsmanager_secret.openai_api_key.arn,
          aws_secretsmanager_secret.anthropic_api_key.arn,
          aws_secretsmanager_secret.spacelift_webhook_secret.arn,
          aws_secretsmanager_secret.github_webhook_secret.arn
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy" "lambda_invoke" {
  name = "${local.project_name}-lambda-invoke-${var.environment}"
  role = aws_iam_role.lambda_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = [
          aws_lambda_function.ai_reviewer.arn,
          aws_lambda_function.pr_review_handler.arn,
          aws_lambda_function.historical_analysis_handler.arn,
          aws_lambda_function.trend_aggregation_handler.arn
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy" "lambda_bedrock" {
  name = "${local.project_name}-lambda-bedrock-${var.environment}"
  role = aws_iam_role.lambda_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream"
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

resource "aws_iam_role_policy" "lambda_logs" {
  name = "${local.project_name}-lambda-logs-${var.environment}"
  role = aws_iam_role.lambda_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

