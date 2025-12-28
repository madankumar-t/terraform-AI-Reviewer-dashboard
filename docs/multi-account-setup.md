# Multi-Account Setup Guide

## Overview

This guide provides step-by-step instructions for setting up the multi-account AWS architecture for the Terraform + Spacelift AI Reviewer platform.

## Prerequisites

- AWS account with Organizations access
- AWS CLI configured
- Terraform >= 1.5.0
- Administrative access to Management account

## Step 1: Create AWS Organization

### 1.1 Enable Organizations

```bash
# In Management Account
aws organizations create-organization --feature-set ALL
```

### 1.2 Create Organizational Units (OUs)

```bash
# Create OUs
aws organizations create-organizational-unit \
  --parent-id r-xxxx \
  --name "SharedServices"

aws organizations create-organizational-unit \
  --parent-id r-xxxx \
  --name "Applications"
```

### 1.3 Create Accounts

```bash
# Create Shared Services Account
aws organizations create-account \
  --email shared-services@example.com \
  --account-name "SharedServices"

# Create Production Account
aws organizations create-account \
  --email production@example.com \
  --account-name "Production"

# Create Staging Account
aws organizations create-account \
  --email staging@example.com \
  --account-name "Staging"
```

**Note**: Save the account IDs for later use.

## Step 2: Configure Service Control Policies (SCPs)

### 2.1 Create SCPs

**Organization-Level SCP** (`deny-root-usage.json`):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyRootAccountUsage",
      "Effect": "Deny",
      "Action": "*",
      "Resource": "*",
      "Condition": {
        "StringLike": {
          "aws:PrincipalArn": "arn:aws:iam::*:root"
        }
      }
    },
    {
      "Sid": "RequireMFA",
      "Effect": "Deny",
      "Action": "*",
      "Resource": "*",
      "Condition": {
        "BoolIfExists": {
          "aws:MultiFactorAuthPresent": "false"
        }
      }
    }
  ]
}
```

**Application Account SCP** (`application-guardrails.json`):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyRegions",
      "Effect": "Deny",
      "NotAction": [
        "iam:*",
        "organizations:*",
        "route53:*",
        "cloudfront:*"
      ],
      "Resource": "*",
      "Condition": {
        "StringNotEquals": {
          "aws:RequestedRegion": [
            "us-east-1",
            "us-west-2"
          ]
        }
      }
    },
    {
      "Sid": "DenyPublicS3Buckets",
      "Effect": "Deny",
      "Action": [
        "s3:PutBucketPublicAccessBlock",
        "s3:PutBucketAcl"
      ],
      "Resource": "*",
      "Condition": {
        "StringNotEquals": {
          "s3:x-amz-acl": "private"
        }
      }
    }
  ]
}
```

### 2.2 Attach SCPs

```bash
# Create SCPs
ORG_SCP_ID=$(aws organizations create-policy \
  --content file://deny-root-usage.json \
  --name "DenyRootUsage" \
  --type SERVICE_CONTROL_POLICY \
  --description "Deny root account usage and require MFA" \
  --query 'Policy.PolicySummary.Id' --output text)

APP_SCP_ID=$(aws organizations create-policy \
  --content file://application-guardrails.json \
  --name "ApplicationGuardrails" \
  --type SERVICE_CONTROL_POLICY \
  --description "Application account guardrails" \
  --query 'Policy.PolicySummary.Id' --output text)

# Attach to root
aws organizations attach-policy \
  --policy-id $ORG_SCP_ID \
  --target-id r-xxxx

# Attach to Applications OU
aws organizations attach-policy \
  --policy-id $APP_SCP_ID \
  --target-id ou-xxxx-xxxxx
```

## Step 3: Set Up IAM Identity Center

### 3.1 Enable IAM Identity Center

```bash
# Enable (via Console or CLI)
aws sso-admin create-instance \
  --name "MainSSO" \
  --query 'InstanceArn' --output text
```

### 3.2 Configure Azure Entra ID as Identity Provider

**Via Console**:
1. Go to IAM Identity Center
2. Settings → Identity source
3. Change identity source → External identity provider
4. Upload Azure Entra ID SAML metadata
5. Configure attribute mapping

