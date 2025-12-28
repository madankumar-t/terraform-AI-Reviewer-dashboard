# Terraform Infrastructure - Complete Platform Deployment

## Overview

Complete Terraform configuration for deploying the Terraform + Spacelift AI Reviewer platform with multi-account support, VPCs, API Gateway, Lambda, DynamoDB, CloudFront, S3, Bedrock access, IAM, and monitoring.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    MANAGEMENT ACCOUNT                         │
│  - IAM Identity Center                                       │
│  - SSO Configuration                                         │
└─────────────────────────────────────────────────────────────┘
                            │
                            │
┌─────────────────────────────────────────────────────────────┐
│                 APPLICATION ACCOUNT                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  VPC (Private Subnets)                               │   │
│  │  - Lambda Functions                                  │   │
│  │  - VPC Endpoints (Bedrock, DynamoDB, S3)             │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  API Gateway (Public)                                 │   │
│  │  - JWT Authorizer                                     │   │
│  │  - Lambda Integrations                                │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  CloudFront + S3 (Frontend)                          │   │
│  │  - Static Assets                                     │   │
│  │  - WAF Protection                                    │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  DynamoDB (Single Table Design)                      │   │
│  │  - Versioned Reviews                                 │   │
│  │  - GSIs for Queries                                  │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  CloudWatch (Monitoring)                            │   │
│  │  - Logs                                             │   │
│  │  - Alarms                                           │   │
│  │  - Dashboards                                       │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Prerequisites

1. **AWS CLI** configured with appropriate credentials
2. **Terraform** >= 1.5.0
3. **S3 Bucket** for remote state (or use remote-state.tf to create)
4. **DynamoDB Table** for state locking (or use remote-state.tf to create)
5. **AWS Account** with appropriate permissions

## Setup

### 1. Initialize Remote State

First, create the remote state infrastructure:

```bash
# Option 1: Use existing S3 bucket
# Update backend.tf with your bucket details

# Option 2: Create state bucket (run once)
# Uncomment resources in remote-state.tf and run:
terraform init
terraform apply -target=aws_s3_bucket.terraform_state
terraform apply -target=aws_dynamodb_table.terraform_state_lock
```

### 2. Configure Backend

Copy `backend.hcl.example` to `backend.hcl` and update with your values:

```hcl
bucket         = "terraform-state-YOUR-ACCOUNT-ID-REGION"
key            = "terraform-spacelift-ai-reviewer/terraform.tfstate"
region         = "us-east-1"
dynamodb_table = "terraform-state-lock"
encrypt        = true
```

### 3. Configure Variables

Copy `terraform.tfvars.example` to `terraform.tfvars` and update:

```hcl
aws_region = "us-east-1"
environment = "prod"

# VPC Configuration
vpc_cidr = "10.0.0.0/16"
public_subnet_cidrs = ["10.0.1.0/24", "10.0.2.0/24"]
private_subnet_cidrs = ["10.0.11.0/24", "10.0.12.0/24"]

# Multi-Account (if applicable)
management_account_id = "123456789012"
application_account_id = "987654321098"

# Secrets (stored in Secrets Manager)
openai_api_key = "sk-..."
anthropic_api_key = "sk-ant-..."
spacelift_webhook_secret = "secret"
github_webhook_secret = "secret"

# Frontend
frontend_custom_domain = "reviewer.example.com"
frontend_acm_certificate_arn = "arn:aws:acm:..."

# Monitoring
log_retention_days = 30
create_sns_topic = true
sns_email_subscriptions = ["admin@example.com"]
```

### 4. Initialize Terraform

```bash
terraform init -backend-config=backend.hcl
```

### 5. Plan Deployment

```bash
terraform plan
```

### 6. Deploy

```bash
terraform apply
```

## Module Structure

```
terraform/
├── modules/
│   ├── vpc/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── frontend/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── spa-routing.js
│   └── monitoring/
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
├── main.tf
├── backend.tf
├── remote-state.tf
├── vpc.tf
├── frontend.tf
├── monitoring.tf
├── security_groups.tf
├── multi-account.tf
└── ... (existing files)
```

## Key Features

### ✅ Multi-Account Support
- Management account configuration
- Cross-account role assumptions
- IAM Identity Center integration

### ✅ VPC Configuration
- Public and private subnets
- NAT Gateways
- VPC Endpoints (S3, DynamoDB, Bedrock)
- VPC Flow Logs
- Security groups

### ✅ Lambda Functions
- VPC configuration for private access
- Security groups
- IAM roles with least privilege
- Environment variables
- CloudWatch logging

### ✅ Frontend (CloudFront + S3)
- S3 bucket with versioning and encryption
- CloudFront distribution
- WAF protection
- SPA routing
- Custom domain support

### ✅ Monitoring
- CloudWatch Logs
- CloudWatch Alarms
- CloudWatch Dashboard
- SNS notifications

### ✅ Security
- Encryption at rest and in transit
- VPC isolation
- Security groups
- IAM least privilege
- WAF protection

## Outputs

After deployment, key outputs include:

- API Gateway URL
- CloudFront distribution URL
- DynamoDB table name
- Lambda function ARNs
- VPC IDs and subnet IDs

View all outputs:

```bash
terraform output
```

## Destroy

To destroy all resources:

```bash
terraform destroy
```

**Warning**: This will delete all resources. Ensure you have backups of important data.

## Troubleshooting

### State Lock Issues

If you encounter state lock issues:

```bash
# Check lock
aws dynamodb get-item \
  --table-name terraform-state-lock \
  --key '{"LockID":{"S":"..."}}'

# Force unlock (use with caution)
terraform force-unlock LOCK_ID
```

### VPC Endpoint Issues

Ensure Lambda functions have proper security group rules to access VPC endpoints.

### Bedrock Access

Ensure Bedrock models are enabled in your AWS account:
- Go to AWS Bedrock console
- Enable required models (Claude 3.5 Sonnet, Claude 3 Opus, Llama 3 70B)

## Best Practices

1. **Use Remote State**: Always use S3 backend for state
2. **Enable Encryption**: Use KMS for state encryption
3. **Version Control**: Never commit `.tfvars` files
4. **State Locking**: Always use DynamoDB for state locking
5. **Modular Design**: Use modules for reusable components
6. **Tagging**: Consistent tagging for cost tracking
7. **Least Privilege**: IAM roles with minimal permissions
8. **Monitoring**: Enable CloudWatch logs and alarms

## Cost Optimization

- Use NAT Gateway only when needed
- Choose appropriate CloudFront price class
- Set appropriate log retention periods
- Use provisioned capacity for DynamoDB (if predictable load)
- Enable S3 lifecycle policies for old logs

## Security Considerations

- All secrets stored in AWS Secrets Manager
- VPC isolation for Lambda functions
- Private endpoints for AWS services
- WAF protection for CloudFront
- Encryption everywhere (S3, DynamoDB, CloudWatch)
- IAM roles with least privilege
- Security groups with minimal rules

## Support

For issues or questions, refer to:
- AWS Well-Architected Framework
- Terraform AWS Provider documentation
- Project documentation in `/docs`

