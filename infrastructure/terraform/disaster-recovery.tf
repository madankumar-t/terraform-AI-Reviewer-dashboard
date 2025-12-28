# Disaster Recovery Configuration

# DynamoDB Point-in-Time Recovery
resource "aws_dynamodb_table" "reviews" {
  # ... existing configuration ...
  
  point_in_time_recovery {
    enabled = true
  }

  # Backup configuration
  server_side_encryption {
    enabled     = true
    kms_key_arn = aws_kms_key.dynamodb.arn
  }
}

# KMS Key for DynamoDB Encryption
resource "aws_kms_key" "dynamodb" {
  description             = "KMS key for DynamoDB encryption"
  deletion_window_in_days = 10
  enable_key_rotation     = true

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "Enable IAM User Permissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "Allow DynamoDB"
        Effect = "Allow"
        Principal = {
          Service = "dynamodb.amazonaws.com"
        }
        Action = [
          "kms:Decrypt",
          "kms:Encrypt",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*",
          "kms:DescribeKey"
        ]
        Resource = "*"
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_kms_alias" "dynamodb" {
  name          = "alias/${local.project_name}-dynamodb-${var.environment}"
  target_key_id = aws_kms_key.dynamodb.key_id
}

# DynamoDB Continuous Backups
resource "aws_dynamodb_continuous_backup" "reviews" {
  table_name = aws_dynamodb_table.reviews.name
}

# DynamoDB On-Demand Backup
resource "aws_dynamodb_table" "reviews_backup" {
  count = var.enable_scheduled_backups ? 1 : 0

  # This would be a separate backup table or use AWS Backup service
  # For now, we use AWS Backup service (see below)
}

# AWS Backup Plan
resource "aws_backup_plan" "main" {
  count = var.enable_aws_backup ? 1 : 0

  name = "${local.project_name}-backup-plan-${var.environment}"

  rule {
    rule_name         = "daily_backup"
    target_vault_name = aws_backup_vault.main[0].name
    schedule          = "cron(0 2 * * ? *)"  # Daily at 2 AM UTC

    lifecycle {
      cold_storage_after = 30
      delete_after       = 90
    }
  }

  rule {
    rule_name         = "weekly_backup"
    target_vault_name = aws_backup_vault.main[0].name
    schedule          = "cron(0 3 ? * SUN *)"  # Weekly on Sunday at 3 AM UTC

    lifecycle {
      cold_storage_after = 90
      delete_after       = 365
    }
  }

  tags = local.common_tags
}

# AWS Backup Vault
resource "aws_backup_vault" "main" {
  count = var.enable_aws_backup ? 1 : 0

  name        = "${local.project_name}-backup-vault-${var.environment}"
  kms_key_arn = aws_kms_key.backup[0].arn

  tags = local.common_tags
}

# KMS Key for Backup Encryption
resource "aws_kms_key" "backup" {
  count = var.enable_aws_backup ? 1 : 0

  description             = "KMS key for AWS Backup encryption"
  deletion_window_in_days = 10
  enable_key_rotation     = true

  tags = local.common_tags
}

# Backup Selection - DynamoDB
resource "aws_backup_selection" "dynamodb" {
  count = var.enable_aws_backup ? 1 : 0

  name         = "${local.project_name}-dynamodb-backup-selection"
  iam_role_arn = aws_iam_role.backup[0].arn
  plan_id      = aws_backup_plan.main[0].id

  resources = [
    aws_dynamodb_table.reviews.arn
  ]
}

# Backup Selection - Lambda
resource "aws_backup_selection" "lambda" {
  count = var.enable_aws_backup ? 1 : 0

  name         = "${local.project_name}-lambda-backup-selection"
  iam_role_arn = aws_iam_role.backup[0].arn
  plan_id      = aws_backup_plan.main[0].id

  resources = [
    aws_lambda_function.api_handler.arn,
    aws_lambda_function.ai_reviewer.arn
  ]
}

# IAM Role for AWS Backup
resource "aws_iam_role" "backup" {
  count = var.enable_aws_backup ? 1 : 0

  name = "${local.project_name}-backup-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "backup.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "backup" {
  count = var.enable_aws_backup ? 1 : 0

  role       = aws_iam_role.backup[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSBackupServiceRolePolicyForBackup"
}

# S3 Cross-Region Replication (for frontend assets)
resource "aws_s3_bucket_replication_configuration" "frontend" {
  count = var.enable_cross_region_replication ? 1 : 0

  role   = aws_iam_role.s3_replication[0].arn
  bucket = module.frontend.s3_bucket_id

  rule {
    id     = "replicate-to-${var.dr_region}"
    status = "Enabled"

    destination {
      bucket        = aws_s3_bucket.frontend_dr[0].arn
      storage_class = "STANDARD_IA"
    }
  }
}

# S3 Bucket in DR Region
resource "aws_s3_bucket" "frontend_dr" {
  count = var.enable_cross_region_replication ? 1 : 0

  provider = aws.dr_region
  bucket   = "${local.project_name}-frontend-${var.environment}-dr-${data.aws_caller_identity.current.account_id}"

  tags = merge(
    local.common_tags,
    {
      Purpose = "Disaster Recovery"
    }
  )
}

# IAM Role for S3 Replication
resource "aws_iam_role" "s3_replication" {
  count = var.enable_cross_region_replication ? 1 : 0

  name = "${local.project_name}-s3-replication-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "s3.amazonaws.com"
        }
      }
    ]
  })

  tags = local.common_tags
}

# Provider for DR Region
provider "aws" {
  alias  = "dr_region"
  region = var.dr_region
}

# CloudWatch Alarm for Backup Failures
resource "aws_cloudwatch_metric_alarm" "backup_failure" {
  count = var.enable_aws_backup ? 1 : 0

  alarm_name          = "${local.project_name}-backup-failure-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "NumberOfBackupJobsFailed"
  namespace           = "AWS/Backup"
  period               = 300
  statistic           = "Sum"
  threshold           = 0
  alarm_description   = "This metric monitors backup job failures"

  tags = local.common_tags
}

