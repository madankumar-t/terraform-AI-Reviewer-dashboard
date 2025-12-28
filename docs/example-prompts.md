# Example AI Prompts

This document contains example prompts used by the AI reviewer service.

## Main Review Prompt

The system uses a comprehensive prompt that instructs the AI to analyze Terraform code across three dimensions: security, cost, and reliability.

### Base Prompt Structure

```
Analyze the following Terraform code for security, cost, and reliability issues.

[Spacelift Context Information]

Terraform Code:
```hcl
[TERRAFORM_CODE_HERE]
```

Provide a comprehensive analysis in the following JSON format:
{
  "security_analysis": {...},
  "cost_analysis": {...},
  "reliability_analysis": {...},
  "overall_risk_score": 0.5,
  "fix_suggestions": [...],
  "review_metadata": {...}
}
```

## Example Terraform Code Input

```hcl
resource "aws_s3_bucket" "example" {
  bucket = "my-public-bucket"
  
  tags = {
    Name = "Example"
  }
}

resource "aws_s3_bucket_public_access_block" "example" {
  bucket = aws_s3_bucket.example.id
  # Missing public access block settings
}

resource "aws_iam_role" "example" {
  name = "example-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "example" {
  name = "example-policy"
  role = aws_iam_role.example.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = "*"
        Resource = "*"
      }
    ]
  })
}

resource "aws_instance" "example" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "m5.24xlarge"  # Over-provisioned
  
  tags = {
    Name = "Example"
  }
}
```

## Expected AI Response

The AI should identify:
- **Security**: Public S3 bucket, overly permissive IAM policy
- **Cost**: Over-provisioned instance type
- **Reliability**: Missing backups, no health checks

## Context-Aware Prompts

When Spacelift context is available, the prompt includes:

```
Spacelift Run Context:
- Run ID: run-abc123
- Stack: production-stack
- Previous Run Status: SUCCESS
- Changed Files: main.tf, variables.tf
- Commit SHA: abc123def456
- Branch: main
```

This helps the AI understand:
- What changed in this run
- Historical context
- Deployment environment

## Prompt Variations

### Security-Focused Review
```
Focus specifically on security vulnerabilities:
- Exposed credentials
- Missing encryption
- Overly permissive IAM policies
- Public resources
- Missing security groups
```

### Cost-Optimization Review
```
Focus on cost optimization opportunities:
- Over-provisioned resources
- Missing auto-scaling
- Expensive instance types
- Unused resources
- Missing reserved instances
```

### Reliability Review
```
Focus on reliability and availability:
- Single points of failure
- Missing backups
- No health checks
- Tight coupling
- Missing disaster recovery
```

