# Example API Payloads

This document contains example request and response payloads for the API.

## Create Review Request

### POST /api/reviews

```json
{
  "terraform_code": "resource \"aws_s3_bucket\" \"example\" {\n  bucket = \"my-bucket\"\n}",
  "spacelift_run_id": "run-abc123",
  "spacelift_context": {
    "run_id": "run-abc123",
    "stack_id": "production-stack",
    "status": "TRACKED",
    "previous_status": "FINISHED",
    "changed_files": ["main.tf", "variables.tf"],
    "commit_sha": "abc123def456",
    "branch": "main"
  }
}
```

### Response

```json
{
  "review_id": "550e8400-e29b-41d4-a716-446655440000",
  "terraform_code": "resource \"aws_s3_bucket\" \"example\" {\n  bucket = \"my-bucket\"\n}",
  "spacelift_run_id": "run-abc123",
  "spacelift_context": {
    "run_id": "run-abc123",
    "stack_id": "production-stack",
    "status": "TRACKED"
  },
  "status": "pending",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "version": 1
}
```

## Get Review Response

### GET /api/reviews/{reviewId}

```json
{
  "review_id": "550e8400-e29b-41d4-a716-446655440000",
  "terraform_code": "resource \"aws_s3_bucket\" \"example\" {\n  bucket = \"my-bucket\"\n}",
  "spacelift_run_id": "run-abc123",
  "spacelift_context": {},
  "status": "completed",
  "ai_review_result": {
    "review_id": "550e8400-e29b-41d4-a716-446655440000",
    "security_analysis": {
      "total_findings": 3,
      "high_severity": 2,
      "medium_severity": 1,
      "low_severity": 0,
      "findings": [
        {
          "finding_id": "find-001",
          "category": "security",
          "severity": "high",
          "title": "Public S3 Bucket",
          "description": "S3 bucket is publicly accessible without proper access controls",
          "line_number": 1,
          "file_path": "main.tf",
          "recommendation": "Add aws_s3_bucket_public_access_block resource to restrict public access",
          "confidence_score": 0.95
        },
        {
          "finding_id": "find-002",
          "category": "security",
          "severity": "high",
          "title": "Overly Permissive IAM Policy",
          "description": "IAM policy allows all actions on all resources",
          "line_number": 15,
          "file_path": "main.tf",
          "recommendation": "Follow principle of least privilege - restrict actions and resources",
          "confidence_score": 0.98
        }
      ]
    },
    "cost_analysis": {
      "estimated_monthly_cost": 1200.50,
      "estimated_annual_cost": 14406.00,
      "resource_count": 5,
      "cost_optimizations": [
        {
          "finding_id": "cost-001",
          "category": "cost",
          "severity": "medium",
          "title": "Over-Provisioned Instance",
          "description": "Using m5.24xlarge instance type which may be over-provisioned",
          "line_number": 20,
          "file_path": "main.tf",
          "recommendation": "Consider using smaller instance type or auto-scaling group",
          "estimated_cost_impact": 800.00,
          "confidence_score": 0.85
        }
      ]
    },
    "reliability_analysis": {
      "reliability_score": 0.65,
      "single_points_of_failure": [
        {
          "finding_id": "rel-001",
          "category": "reliability",
          "severity": "medium",
          "title": "No Backup Strategy",
          "description": "No backup or disaster recovery configuration found",
          "recommendation": "Implement automated backups and disaster recovery plan",
          "confidence_score": 0.90
        }
      ],
      "recommendations": [
        "Add health checks for critical resources",
        "Implement multi-AZ deployment",
        "Add monitoring and alerting"
      ]
    },
    "overall_risk_score": 0.72,
    "fix_suggestions": [
      {
        "fix_id": "fix-001",
        "finding_id": "find-001",
        "original_code": "resource \"aws_s3_bucket\" \"example\" {\n  bucket = \"my-bucket\"\n}",
        "suggested_code": "resource \"aws_s3_bucket\" \"example\" {\n  bucket = \"my-bucket\"\n}\n\nresource \"aws_s3_bucket_public_access_block\" \"example\" {\n  bucket = aws_s3_bucket.example.id\n  block_public_acls       = true\n  block_public_policy     = true\n  ignore_public_acls      = true\n  restrict_public_buckets = true\n}",
        "explanation": "Adding public access block prevents accidental public exposure",
        "effectiveness_score": 0.95
      }
    ],
    "review_metadata": {
      "model_used": "gpt-4-turbo",
      "review_timestamp": "2024-01-15T10:31:00Z",
      "code_length": 250
    }
  },
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:31:00Z",
  "version": 1
}
```

## Analytics Response

### GET /api/analytics?days=30

```json
{
  "total_reviews": 150,
  "reviews_by_status": {
    "completed": 120,
    "pending": 10,
    "in_progress": 15,
    "failed": 5
  },
  "reviews_by_risk": {
    "low": 80,
    "medium": 50,
    "high": 20
  },
  "average_risk_score": 0.45,
  "trend_data": [
    {
      "date": "2024-01-01",
      "count": 5
    },
    {
      "date": "2024-01-02",
      "count": 8
    }
  ],
  "top_findings": [
    {
      "title": "Public S3 Bucket",
      "count": 45
    },
    {
      "title": "Overly Permissive IAM Policy",
      "count": 32
    },
    {
      "title": "Missing Encryption",
      "count": 28
    }
  ]
}
```

## Spacelift Webhook Payload

### POST /webhook/spacelift

```json
{
  "event": {
    "type": "run:finished",
    "id": "evt-abc123",
    "timestamp": "2024-01-15T10:30:00Z"
  },
  "run": {
    "id": "run-abc123",
    "state": "FINISHED",
    "previous_state": "TRACKED",
    "stack": {
      "id": "production-stack",
      "name": "Production Stack"
    },
    "commit": {
      "sha": "abc123def456",
      "message": "Update infrastructure"
    },
    "branch": "main",
    "changed_files": ["main.tf", "variables.tf"],
    "terraform": {
      "code": "resource \"aws_s3_bucket\" \"example\" {\n  bucket = \"my-bucket\"\n}"
    }
  }
}
```

## Error Responses

### 400 Bad Request

```json
{
  "error": "Invalid JSON: Expecting property name in JSON at position 5"
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
  "message": "AI service unavailable"
}
```

