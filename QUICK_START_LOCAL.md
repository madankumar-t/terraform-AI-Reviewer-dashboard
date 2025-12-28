# Quick Start - Local Testing

## Fastest Way to Test Locally

### Option 1: Frontend Only (Mock Backend)

```bash
# 1. Install dependencies
npm install

# 2. Set up environment
cp .env.local.example .env.local
# Edit .env.local - set NEXT_PUBLIC_USE_MOCK_API=true

# 3. Start mock API (in separate terminal)
npm install -g json-server
json-server --watch mock-api/db.json --port 3001

# 4. Start frontend
npm run dev
```

Open `http://localhost:3000` - Frontend works with mock data!

### Option 2: Full Stack (Docker + Local Services)

```bash
# 1. Start DynamoDB Local
docker run -d -p 8000:8000 --name dynamodb-local amazon/dynamodb-local

# 2. Create table
aws dynamodb create-table \
  --endpoint-url http://localhost:8000 \
  --table-name reviews \
  --attribute-definitions AttributeName=PK,AttributeType=S AttributeName=SK,AttributeType=S \
  --key-schema AttributeName=PK,KeyType=HASH AttributeName=SK,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST

# 3. Load test data
python scripts/load-test-data.py --endpoint http://localhost:8000

# 4. Set environment for Lambda
export AWS_ENDPOINT_URL=http://localhost:8000
export DYNAMODB_TABLE_NAME=reviews

# 5. Test Lambda locally
cd lambda
python -m pytest tests/ -v

# 6. Start frontend
cd ..
npm run dev
```

### Option 3: Test with Real AWS (Dev Account)

```bash
# 1. Deploy to dev
cd terraform
terraform workspace new dev
terraform apply

# 2. Update frontend .env.local
NEXT_PUBLIC_API_URL=https://<your-api-gateway-url>

# 3. Start frontend
npm run dev
```

## Testing Authentication

### Mock Authentication (Easiest)

Update `src/components/auth-provider.tsx`:

```typescript
// Add at top of component
if (process.env.NODE_ENV === 'development') {
  // Use mock user
  const mockUser = {
    id: "test-user",
    email: "test@example.com",
    groups: ["aws-reviewers"],
    token: "mock-token"
  }
  // Return mock user
}
```

### Real Authentication (Full Test)

1. Set up Cognito in AWS
2. Configure Azure Entra ID
3. Update `.env.local` with real values
4. Test login flow

## Common Test Scenarios

### 1. Test Review Creation

```bash
# Using curl
curl -X POST http://localhost:3001/api/reviews \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer mock-token" \
  -d '{
    "terraform_code": "resource \"aws_s3_bucket\" \"test\" {}"
  }'
```

### 2. Test Webhook

```bash
# Generate signature
python scripts/test-webhook-signature.py github "your-secret" test-payloads/github-pr-event.json

# Send webhook
curl -X POST http://localhost:3001/webhook/github \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: sha256=<signature>" \
  -d @test-payloads/github-pr-event.json
```

### 3. Test Frontend Screens

1. **Executive Dashboard**: `http://localhost:3000/executive`
2. **PR Review**: `http://localhost:3000/pr-review/test-review-1`
3. **Spacelift Runs**: `http://localhost:3000/spacelift-runs`
4. **Compliance**: `http://localhost:3000/compliance`

## Troubleshooting

### Port Already in Use

```bash
# Kill process on port 3000
lsof -ti:3000 | xargs kill -9

# Kill process on port 3001
lsof -ti:3001 | xargs kill -9
```

### DynamoDB Connection Issues

```bash
# Check if DynamoDB Local is running
docker ps | grep dynamodb-local

# Restart if needed
docker restart dynamodb-local
```

### CORS Errors

Add to `next.config.js`:

```javascript
async headers() {
  return [
    {
      source: '/api/:path*',
      headers: [
        { key: 'Access-Control-Allow-Origin', value: '*' },
      ],
    },
  ]
}
```

## Next Steps

1. ✅ Test frontend locally
2. ✅ Test backend functions
3. ✅ Test integration
4. ✅ Deploy to dev environment

