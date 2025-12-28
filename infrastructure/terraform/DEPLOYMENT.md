# Complete Platform Deployment Guide

## Step-by-Step Deployment

### Phase 1: Prerequisites

1. **AWS Account Setup**
   ```bash
   # Verify AWS credentials
   aws sts get-caller-identity
   
   # Verify required permissions
   aws iam get-user
   ```

2. **Enable Bedrock Models**
   - Go to AWS Bedrock Console
   - Enable models:
     - Claude 3.5 Sonnet
     - Claude 3 Opus
     - Llama 3 70B

3. **Create Remote State Infrastructure** (One-time setup)
   ```bash
   # Uncomment resources in remote-state.tf
   terraform init
   terraform apply -target=aws_s3_bucket.terraform_state
   terraform apply -target=aws_dynamodb_table.terraform_state_lock
   ```

### Phase 2: Configuration

1. **Backend Configuration**
   ```bash
   cp backend.hcl.example backend.hcl
   # Edit backend.hcl with your values
   ```

2. **Variables Configuration**
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with your values
   ```

3. **Initialize Terraform**
   ```bash
   terraform init -backend-config=backend.hcl
   ```

### Phase 3: Deployment

1. **Plan Deployment**
   ```bash
   terraform plan -out=tfplan
   ```

2. **Review Plan**
   - Check resource counts
   - Verify VPC CIDR blocks
   - Confirm account IDs

3. **Deploy Infrastructure**
   ```bash
   terraform apply tfplan
   ```

### Phase 4: Post-Deployment

1. **Configure Secrets**
   ```bash
   # Update secrets in AWS Secrets Manager
   aws secretsmanager update-secret \
     --secret-id terraform-spacelift-ai-reviewer-openai-api-key-prod \
     --secret-string "your-key"
   ```

2. **Deploy Frontend**
   ```bash
   # Build Next.js app
   cd ..
   npm run build
   
   # Upload to S3
   aws s3 sync .next/static s3://$(terraform output -raw s3_bucket_name)/_next/static
   aws s3 sync public s3://$(terraform output -raw s3_bucket_name)/public
   aws s3 cp .next/standalone s3://$(terraform output -raw s3_bucket_name)/ --recursive
   ```

3. **Configure Webhooks**
   - GitHub: Point to API Gateway `/webhook/github`
   - Spacelift: Point to API Gateway `/webhook/spacelift`

4. **Test Endpoints**
   ```bash
   # Get API URL
   API_URL=$(terraform output -raw api_gateway_url)
   
   # Test health endpoint
   curl $API_URL/api/reviews
   ```

## Multi-Account Deployment

### Management Account

1. Deploy IAM Identity Center configuration
2. Configure external identity provider (Azure AD)
3. Create permission sets
4. Assign groups to accounts

### Application Account

1. Deploy all infrastructure (this repo)
2. Configure cross-account roles
3. Set up VPC peering (if needed)
4. Configure resource sharing (if using RAM)

## Verification Checklist

- [ ] Remote state bucket created
- [ ] DynamoDB state lock table created
- [ ] VPC created with subnets
- [ ] VPC endpoints created
- [ ] Lambda functions deployed
- [ ] API Gateway configured
- [ ] DynamoDB table created
- [ ] CloudFront distribution created
- [ ] S3 bucket for frontend created
- [ ] CloudWatch logs configured
- [ ] Alarms created
- [ ] SNS topic created (if enabled)
- [ ] Secrets stored
- [ ] IAM roles configured
- [ ] Security groups configured

## Rollback Procedure

If deployment fails:

1. **Check State**
   ```bash
   terraform state list
   ```

2. **Remove Failed Resources**
   ```bash
   terraform state rm <resource>
   ```

3. **Re-apply**
   ```bash
   terraform apply
   ```

## Troubleshooting

### Common Issues

1. **State Lock**
   ```bash
   terraform force-unlock <LOCK_ID>
   ```

2. **VPC Endpoint Timeout**
   - Check security group rules
   - Verify subnet routing

3. **Lambda VPC Timeout**
   - Increase Lambda timeout
   - Check NAT Gateway
   - Verify security groups

4. **Bedrock Access Denied**
   - Enable models in Bedrock console
   - Check IAM permissions
   - Verify VPC endpoint

## Cost Estimation

Approximate monthly costs (us-east-1):

- VPC: ~$50 (NAT Gateways)
- Lambda: ~$20 (based on usage)
- API Gateway: ~$10 (based on requests)
- DynamoDB: ~$25 (on-demand)
- CloudFront: ~$10 (based on traffic)
- S3: ~$5 (storage + requests)
- CloudWatch: ~$15 (logs + metrics)

**Total**: ~$135/month (varies by usage)

## Security Hardening

1. Enable MFA for all IAM users
2. Use least privilege IAM policies
3. Enable VPC Flow Logs
4. Enable CloudTrail
5. Enable GuardDuty
6. Regular security audits
7. Rotate secrets regularly
8. Use AWS Config for compliance

## Monitoring Setup

1. **CloudWatch Dashboard**
   - Access via AWS Console
   - URL in terraform outputs

2. **SNS Alerts**
   - Subscribe email addresses
   - Configure Slack/PagerDuty (optional)

3. **Custom Metrics**
   - Add custom metrics in Lambda
   - Create alarms as needed

## Maintenance

### Regular Tasks

- Weekly: Review CloudWatch alarms
- Monthly: Review costs and optimize
- Quarterly: Security audit
- Annually: Disaster recovery test

### Updates

1. **Terraform Updates**
   ```bash
   terraform init -upgrade
   terraform plan
   terraform apply
   ```

2. **Lambda Updates**
   - Update code
   - Update zip file
   - Terraform will detect changes

3. **Frontend Updates**
   - Build new version
   - Upload to S3
   - Invalidate CloudFront cache

## Disaster Recovery

### Backup Strategy

1. **Terraform State**: Versioned in S3
2. **DynamoDB**: Point-in-time recovery enabled
3. **S3**: Versioning enabled
4. **Lambda Code**: In version control

### Recovery Procedure

1. Restore from Terraform state
2. Restore DynamoDB from backup
3. Re-upload frontend to S3
4. Verify all services

## Support

For issues:
1. Check CloudWatch logs
2. Review Terraform state
3. Check AWS Service Health
4. Review documentation

