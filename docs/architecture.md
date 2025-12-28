# System Architecture

## Overview

The Terraform + Spacelift AI Reviewer is built on AWS serverless architecture following the Well-Architected Framework.

## Components

### 1. API Layer (API Gateway)

- **Type**: HTTP API (API Gateway v2)
- **Purpose**: RESTful API endpoints
- **Features**:
  - CORS support
  - Request throttling
  - Access logging
  - Custom domain support

### 2. Compute Layer (Lambda)

#### API Handler
- **Runtime**: Python 3.11
- **Memory**: 512 MB
- **Timeout**: 30 seconds
- **Purpose**: Handle REST API requests
- **Endpoints**:
  - GET/POST/PUT /api/reviews
  - GET /api/analytics

#### AI Reviewer
- **Runtime**: Python 3.11
- **Memory**: 2048 MB
- **Timeout**: 300 seconds (5 minutes)
- **Purpose**: Perform AI-powered code analysis
- **Dependencies**: OpenAI/Anthropic SDK

#### Webhook Handler
- **Runtime**: Python 3.11
- **Memory**: 512 MB
- **Timeout**: 30 seconds
- **Purpose**: Process Spacelift webhooks
- **Features**: Signature verification

### 3. Data Layer (DynamoDB)

#### Table Design
- **Name**: `terraform-spacelift-ai-reviewer-reviews-{env}`
- **Billing**: Pay-per-request
- **Primary Key**:
  - PK: `REVIEW#{review_id}`
  - SK: `VERSION#{version}`

#### Global Secondary Indexes

**GSI1** (Spacelift Run Lookup):
- GSI1PK: `SPACELIFT_RUN#{run_id}`
- GSI1SK: `CREATED#{timestamp}`

**GSI2** (Status Lookup):
- GSI2PK: `STATUS#{status}`
- GSI2SK: `CREATED#{timestamp}`

#### Features
- Point-in-time recovery enabled
- Versioned records (immutable history)
- Automatic scaling

### 4. Security Layer

#### Secrets Manager
- OpenAI API key
- Anthropic API key
- Spacelift webhook secret

#### IAM Roles
- Lambda execution role
- DynamoDB read/write permissions
- Secrets Manager read permissions
- CloudWatch Logs write permissions

### 5. Frontend (Next.js)

#### Architecture
- **Framework**: Next.js 14 (App Router)
- **Styling**: Tailwind CSS
- **Components**: shadcn/ui
- **Charts**: Recharts
- **State**: React hooks

#### Features
- Real-time polling (10-second intervals)
- Responsive design
- Color-coded risk indicators
- Interactive charts and visualizations

## Data Flow

### Review Creation Flow

```
1. Client → API Gateway → API Handler Lambda
2. API Handler → DynamoDB (create review record)
3. API Handler → AI Reviewer Lambda (async invoke)
4. AI Reviewer → AI Service (OpenAI/Anthropic)
5. AI Reviewer → DynamoDB (update with results)
6. Client polls for completion
```

### Webhook Flow

```
1. Spacelift → API Gateway → Webhook Handler Lambda
2. Webhook Handler → Verify signature
3. Webhook Handler → AI Reviewer Lambda (async invoke)
4. AI Reviewer → AI Service
5. AI Reviewer → DynamoDB
```

### Query Flow

```
1. Client → API Gateway → API Handler Lambda
2. API Handler → DynamoDB (query/scan)
3. API Handler → Client (JSON response)
```

## Scalability

### Horizontal Scaling
- Lambda: Automatic scaling (1000 concurrent executions)
- DynamoDB: On-demand scaling
- API Gateway: Automatic scaling

### Performance Optimization
- Lambda memory tuning
- DynamoDB query optimization
- API Gateway caching (can be added)
- Frontend polling intervals

## Reliability

### Error Handling
- Lambda retries (3 attempts)
- Dead letter queues (can be added)
- Error logging to CloudWatch
- Graceful degradation

### High Availability
- Multi-AZ by default (AWS managed)
- No single points of failure
- Stateless architecture

## Security

### Network Security
- API Gateway HTTPS only
- VPC endpoints (optional)
- Private subnets (optional)

### Data Security
- Encryption at rest (DynamoDB)
- Encryption in transit (TLS)
- Secrets in Secrets Manager
- IAM least privilege

### Application Security
- Input validation
- Webhook signature verification
- CORS configuration
- Rate limiting

## Monitoring & Observability

### CloudWatch
- Lambda execution logs
- API Gateway access logs
- DynamoDB metrics
- Custom metrics (can be added)

### Alarms (Recommended)
- Lambda error rate
- API Gateway 5xx errors
- DynamoDB throttling
- High latency

## Cost Optimization

### Current Design
- Pay-per-request DynamoDB
- Lambda pay-per-invocation
- API Gateway pay-per-request

### Cost Estimates (Example)
- 1000 reviews/month:
  - Lambda: ~$5-10
  - DynamoDB: ~$1-2
  - API Gateway: ~$1
  - AI API: Variable (OpenAI/Anthropic pricing)

### Optimization Opportunities
- Reserved capacity (if predictable)
- Lambda provisioned concurrency (if needed)
- API Gateway caching
- DynamoDB on-demand vs provisioned

## Disaster Recovery

### Backup Strategy
- DynamoDB point-in-time recovery
- Terraform state in S3
- Secrets in Secrets Manager (backed up)

### Recovery Procedures
1. Restore DynamoDB from PITR
2. Redeploy infrastructure (Terraform)
3. Restore secrets (if needed)

## Future Enhancements

### Potential Additions
- SQS for async processing
- EventBridge for event-driven architecture
- Step Functions for complex workflows
- CloudFront for frontend CDN
- WAF for API protection
- X-Ray for distributed tracing
- SNS for notifications

