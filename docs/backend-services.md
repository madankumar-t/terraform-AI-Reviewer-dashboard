# Backend Services Documentation

## Overview

Complete backend service architecture with API Gateway, Lambda functions, webhook handlers, and structured logging for SOC2 compliance.

## API Gateway Routes

### Review Endpoints

| Method | Route | Handler | Description |
|--------|-------|---------|-------------|
| GET | `/api/reviews` | `api_handler` | List reviews with filters |
| GET | `/api/reviews/{reviewId}` | `api_handler` | Get specific review |
| POST | `/api/reviews` | `api_handler` | Create new review |
| PUT | `/api/reviews/{reviewId}` | `api_handler` | Update review |
| POST | `/api/reviews/pr` | `pr_review_handler` | Create PR review |

### Analytics Endpoints

| Method | Route | Handler | Description |
|--------|-------|---------|-------------|
| GET | `/api/analytics` | `api_handler` | Get analytics summary |
| GET | `/api/analytics/historical` | `historical_analysis_handler` | Historical analysis |

### Webhook Endpoints

| Method | Route | Handler | Description |
|--------|-------|---------|-------------|
| POST | `/webhook/spacelift` | `webhook_handler` | Spacelift webhook |
| POST | `/webhook/github` | `github_webhook_handler` | GitHub webhook |

## Lambda Functions

### 1. API Handler (`api_handler.py`)

**Purpose**: Main REST API endpoint handler

**Routes Handled**:
- `GET /api/reviews`
- `GET /api/reviews/{reviewId}`
- `POST /api/reviews`
- `PUT /api/reviews/{reviewId}`
- `GET /api/analytics`

**Features**:
- Structured logging
- Audit trail
- Error handling
- Request/response logging

**IAM Permissions**:
- DynamoDB read/write
- CloudWatch Logs

### 2. PR Review Handler (`pr_review_handler.py`)

**Purpose**: Handle GitHub PR review requests

**Features**:
- PR context extraction
- Review creation
- Async AI reviewer invocation
- Audit logging

**IAM Permissions**:
- DynamoDB write
- Lambda invoke (AI reviewer)
- CloudWatch Logs

### 3. AI Reviewer (`ai_reviewer.py`)

**Purpose**: Perform AI-powered code analysis

**Features**:
- Bedrock integration
- Risk scoring
- Confidence calculation
- Versioned reviews

**IAM Permissions**:
- DynamoDB read/write
- Bedrock invoke
- CloudWatch Logs

### 4. Spacelift Webhook Handler (`webhook_handler.py`)

**Purpose**: Process Spacelift webhook events

**Events Handled**:
- `run:finished`
- `run:tracked`
- `run:plan_finished`

**Features**:
- Signature verification
- Review creation
- Async processing
- Security event logging

**IAM Permissions**:
- Secrets Manager read
- DynamoDB write
- Lambda invoke
- CloudWatch Logs

### 5. GitHub Webhook Handler (`github_webhook_handler.py`)

**Purpose**: Process GitHub webhook events

**Events Handled**:
- `pull_request` (opened, synchronize)
- `push`

**Features**:
- HMAC SHA256 signature verification
- PR context extraction
- Terraform file detection
- Review triggering

**IAM Permissions**:
- Secrets Manager read
- Lambda invoke (PR review handler)
- CloudWatch Logs

### 6. Historical Analysis Handler (`historical_analysis_handler.py`)

**Purpose**: Analyze historical review data

**Analysis Types**:
- Trends: Risk and finding trends over time
- Patterns: Repeated issues and patterns
- Correlations: Finding-to-risk correlations

**Features**:
- Stack-specific analysis
- Date range filtering
- Aggregated insights
- Performance logging

**IAM Permissions**:
- DynamoDB read (query/scan)
- CloudWatch Logs

### 7. Trend Aggregation Handler (`trend_aggregation_handler.py`)

**Purpose**: Pre-compute trend data (scheduled)

**Schedule**: Daily at 2 AM UTC (EventBridge)

**Features**:
- Stack-level aggregation
- Global trend calculation
- Data storage
- Performance metrics

**IAM Permissions**:
- DynamoDB read/write
- CloudWatch Logs

## Webhook Verification

### GitHub Webhook Verification

**Algorithm**: HMAC SHA256

**Implementation**:
```python
def verify_github_signature(body: str, signature: str) -> bool:
    secret = get_secret('github-webhook-secret')
    expected = hmac.new(
        secret.encode('utf-8'),
        body.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature[7:], expected)  # Remove 'sha256=' prefix
```

**Security Events**:
- Invalid signature → Security event logged
- Failed verification → 401 response

### Spacelift Webhook Verification

**Algorithm**: HMAC SHA256

**Implementation**:
```python
def verify_signature(body: str, signature: str, secret: str) -> bool:
    expected = hmac.new(
        secret.encode('utf-8'),
        body.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected)
```

## DynamoDB Versioning

### Version Creation

**Process**:
1. Create Version 1 (initial)
2. Update creates Version 2, 3, etc.
3. Previous version ID tracked
4. All versions immutable

