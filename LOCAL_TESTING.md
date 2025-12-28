# Local Testing Guide

## Overview

Complete guide for testing the Terraform + Spacelift AI Reviewer application locally.

## Prerequisites

### Required Software
- Node.js 18+ and npm
- Python 3.11+
- Docker Desktop (for local services)
- AWS CLI configured
- Terraform >= 1.5.0

### Optional
- AWS SAM CLI (for Lambda testing)
- LocalStack (for AWS services emulation)
- DynamoDB Local

## Quick Start

### 1. Frontend Local Development

```bash
# Install dependencies
npm install

# Set up environment variables
cp .env.local.example .env.local
# Edit .env.local with your values

# Start development server
npm run dev
```

The frontend will be available at `http://localhost:3000`

### 2. Backend Local Testing

```bash
# Install Python dependencies
cd lambda
pip install -r requirements.txt

# Run tests
pytest tests/
```

## Frontend Testing

### Environment Variables

Create `.env.local`:

```env
# Cognito Configuration (for local testing)
NEXT_PUBLIC_COGNITO_USER_POOL_ID=us-east-1_TEST123
NEXT_PUBLIC_COGNITO_CLIENT_ID=test_client_id
NEXT_PUBLIC_COGNITO_DOMAIN=terraform-ai-reviewer-dev
NEXT_PUBLIC_AWS_REGION=us-east-1

# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:3001

# For local development, you can use mock API
NEXT_PUBLIC_USE_MOCK_API=true
```

### Mock API Server

For local frontend testing without backend:

```bash
# Install mock server
npm install -g json-server

# Start mock API
json-server --watch mock-api/db.json --port 3001
```

Create `mock-api/db.json`:

```json
{
  "reviews": [
    {
      "review_id": "test-123",
      "terraform_code": "resource \"aws_s3_bucket\" \"test\" {}",
      "status": "completed",
      "created_at": "2024-01-15T10:00:00Z",
      "ai_review_result": {
        "overall_risk_score": 0.5,
        "security_analysis": {
          "total_findings": 2,
          "high_severity": 1,
          "medium_severity": 1,
          "low_severity": 0,
          "findings": []
        }
      }
    }
  ],
  "analytics": {
    "total_reviews": 10,
    "reviews_by_status": { "completed": 8, "pending": 2 },
    "average_risk_score": 0.45
  }
}
```

### Testing Authentication Locally

1. **Mock Authentication** (for development):

Create `src/lib/auth-mock.ts`:

```typescript
export const mockAuth = {
  user: {
    id: "test-user-123",
    email: "test@example.com",
    groups: ["aws-reviewers"],
    token: "mock-jwt-token"
  },
  signIn: async () => {},
  signOut: async () => {},
  hasRole: (role: string) => true
}
```

2. **Use Mock in Development**:

Update `src/components/auth-provider.tsx`:

```typescript
if (process.env.NODE_ENV === 'development' && process.env.NEXT_PUBLIC_USE_MOCK_AUTH === 'true') {
  // Use mock auth
}
```

## Backend Testing

### Local Lambda Testing

#### Option 1: AWS SAM Local

```bash
# Install SAM CLI
# https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html

# Test Lambda function
sam local invoke ApiHandlerFunction \
  --event events/api-handler-event.json \
  --env-vars env.json
```

Create `events/api-handler-event.json`:

```json
{
  "httpMethod": "GET",
  "path": "/api/reviews",
  "headers": {
    "Authorization": "Bearer mock-token"
  },
  "requestContext": {
    "requestId": "test-request-id"
  }
}
```

#### Option 2: Python Direct Testing

Create `lambda/tests/test_api_handler.py`:

```python
import json
import sys
sys.path.insert(0, '.')

from api_handler import handler

def test_api_handler():
    event = {
        "httpMethod": "GET",
        "path": "/api/reviews",
        "headers": {
            "Authorization": "Bearer mock-token"
        }
    }
    
    context = {}
    
    response = handler(event, context)
    print(json.dumps(response, indent=2))
```

Run:
```bash
cd lambda
python tests/test_api_handler.py
```

### Local DynamoDB Testing

#### Option 1: DynamoDB Local

```bash
# Run DynamoDB Local with Docker
docker run -p 8000:8000 amazon/dynamodb-local

# Set environment variable
export AWS_ENDPOINT_URL=http://localhost:8000

# Create table
aws dynamodb create-table \
  --endpoint-url http://localhost:8000 \
  --table-name reviews \
  --attribute-definitions AttributeName=PK,AttributeType=S AttributeName=SK,AttributeType=S \
  --key-schema AttributeName=PK,KeyType=HASH AttributeName=SK,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST
```

Update Lambda code for local testing:

```python
import os

if os.environ.get('AWS_ENDPOINT_URL'):
    dynamodb = boto3.client(
        'dynamodb',
        endpoint_url=os.environ.get('AWS_ENDPOINT_URL')
    )
else:
    dynamodb = boto3.client('dynamodb')
```

#### Option 2: LocalStack

```bash
# Install LocalStack
pip install localstack

# Start LocalStack
localstack start

# Set environment
export AWS_ENDPOINT_URL=http://localhost:4566
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1

# Deploy with LocalStack
terraform apply \
  -backend-config="endpoint=http://localhost:4566"
```

