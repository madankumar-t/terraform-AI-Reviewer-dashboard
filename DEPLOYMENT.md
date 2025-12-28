# Deployment Guide

## Prerequisites

1. AWS CLI configured with appropriate credentials
2. Terraform >= 1.5.0 installed
3. Node.js >= 18.x and npm
4. Python >= 3.11 (for local testing)

## Step-by-Step Deployment

### 1. Clone and Setup

```bash
git clone <repository-url>
cd terraform-spacelift-ai-reviewer
npm install
```

### 2. Configure Terraform Variables

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` with your values:

```hcl
aws_region = "us-east-1"
environment = "prod"
openai_api_key = "sk-your-key-here"
# or
anthropic_api_key = "sk-ant-your-key-here"
spacelift_webhook_secret = "your-secret"
allowed_origins = ["https://yourdomain.com"]
```

### 3. Initialize Terraform

```bash
terraform init
```

If using S3 backend, configure it in `main.tf`:

```hcl
backend "s3" {
  bucket = "your-terraform-state-bucket"
  key    = "terraform-spacelift-ai-reviewer/terraform.tfstate"
  region = "us-east-1"
}
```

### 4. Review Deployment Plan

```bash
terraform plan
```

Review the resources that will be created:
- DynamoDB table
- Lambda functions (3)
- API Gateway
- IAM roles and policies
- Secrets Manager secrets

### 5. Deploy Infrastructure

```bash
terraform apply
```

Type `yes` when prompted. This will take approximately 5-10 minutes.

### 6. Note Output Values

After deployment, Terraform will output:

```
api_gateway_url = "https://abc123.execute-api.us-east-1.amazonaws.com"
api_endpoint = "https://abc123.execute-api.us-east-1.amazonaws.com/$default"
dynamodb_table_name = "terraform-spacelift-ai-reviewer-reviews-prod"
```

Save these values.

### 7. Configure Frontend

Update the frontend API URL:

**Option A: Environment Variable**

```bash
export NEXT_PUBLIC_API_URL="https://abc123.execute-api.us-east-1.amazonaws.com"
```

**Option B: Update next.config.js**

```javascript
env: {
  NEXT_PUBLIC_API_URL: 'https://abc123.execute-api.us-east-1.amazonaws.com',
}
```

### 8. Build and Deploy Frontend

**For Development:**

```bash
npm run dev
```

**For Production:**

```bash
npm run build
npm start
```

Or deploy to Vercel/Netlify:

```bash
# Vercel
vercel deploy

# Netlify
netlify deploy --prod
```

### 9. Configure Spacelift Webhook

1. Go to your Spacelift stack settings
2. Navigate to Webhooks
3. Add new webhook:
   - URL: `https://your-api-url/webhook/spacelift`
   - Events: `run:finished`, `run:tracked`, `run:plan_finished`
   - Secret: (use the same secret from terraform.tfvars)

### 10. Test the System

**Test API Endpoint:**

```bash
curl https://your-api-url/api/reviews
```

**Test Review Creation:**

```bash
curl -X POST https://your-api-url/api/reviews \
  -H "Content-Type: application/json" \
  -d '{
    "terraform_code": "resource \"aws_s3_bucket\" \"test\" {\n  bucket = \"test-bucket\"\n}",
    "spacelift_run_id": "test-run-123"
  }'
```

**Test Webhook (if configured):**

Trigger a Spacelift run and verify the webhook is received.

## Verification Checklist

- [ ] DynamoDB table created
- [ ] Lambda functions deployed
- [ ] API Gateway accessible
- [ ] Secrets stored in Secrets Manager
- [ ] Frontend connects to API
- [ ] Test review creation works
- [ ] AI review completes successfully
- [ ] Webhook receives Spacelift events

## Troubleshooting

### Lambda Function Errors

Check CloudWatch Logs:

```bash
aws logs tail /aws/lambda/terraform-spacelift-ai-reviewer-ai-reviewer-prod --follow
```

### API Gateway CORS Issues

Verify CORS configuration in `terraform/api_gateway.tf` and update `allowed_origins`.

### AI Service Errors

1. Verify API keys in Secrets Manager:
   ```bash
   aws secretsmanager get-secret-value --secret-id terraform-spacelift-ai-reviewer/openai-api-key/prod
   ```

2. Check Lambda execution logs for AI service errors

3. Verify API quota/limits

### DynamoDB Access Issues

Check IAM role permissions in `terraform/iam.tf`.

## Updating Deployment

### Update Lambda Code

```bash
cd lambda
# Make your changes
cd ../terraform
terraform apply
```

### Update Infrastructure

```bash
cd terraform
terraform plan
terraform apply
```

### Rollback

If needed, rollback to previous Terraform state:

```bash
terraform state list
terraform state show <resource>
terraform apply -target=<resource>
```

## Cleanup

To remove all resources:

```bash
cd terraform
terraform destroy
```

**Warning**: This will delete all data in DynamoDB!

## Production Considerations

1. **Backend State**: Use S3 backend for Terraform state
2. **Secrets**: Rotate API keys regularly
3. **Monitoring**: Set up CloudWatch alarms
4. **Backup**: Enable DynamoDB point-in-time recovery
5. **CORS**: Restrict allowed origins to your domain
6. **Rate Limiting**: Configure API Gateway throttling
7. **Custom Domain**: Set up custom domain for API Gateway
8. **CDN**: Use CloudFront for frontend
9. **WAF**: Add Web Application Firewall
10. **Logging**: Enable detailed logging and monitoring

## Cost Monitoring

Monitor costs in AWS Cost Explorer:

- Lambda invocations
- DynamoDB read/write units
- API Gateway requests
- AI API usage (external)

Set up billing alerts in AWS Budgets.

