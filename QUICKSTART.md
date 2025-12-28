# Quick Start Guide

Get the Terraform + Spacelift AI Reviewer up and running in 15 minutes.

## Prerequisites

- AWS Account
- AWS CLI configured
- Terraform installed
- Node.js 18+ installed

## 5-Minute Setup

### 1. Install Dependencies

```bash
npm install
```

### 2. Configure AWS

```bash
aws configure
```

### 3. Set API Keys

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars`:
```hcl
openai_api_key = "sk-your-key"
# OR
anthropic_api_key = "sk-ant-your-key"
```

### 4. Deploy

```bash
terraform init
terraform apply
```

### 5. Configure Frontend

```bash
# Get API URL from terraform output
export NEXT_PUBLIC_API_URL="https://your-api-url.execute-api.us-east-1.amazonaws.com"

# Run frontend
npm run dev
```

Visit `http://localhost:3000`

## Test It

### Create a Review

```bash
curl -X POST $NEXT_PUBLIC_API_URL/api/reviews \
  -H "Content-Type: application/json" \
  -d '{
    "terraform_code": "resource \"aws_s3_bucket\" \"test\" {\n  bucket = \"test\"\n}"
  }'
```

### Check Results

Visit the dashboard at `http://localhost:3000` to see the review results.

## Next Steps

- Read [README.md](README.md) for full documentation
- See [DEPLOYMENT.md](DEPLOYMENT.md) for production deployment
- Check [docs/](docs/) for architecture and examples

