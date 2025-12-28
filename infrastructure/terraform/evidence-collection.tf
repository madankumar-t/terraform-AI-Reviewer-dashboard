# Evidence Collection Infrastructure

# S3 Bucket for Evidence Storage
resource "aws_s3_bucket" "evidence" {
  bucket = "${local.project_name}-evidence-${var.environment}-${data.aws_caller_identity.current.account_id}"

  tags = merge(
    local.common_tags,
    {
      Purpose = "Compliance Evidence Storage"
    }
  )
}

# S3 Bucket Versioning
resource "aws_s3_bucket_versioning" "evidence" {
  bucket = aws_s3_bucket.evidence.id

  versioning_configuration {
    status = "Enabled"
  }
}

# S3 Bucket Encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "evidence" {
  bucket = aws_s3_bucket.evidence.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# S3 Bucket Lifecycle Configuration
resource "aws_s3_bucket_lifecycle_configuration" "evidence" {
  bucket = aws_s3_bucket.evidence.id

  rule {
    id     = "transition-to-ia"
    status = "Enabled"

    transition {
      days          = 90
      storage_class = "STANDARD_IA"
    }
  }

  rule {
    id     = "transition-to-glacier"
    status = "Enabled"

    transition {
      days          = 365
      storage_class = "GLACIER"
    }
  }

  rule {
    id     = "delete-old-evidence"
    status = "Enabled"

    expiration {
      days = 2555  # 7 years
    }
  }
}

# S3 Bucket Public Access Block
resource "aws_s3_bucket_public_access_block" "evidence" {
  bucket = aws_s3_bucket.evidence.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Lambda Function for Evidence Collection
resource "aws_lambda_function" "evidence_collector" {
  filename         = data.archive_file.evidence_collector_zip.output_path
  function_name    = "${local.project_name}-evidence-collector-${var.environment}"
  role             = aws_iam_role.evidence_collector.arn
  handler          = "evidence_collector.handler"
  source_code_hash = data.archive_file.evidence_collector_zip.output_base64sha256
  runtime          = "python3.11"
  timeout          = 900  # 15 minutes
  memory_size      = 1024

  environment {
    variables = {
      EVIDENCE_BUCKET = aws_s3_bucket.evidence.id
      TABLE_NAME      = aws_dynamodb_table.reviews.name
      LOG_GROUP_PREFIX = "/aws/lambda/${local.project_name}"
    }
  }

  tags = local.common_tags
}

# Archive for Evidence Collector
data "archive_file" "evidence_collector_zip" {
  type        = "zip"
  source_file = "${path.module}/../lambda/evidence_collector.py"
  output_path = "${path.module}/evidence-collector.zip"
}

# IAM Role for Evidence Collector
resource "aws_iam_role" "evidence_collector" {
  name = "${local.project_name}-evidence-collector-${var.environment}"

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

# IAM Policy for Evidence Collector
resource "aws_iam_role_policy" "evidence_collector" {
  name = "${local.project_name}-evidence-collector-policy-${var.environment}"
  role = aws_iam_role.evidence_collector.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:DescribeLogGroups",
          "logs:FilterLogEvents",
          "logs:GetLogEvents"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:DescribeTable"
        ]
        Resource = [
          aws_dynamodb_table.reviews.arn,
          "${aws_dynamodb_table.reviews.arn}/index/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "iam:ListRoles",
          "iam:GetRole",
          "iam:ListAttachedRolePolicies",
          "iam:GetPolicy",
          "iam:GetPolicyVersion"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "cloudwatch:GetMetricStatistics",
          "cloudwatch:ListMetrics"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.evidence.arn,
          "${aws_s3_bucket.evidence.arn}/*"
        ]
      }
    ]
  })
}

# EventBridge Rule - Daily Evidence Collection
resource "aws_cloudwatch_event_rule" "daily_evidence" {
  name                = "${local.project_name}-daily-evidence-${var.environment}"
  description         = "Trigger daily evidence collection"
  schedule_expression = "cron(0 2 * * ? *)"  # Daily at 2 AM UTC

  tags = local.common_tags
}

resource "aws_cloudwatch_event_target" "daily_evidence" {
  rule      = aws_cloudwatch_event_rule.daily_evidence.name
  target_id = "DailyEvidenceCollection"
  arn       = aws_lambda_function.evidence_collector.arn

  input = jsonencode({
    collection_type = "daily"
  })
}

# EventBridge Rule - Weekly Evidence Collection
resource "aws_cloudwatch_event_rule" "weekly_evidence" {
  name                = "${local.project_name}-weekly-evidence-${var.environment}"
  description         = "Trigger weekly evidence collection"
  schedule_expression = "cron(0 3 ? * SUN *)"  # Weekly on Sunday at 3 AM UTC

  tags = local.common_tags
}

resource "aws_cloudwatch_event_target" "weekly_evidence" {
  rule      = aws_cloudwatch_event_rule.weekly_evidence.name
  target_id = "WeeklyEvidenceCollection"
  arn       = aws_lambda_function.evidence_collector.arn

  input = jsonencode({
    collection_type = "weekly"
  })
}

# EventBridge Rule - Monthly Evidence Collection
resource "aws_cloudwatch_event_rule" "monthly_evidence" {
  name                = "${local.project_name}-monthly-evidence-${var.environment}"
  description         = "Trigger monthly evidence collection"
  schedule_expression = "cron(0 4 1 * ? *)"  # Monthly on 1st at 4 AM UTC

  tags = local.common_tags
}

resource "aws_cloudwatch_event_target" "monthly_evidence" {
  rule      = aws_cloudwatch_event_rule.monthly_evidence.name
  target_id = "MonthlyEvidenceCollection"
  arn       = aws_lambda_function.evidence_collector.arn

  input = jsonencode({
    collection_type = "monthly"
  })
}

# Lambda Permissions
resource "aws_lambda_permission" "daily_evidence_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridgeDaily"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.evidence_collector.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_evidence.arn
}

resource "aws_lambda_permission" "weekly_evidence_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridgeWeekly"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.evidence_collector.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.weekly_evidence.arn
}

resource "aws_lambda_permission" "monthly_evidence_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridgeMonthly"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.evidence_collector.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.monthly_evidence.arn
}

