# Backend API Reference

## API Endpoints

### Reviews

#### List Reviews
```
GET /api/reviews?spaceliftRunId={id}&status={status}&limit={n}
```

**Query Parameters**:
- `spaceliftRunId` (optional): Filter by Spacelift run ID
- `status` (optional): Filter by status (pending, in_progress, completed, failed)
- `limit` (optional): Maximum results (default: 50)

**Response**:
```json
{
  "reviews": [...],
  "count": 10
}
```

#### Get Review
```
GET /api/reviews/{reviewId}
```

**Response**:
```json
{
  "review_id": "...",
  "status": "completed",
  "ai_review_result": {...}
}
```

#### Create Review
```
POST /api/reviews
```

**Request Body**:
```json
{
  "terraform_code": "...",
  "spacelift_run_id": "run-123",
  "spacelift_context": {...}
}
```

#### Update Review
```
PUT /api/reviews/{reviewId}
```

**Request Body**:
```json
{
  "status": "completed",
  "ai_review_result": {...}
}
```

#### Create PR Review
```
POST /api/reviews/pr
```

**Request Body**:
```json
{
  "terraform_code": "...",
  "pr_number": 123,
  "repository": "org/repo",
  "branch": "main",
  "commit_sha": "abc123",
  "author": "user@example.com",
  "title": "PR Title",
  "changed_files": ["main.tf"]
}
```

### Analytics

#### Get Analytics
```
GET /api/analytics?days={n}
```

**Query Parameters**:
- `days` (optional): Number of days (default: 30)

**Response**:
```json
{
  "total_reviews": 150,
  "reviews_by_status": {...},
  "reviews_by_risk": {...},
  "average_risk_score": 0.45,
  "trend_data": [...],
  "top_findings": [...]
}
```

#### Historical Analysis
```
GET /api/analytics/historical?stack_id={id}&days={n}&analysis_type={type}
```

**Query Parameters**:
- `stack_id` (optional): Filter by stack
- `days` (optional): Number of days (default: 30)
- `analysis_type`: `trends`, `patterns`, or `correlations`

**Response** (trends):
```json
{
  "analysis_type": "trends",
  "period_days": 30,
  "trend_data": [...],
  "summary": {...}
}
```

### Webhooks

#### Spacelift Webhook
```
POST /webhook/spacelift
```

**Headers**:
- `X-Spacelift-Signature`: HMAC SHA256 signature

**Request Body**: Spacelift webhook payload

#### GitHub Webhook
```
POST /webhook/github
```

**Headers**:
- `X-Hub-Signature-256`: HMAC SHA256 signature
- `X-GitHub-Event`: Event type
- `X-GitHub-Delivery`: Delivery ID

**Request Body**: GitHub webhook payload

## Error Responses

### 400 Bad Request
```json
{
  "error": "Invalid JSON",
  "message": "Detailed error message"
}
```

### 401 Unauthorized
```json
{
  "error": "Invalid signature"
}
```

### 404 Not Found
```json
{
  "error": "Review not found"
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error",
  "message": "Error details"
}
```

## Authentication

Currently, webhooks use signature verification. API endpoints may require authentication in production (not implemented in this version).

## Rate Limiting

API Gateway throttling:
- Rate: 100 requests/second
- Burst: 200 requests

## CORS

All endpoints support CORS with:
- `Access-Control-Allow-Origin: *`
- `Access-Control-Allow-Methods: GET,POST,PUT,DELETE,OPTIONS`
- `Access-Control-Allow-Headers: Content-Type,Authorization`