**Implementation**:
```python
def update_review(review_id: str, update_data: Dict[str, Any]):
    current = get_review(review_id)
    new_version = current['version'] + 1
    
    new_review = Review(
        **current,
        **update_data,
        version=new_version,
        previous_version_id=f"{review_id}#VERSION#{current['version']}"
    )
    
    create_review(new_review)  # Creates new version
```

### Version Query

**Get Latest**:
```python
response = table.query(
    KeyConditionExpression='PK = :pk',
    ScanIndexForward=False,  # Descending
    Limit=1
)
```

**Get All Versions**:
```python
response = table.query(
    KeyConditionExpression='PK = :pk',
    ScanIndexForward=True  # Ascending
)
```

## Structured Logging

### Logger Features

**SOC2 Compliance**:
- JSON structured logs
- Trace ID correlation
- Audit trail fields
- Security event logging
- Performance metrics

**Log Levels**:
- `INFO`: General information
- `WARN`: Warnings
- `ERROR`: Errors with stack traces
- `DEBUG`: Debug information (non-prod)
- `AUDIT`: Audit events
- `SECURITY`: Security events
- `PERF`: Performance metrics

### Audit Logging

**Required Fields**:
- `event_type`: Type of audit event
- `user_id`: User/service performing action
- `resource`: Resource being accessed
- `action`: Action performed
- `timestamp`: Event timestamp
- `success`: Success/failure
- `ip_address`: Source IP (if available)

**Example**:
```python
logger.audit(
    event_type='review_created',
    user_id='user@example.com',
    resource='review/abc123',
    action='create',
    pr_number=123,
    repository='org/repo'
)
```

### Security Event Logging

**Events Logged**:
- Invalid webhook signatures
- Unauthorized access attempts
- Failed authentication
- Suspicious activity

**Example**:
```python
logger.security_event(
    event_type='webhook_signature_invalid',
    severity='high',
    source_ip='1.2.3.4'
)
```

## Error Handling

### Error Response Format

```json
{
  "error": "Error type",
  "message": "Detailed error message",
  "trace_id": "correlation-id"
}
```

### Error Categories

1. **Client Errors (4xx)**:
   - Invalid JSON
   - Missing required fields
   - Invalid parameters
   - Not found

2. **Server Errors (5xx)**:
   - Internal errors
   - Service unavailable
   - Timeout
   - Database errors

### Error Logging

**All errors logged with**:
- Error type
- Error message
- Stack trace
- Context (review_id, user_id, etc.)
- Trace ID

## IAM Policies

### Lambda Execution Role

**Policies Attached**:
1. **DynamoDB Access**:
   - `PutItem`, `GetItem`, `UpdateItem`, `Query`, `Scan`
   - Resource: Table and indexes

2. **Secrets Manager**:
   - `GetSecretValue`, `DescribeSecret`
   - Resource: Specific secrets

3. **Bedrock**:
   - `InvokeModel`
   - Resource: Specific model ARNs

4. **Lambda Invoke**:
   - `InvokeFunction`
   - Resource: Other Lambda functions

5. **CloudWatch Logs**:
   - `CreateLogGroup`, `CreateLogStream`, `PutLogEvents`
   - Resource: All logs

### Least Privilege

**Principle**: Each function has minimum required permissions

**Implementation**:
- Resource-specific ARNs
- Condition keys where applicable
- No wildcard permissions (except logs)

## SOC2 Logging Requirements

### CC2 - Communication and Information

**Requirement**: System captures and communicates information

**Implementation**:
- Structured JSON logs
- All API calls logged
- Request/response logging
- Error logging

### CC4 - Monitoring Activities

**Requirement**: System monitors activities

**Implementation**:
- Performance metrics
- Error rates
- Security events
- Audit trail

### CC6 - Logical and Physical Access

**Requirement**: System restricts access

**Implementation**:
- Audit logs for all access
- Security event logging
- Failed access attempts logged
- User attribution

### Evidence Collection

**Automated**:
- CloudTrail (all API calls)
- CloudWatch Logs (application logs)
- DynamoDB access logs
- Lambda execution logs

**Retention**:
- CloudWatch Logs: 30 days
- CloudTrail: 90 days (S3)
- DynamoDB: Point-in-time recovery

## Performance Characteristics

### Latency Targets

- API Handler: < 100ms (p95)
- PR Review Handler: < 200ms (p95)
- Webhook Handlers: < 500ms (p95)
- AI Reviewer: < 30s (p95)
- Historical Analysis: < 5s (p95)

### Throughput

- API Gateway: 10,000 req/sec
- Lambda: Auto-scaling
- DynamoDB: On-demand capacity

## Monitoring

### CloudWatch Metrics

**Custom Metrics**:
- Request count
- Error rate
- Latency
- Review creation rate
- AI review duration

### Alarms

**Critical Alarms**:
- Error rate > 5%
- Latency > 1s (p95)
- Failed reviews > 10%
- Security events

## Best Practices

1. **Always log requests/responses**
2. **Include trace IDs for correlation**
3. **Audit all data modifications**
4. **Log security events immediately**
5. **Use structured logging (JSON)**
6. **Handle errors gracefully**
7. **Validate all inputs**
8. **Use least privilege IAM**