**SAML Attribute Mapping**:
- `NameID` → `${user:name}`
- `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress` → `${user:email}`
- `http://schemas.microsoft.com/ws/2008/06/identity/claims/groups` → `${user:groups}`

### 3.3 Enable SCIM Provisioning

```bash
# Get SCIM endpoint
SCIM_ENDPOINT=$(aws sso-admin get-instance \
  --query 'InstanceArn' --output text)

# Configure in Azure Entra ID
# Use SCIM endpoint and access token from IAM Identity Center
```

## Step 4: Create Permission Sets

### 4.1 Define Permission Sets

**ReadOnlyAccess**:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudwatch:Get*",
        "cloudwatch:List*",
        "cloudwatch:Describe*",
        "logs:Describe*",
        "logs:Get*",
        "logs:List*",
        "logs:TestMetricFilter",
        "logs:FilterLogEvents"
      ],
      "Resource": "*"
    }
  ]
}
```

**PowerUserAccess**:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "NotAction": [
        "iam:*",
        "organizations:*"
      ],
      "Resource": "*"
    }
  ]
}
```

### 4.2 Create Permission Sets

```bash
# Create ReadOnly permission set
aws sso-admin create-permission-set \
  --instance-arn $INSTANCE_ARN \
  --name "ReadOnlyAccess" \
  --description "Read-only access" \
  --session-duration PT1H

# Attach managed policy
aws sso-admin attach-managed-policy-to-permission-set \
  --instance-arn $INSTANCE_ARN \
  --permission-set-arn $PERMISSION_SET_ARN \
  --managed-policy-arn "arn:aws:iam::aws:policy/ReadOnlyAccess"
```

## Step 5: Configure Network Connectivity

### 5.1 Set Up Transit Gateway (Shared Services)

```bash
# In Shared Services Account
TGW_ID=$(aws ec2 create-transit-gateway \
  --description "Hub for multi-account connectivity" \
  --query 'TransitGateway.TransitGatewayId' --output text)

# Share with Organization
aws ram create-resource-share \
  --name "TransitGatewayShare" \
  --resource-arns "arn:aws:ec2:us-east-1:ACCOUNT:transit-gateway/$TGW_ID" \
  --principals "arn:aws:organizations::ORG_ID:organization/o-xxxxx"
```

### 5.2 Accept Transit Gateway Share (Application Accounts)

```bash
# In Application Account
SHARE_ARN=$(aws ram get-resource-shares \
  --resource-owner EXTERNAL \
  --name "TransitGatewayShare" \
  --query 'resourceShares[0].resourceShareArn' --output text)

aws ram associate-resource-share \
  --resource-share-arn $SHARE_ARN
```

### 5.3 Create VPCs and Attach to Transit Gateway

```bash
# In each Application Account
# Create VPC
VPC_ID=$(aws ec2 create-vpc \
  --cidr-block 10.0.0.0/16 \
  --query 'Vpc.VpcId' --output text)

# Create Transit Gateway Attachment
aws ec2 create-transit-gateway-vpc-attachment \
  --transit-gateway-id $TGW_ID \
  --vpc-id $VPC_ID \
  --subnet-ids subnet-xxx subnet-yyy subnet-zzz
```

## Step 6: Set Up VPC Endpoints

### 6.1 Create VPC Endpoints (Application Accounts)

```bash
# DynamoDB Gateway Endpoint
aws ec2 create-vpc-endpoint \
  --vpc-id $VPC_ID \
  --service-name com.amazonaws.us-east-1.dynamodb \
  --route-table-ids rtb-xxx

# Secrets Manager Interface Endpoint
aws ec2 create-vpc-endpoint \
  --vpc-id $VPC_ID \
  --service-name com.amazonaws.us-east-1.secretsmanager \
  --vpc-endpoint-type Interface \
  --subnet-ids subnet-xxx subnet-yyy \
  --security-group-ids sg-xxx

# CloudWatch Logs Interface Endpoint
aws ec2 create-vpc-endpoint \
  --vpc-id $VPC_ID \
  --service-name com.amazonaws.us-east-1.logs \
  --vpc-endpoint-type Interface \
  --subnet-ids subnet-xxx subnet-yyy \
  --security-group-ids sg-xxx
```

### 6.2 Create Bedrock PrivateLink (Shared Services)