### Testing Webhooks Locally

#### GitHub Webhook Testing

```bash
# Use ngrok to expose local endpoint
ngrok http 3001

# Update GitHub webhook URL to ngrok URL
# Test webhook delivery
```

Create test webhook payload:

```bash
# Generate HMAC signature
python scripts/test-webhook-signature.py

# Send test webhook
curl -X POST http://localhost:3001/webhook/github \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: sha256=<signature>" \
  -d @test-payloads/github-pr-event.json
```

#### Spacelift Webhook Testing

```bash
# Send test Spacelift webhook
curl -X POST http://localhost:3001/webhook/spacelift \
  -H "Content-Type: application/json" \
  -H "X-Spacelift-Signature: <signature>" \
  -d @test-payloads/spacelift-run-event.json
```

## Integration Testing

### End-to-End Local Testing

1. **Start Local Services**:

```bash
# Terminal 1: DynamoDB Local
docker run -p 8000:8000 amazon/dynamodb-local

# Terminal 2: Mock API (if not using real backend)
json-server --watch mock-api/db.json --port 3001

# Terminal 3: Frontend
npm run dev
```

2. **Test Flow**:

- Open `http://localhost:3000`
- Login (mock or real)
- Create review
- View review details
- Check analytics

### Testing with Real AWS Services

For testing with real AWS (development account):

```bash
# Set AWS profile
export AWS_PROFILE=dev

# Deploy to dev environment
cd terraform
terraform workspace select dev
terraform apply

# Update frontend .env.local
NEXT_PUBLIC_API_URL=https://<api-gateway-url>
```

## Testing Scripts

### Test Data Generator

Create `scripts/test-data-generator.py`:

```python
#!/usr/bin/env python3
"""Generate test data for local testing"""

import json
import uuid
from datetime import datetime, timedelta

def generate_test_reviews(count=10):
    reviews = []
    for i in range(count):
        review = {
            "PK": f"REVIEW#{uuid.uuid4()}",
            "SK": "METADATA",
            "review_id": str(uuid.uuid4()),
            "terraform_code": f'resource "aws_s3_bucket" "test{i}" {{}}',
            "status": "completed" if i % 2 == 0 else "pending",
            "created_at": (datetime.utcnow() - timedelta(days=i)).isoformat(),
            "ai_review_result": {
                "overall_risk_score": 0.3 + (i * 0.05),
                "security_analysis": {
                    "total_findings": i,
                    "high_severity": i // 3,
                    "medium_severity": i // 2,
                    "low_severity": i - (i // 3) - (i // 2)
                }
            }
        }
        reviews.append(review)
    return reviews

if __name__ == "__main__":
    reviews = generate_test_reviews(20)
    with open('test-data/reviews.json', 'w') as f:
        json.dump(reviews, f, indent=2)
    print(f"Generated {len(reviews)} test reviews")
```

### Load Test Reviews

```bash
# Generate test data
python scripts/test-data-generator.py

# Load into DynamoDB Local
python scripts/load-test-data.py --endpoint http://localhost:8000
```

## Authentication Testing

### Mock JWT Token

For local API testing, create a mock JWT:

```python
# scripts/generate-mock-jwt.py
import jwt
import datetime

payload = {
    "sub": "test-user-123",
    "email": "test@example.com",
    "cognito:groups": ["aws-reviewers"],
    "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1),
    "iat": datetime.datetime.utcnow()
}

token = jwt.encode(payload, "mock-secret", algorithm="HS256")
print(token)
```

### Test API with Mock Token

```bash
# Generate token
MOCK_TOKEN=$(python scripts/generate-mock-jwt.py)

# Test API
curl -X GET http://localhost:3001/api/reviews \
  -H "Authorization: Bearer $MOCK_TOKEN"
```

## Testing Checklist

### Frontend Testing
- [ ] All screens load correctly
- [ ] Navigation works
- [ ] Authentication flow works
- [ ] Real-time updates work
- [ ] Responsive design works
- [ ] Charts render correctly
- [ ] Code highlighting works

### Backend Testing
- [ ] Lambda functions execute
- [ ] API endpoints respond
- [ ] DynamoDB operations work
- [ ] Webhook verification works
- [ ] JWT validation works
- [ ] Error handling works

### Integration Testing
- [ ] Frontend → Backend communication
- [ ] Authentication flow end-to-end
- [ ] Review creation flow
- [ ] Webhook processing
- [ ] Real-time updates

## Troubleshooting

### Common Issues

1. **CORS Errors**:
   - Check API Gateway CORS configuration
   - Verify allowed origins in `.env.local`

2. **Authentication Errors**:
   - Verify Cognito configuration
   - Check JWT token validity
   - Review authorizer logs

3. **DynamoDB Connection Errors**:
   - Verify endpoint URL
   - Check credentials
   - Verify table exists

4. **Lambda Timeout**:
   - Increase timeout in local config
   - Check for infinite loops
   - Review function logs

## Next Steps

1. Set up local development environment
2. Run frontend locally
3. Test backend functions
4. Test integration
5. Deploy to dev environment