```bash
# Create VPC Endpoint for Bedrock
aws ec2 create-vpc-endpoint \
  --vpc-id $VPC_ID \
  --service-name com.amazonaws.us-east-1.bedrock-runtime \
  --vpc-endpoint-type Interface \
  --subnet-ids subnet-xxx subnet-yyy \
  --security-group-ids sg-xxx
```

## Step 7: Configure Cross-Account Access

### 7.1 Create Cross-Account Roles

**In Application Account** (`cross-account-role.json`):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::SHARED_SERVICES_ACCOUNT:root"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "sts:ExternalId": "unique-external-id"
        }
      }
    }
  ]
}
```

```bash
# Create role
aws iam create-role \
  --role-name CrossAccountAccess \
  --assume-role-policy-document file://cross-account-role.json
```

### 7.2 Grant Bedrock Access

```bash
# In Application Account
aws iam attach-role-policy \
  --role-name LambdaExecutionRole \
  --policy-arn "arn:aws:iam::aws:policy/AmazonBedrockFullAccess"
```

## Step 8: Deploy Application Infrastructure

### 8.1 Update Terraform Configuration

**Update `terraform/variables.tf`**:

```hcl
variable "aws_account_id" {
  description = "AWS Account ID"
  type        = string
}

variable "shared_services_account_id" {
  description = "Shared Services Account ID"
  type        = string
}

variable "transit_gateway_id" {
  description = "Transit Gateway ID from Shared Services"
  type        = string
}
```

### 8.2 Deploy Infrastructure

```bash
cd terraform

# Initialize
terraform init

# Set variables
export TF_VAR_aws_account_id="123456789012"
export TF_VAR_shared_services_account_id="987654321098"
export TF_VAR_transit_gateway_id="tgw-xxxxx"

# Plan
terraform plan

# Apply
terraform apply
```

## Step 9: Configure Monitoring

### 9.1 Enable Security Hub

```bash
# In Management Account
aws securityhub enable-security-hub

# Create aggregator
aws securityhub create-finding-aggregator \
  --region-linking-mode ALL_REGIONS
```

### 9.2 Enable GuardDuty

```bash
# In Management Account
aws guardduty create-detector --enable

# Enable organization-wide
aws guardduty create-organization-configuration \
  --auto-enable
```

### 9.3 Enable CloudTrail Organization Trail

```bash
# In Management Account
aws cloudtrail create-trail \
  --name organization-trail \
  --s3-bucket-name org-trail-bucket \
  --is-organization-trail
```

## Step 10: Test and Validate

### 10.1 Test Identity Access

```bash
# Login via IAM Identity Center
aws sso login --profile sso-profile

# Verify access
aws sts get-caller-identity
```

### 10.2 Test Network Connectivity

```bash
# Test VPC endpoint
aws dynamodb list-tables --endpoint-url https://dynamodb.us-east-1.amazonaws.com

# Test Transit Gateway
# Ping between VPCs
```

### 10.3 Test Application

```bash
# Create test review
curl -X POST https://api-url/api/reviews \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"terraform_code": "resource \"aws_s3_bucket\" \"test\" {}"}'
```

## Troubleshooting

### Common Issues

1. **SCP Blocking Operations**:
   - Check SCP attachments
   - Verify policy conditions
   - Review CloudTrail for denied actions

2. **Cross-Account Access Denied**:
   - Verify IAM role trust relationships
   - Check external ID (if used)
   - Review resource-based policies

3. **VPC Endpoint Issues**:
   - Check security group rules
   - Verify route table configuration
   - Test DNS resolution

4. **Identity Center Not Working**:
   - Verify SAML metadata
   - Check attribute mapping
   - Review sign-in logs

## Next Steps

1. Configure Azure Entra ID SAML provider
2. Set up SCIM provisioning
3. Create user assignments
4. Test end-to-end flows
5. Document procedures
6. Train team members

## References

- [AWS Organizations User Guide](https://docs.aws.amazon.com/organizations/)
- [IAM Identity Center User Guide](https://docs.aws.amazon.com/singlesignon/)
- [Transit Gateway User Guide](https://docs.aws.amazon.com/vpc/latest/tgw/)
- [VPC Endpoints User Guide](https://docs.aws.amazon.com/vpc/latest/privatelink/)

