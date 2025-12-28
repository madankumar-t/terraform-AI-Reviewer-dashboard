# DynamoDB Single-Table Schema Design

## Overview

This document describes the complete DynamoDB single-table design for the Terraform + Spacelift AI Reviewer system. The design follows DynamoDB best practices for single-table design, ensuring efficient queries, immutability, and compliance requirements.

## Table Structure

### Table Name
`terraform-spacelift-ai-reviewer-reviews-{environment}`

### Primary Key
- **Partition Key (PK)**: `String` - Composite entity identifier
- **Sort Key (SK)**: `String` - Version and timestamp identifier

### Global Secondary Indexes (GSIs)

1. **GSI1**: Stack History Index
   - **GSI1PK**: Stack identifier
   - **GSI1SK**: Timestamp for chronological ordering

2. **GSI2**: Risk Trends Index
   - **GSI2PK**: Risk category and date
   - **GSI2SK**: Risk score for sorting

3. **GSI3**: Repeated Issues Index
   - **GSI3PK**: Finding category and hash
   - **GSI3SK**: Timestamp for frequency analysis

4. **GSI4**: Status and Time Index
   - **GSI4PK**: Status value
   - **GSI4SK**: Timestamp for status-based queries

## Primary Key Strategy

### PK (Partition Key) Patterns

```
REVIEW#{review_id}                    - Individual review record
STACK#{stack_id}                      - Stack-level aggregations
FINDING#{finding_id}                  - Individual finding records
ISSUE#{issue_hash}                    - Repeated issue tracking
RUN#{spacelift_run_id}                - Run-level records
```

### SK (Sort Key) Patterns

```
VERSION#{version_number}              - Versioned review records
METADATA                              - Metadata records
STATS                                 - Statistics records
CREATED#{iso_timestamp}               - Timestamp-based ordering
```

## Item Structure

### Core Attributes

All items include:
- `PK`: Partition key
- `SK`: Sort key
- `GSI1PK`: Stack history index key
- `GSI1SK`: Stack history sort key
- `GSI2PK`: Risk trends index key
- `GSI2SK`: Risk trends sort key
- `GSI3PK`: Repeated issues index key
- `GSI3SK`: Repeated issues sort key
- `GSI4PK`: Status index key
- `GSI4SK`: Status sort key
- `EntityType`: Entity type discriminator
- `CreatedAt`: ISO 8601 timestamp
- `UpdatedAt`: ISO 8601 timestamp
- `TTL`: Time-to-live (optional, for archival)

## Entity Types

### 1. Review Entity

**Purpose**: Main review record with versioning

**PK/SK Pattern**:
- `PK`: `REVIEW#{review_id}`
- `SK`: `VERSION#{version_number}`

**Attributes**:
```json
{
  "PK": "REVIEW#550e8400-e29b-41d4-a716-446655440000",
  "SK": "VERSION#1",
  "GSI1PK": "STACK#prod-stack-001",
  "GSI1SK": "CREATED#2024-01-15T10:30:00Z",
  "GSI2PK": "RISK#2024-01-15",
  "GSI2SK": "0.72",
  "GSI3PK": "ISSUE#CATEGORY#security",
  "GSI3SK": "CREATED#2024-01-15T10:30:00Z",
  "GSI4PK": "STATUS#completed",
  "GSI4SK": "CREATED#2024-01-15T10:31:00Z",
  "EntityType": "REVIEW",
  "ReviewId": "550e8400-e29b-41d4-a716-446655440000",
  "Version": 1,
  "PreviousVersionId": null,
  "SpaceliftRunId": "run-abc123",
  "StackId": "prod-stack-001",
  "TerraformCode": "resource \"aws_s3_bucket\" \"example\" {...}",
  "Status": "completed",
  "OverallRiskScore": 0.72,
  "SecurityFindings": {
    "total": 3,
    "high": 2,
    "medium": 1,
    "low": 0
  },
  "CostAnalysis": {
    "estimatedMonthlyCost": 1200.50,
    "estimatedAnnualCost": 14406.00,
    "resourceCount": 5
  },
  "ReliabilityScore": 0.65,
  "AIReviewResult": {
    "security_analysis": {...},
    "cost_analysis": {...},
    "reliability_analysis": {...},
    "fix_suggestions": [...]
  },
  "SpaceliftContext": {
    "run_id": "run-abc123",
    "stack_id": "prod-stack-001",
    "status": "FINISHED",
    "previous_status": "TRACKED",
    "changed_files": ["main.tf", "variables.tf"],
    "commit_sha": "abc123def456",
    "branch": "main"
  },
  "CreatedAt": "2024-01-15T10:30:00Z",
  "UpdatedAt": "2024-01-15T10:31:00Z",
  "CreatedBy": "user@example.com",
  "Metadata": {
    "model_used": "gpt-4-turbo",
    "review_duration_ms": 4500,
    "code_length": 1250
  }
}
```

### 2. Finding Entity

**Purpose**: Individual finding records for repeated issue tracking

**PK/SK Pattern**:
- `PK`: `FINDING#{finding_id}`
- `SK`: `REVIEW#{review_id}`

**Attributes**:
```json
{
  "PK": "FINDING#find-001",
  "SK": "REVIEW#550e8400-e29b-41d4-a716-446655440000",
  "GSI1PK": "STACK#prod-stack-001",
  "GSI1SK": "CREATED#2024-01-15T10:30:00Z",
  "GSI2PK": "RISK#2024-01-15",
  "GSI2SK": "0.95",
  "GSI3PK": "ISSUE#CATEGORY#security#HASH#abc123",
  "GSI3SK": "CREATED#2024-01-15T10:30:00Z",
  "EntityType": "FINDING",
  "FindingId": "find-001",
  "ReviewId": "550e8400-e29b-41d4-a716-446655440000",
  "Category": "security",
  "Severity": "high",
  "Title": "Public S3 Bucket",
  "Description": "S3 bucket is publicly accessible",
  "LineNumber": 5,
  "FilePath": "main.tf",
  "Recommendation": "Add public access block",
  "IssueHash": "abc123",  // Hash of title + category + file_path
  "ConfidenceScore": 0.95,
  "CreatedAt": "2024-01-15T10:30:00Z"
}
```

### 3. Stack Statistics Entity

**Purpose**: Aggregated statistics per stack

**PK/SK Pattern**:
- `PK`: `STACK#{stack_id}`
- `SK`: `STATS`

**Attributes**:
```json
{
  "PK": "STACK#prod-stack-001",
  "SK": "STATS",
  "GSI1PK": "STACK#prod-stack-001",
  "GSI1SK": "STATS",
  "EntityType": "STACK_STATS",
  "StackId": "prod-stack-001",
  "TotalReviews": 150,
  "AverageRiskScore": 0.45,
  "HighRiskCount": 20,
  "MediumRiskCount": 50,
  "LowRiskCount": 80,
  "TotalFindings": 450,
  "SecurityFindings": 200,
  "CostFindings": 150,
  "ReliabilityFindings": 100,
  "LastReviewDate": "2024-01-15T10:30:00Z",
  "UpdatedAt": "2024-01-15T10:30:00Z"
}
```

### 4. Issue Frequency Entity

**Purpose**: Track repeated issues across runs

**PK/SK Pattern**:
- `PK`: `ISSUE#{issue_hash}`
- `SK`: `STACK#{stack_id}`

**Attributes**:
```json
{
  "PK": "ISSUE#abc123",
  "SK": "STACK#prod-stack-001",
  "GSI1PK": "STACK#prod-stack-001",
  "GSI1SK": "ISSUE#abc123",
  "GSI3PK": "ISSUE#CATEGORY#security#HASH#abc123",
  "GSI3SK": "FREQ#15",
  "EntityType": "ISSUE_FREQUENCY",
  "IssueHash": "abc123",
  "StackId": "prod-stack-001",
  "Category": "security",
  "Title": "Public S3 Bucket",
  "OccurrenceCount": 15,
  "FirstSeen": "2024-01-01T00:00:00Z",
  "LastSeen": "2024-01-15T10:30:00Z",
  "AffectedRuns": ["run-001", "run-002", "run-003"],
  "FixApplied": false,
  "UpdatedAt": "2024-01-15T10:30:00Z"
}
```

## Versioning Logic

### Version Numbering

- **Version 1**: Initial review creation
- **Version 2+**: Updates (status changes, fix applications, re-reviews)
- **Immutable**: Previous versions are never modified

### Version Creation Flow

```
1. Create Review (Version 1)
   PK: REVIEW#{review_id}
   SK: VERSION#1
   PreviousVersionId: null

2. Update Review (Version 2)
   PK: REVIEW#{review_id}
   SK: VERSION#2
   PreviousVersionId: REVIEW#{review_id}#VERSION#1

3. Apply Fix (Version 3)
   PK: REVIEW#{review_id}
   SK: VERSION#3
   PreviousVersionId: REVIEW#{review_id}#VERSION#2
   FixApplied: true
   FixDetails: {...}
```

### Version Query Pattern

```python
# Get latest version
response = table.query(
    KeyConditionExpression='PK = :pk',
    ExpressionAttributeValues={':pk': f'REVIEW#{review_id}'},
    ScanIndexForward=False,  # Descending order
    Limit=1
)

# Get all versions
response = table.query(
    KeyConditionExpression='PK = :pk',
    ExpressionAttributeValues={':pk': f'REVIEW#{review_id}'},
    ScanIndexForward=True  # Ascending order
)

# Get specific version
response = table.get_item(
    Key={
        'PK': f'REVIEW#{review_id}',
        'SK': f'VERSION#{version_number}'
    }
)
```

## Immutability Enforcement

### Application-Level Enforcement

1. **No Update Operations**: Only use `PutItem` for new versions
2. **Conditional Writes**: Prevent accidental overwrites
3. **Version Validation**: Ensure version numbers are sequential
4. **Audit Logging**: Log all write operations

### Conditional Write Example

```python
# Prevent overwriting existing version
table.put_item(
    Item={
        'PK': f'REVIEW#{review_id}',
        'SK': f'VERSION#{new_version}',
        # ... other attributes
    },
    ConditionExpression='attribute_not_exists(PK)'
)
```

### DynamoDB-Level Enforcement

While DynamoDB doesn't enforce immutability natively, we use:
- **TTL Attribute**: For archival (optional)
- **Point-in-Time Recovery**: For accidental deletion recovery
- **Backup Policies**: Regular automated backups

## Global Secondary Indexes

### GSI1: Stack History Index

**Purpose**: Query reviews by stack in chronological order

**Key Structure**:
- `GSI1PK`: `STACK#{stack_id}`
- `GSI1SK`: `CREATED#{iso_timestamp}`

**Access Patterns**:
1. Get all reviews for a stack (chronological)
2. Get reviews for a stack in date range
3. Get latest review for a stack

**Query Example**:
```python
# Get all reviews for a stack
response = table.query(
    IndexName='GSI1',
    KeyConditionExpression='GSI1PK = :gsi1pk',
    ExpressionAttributeValues={
        ':gsi1pk': f'STACK#{stack_id}'
    },
    ScanIndexForward=False  # Most recent first
)

# Get reviews in date range
response = table.query(
    IndexName='GSI1',
    KeyConditionExpression='GSI1PK = :gsi1pk AND GSI1SK BETWEEN :start AND :end',
    ExpressionAttributeValues={
        ':gsi1pk': f'STACK#{stack_id}',
        ':start': 'CREATED#2024-01-01T00:00:00Z',
        ':end': 'CREATED#2024-01-31T23:59:59Z'
    }
)
```

### GSI2: Risk Trends Index

**Purpose**: Analyze risk trends over time

**Key Structure**:
- `GSI2PK`: `RISK#{date}` (e.g., `RISK#2024-01-15`)
- `GSI2SK`: Risk score as string (for sorting)

**Access Patterns**:
1. Get risk distribution for a date
2. Get high-risk reviews for a date
3. Analyze risk trends over time period

**Query Example**:
```python
# Get high-risk reviews for a date (risk >= 0.7)
response = table.query(
    IndexName='GSI2',
    KeyConditionExpression='GSI2PK = :gsi2pk AND GSI2SK >= :min_risk',
    ExpressionAttributeValues={
        ':gsi2pk': 'RISK#2024-01-15',
        ':min_risk': '0.7'
    }
)

# Get risk trend over date range
dates = ['RISK#2024-01-01', 'RISK#2024-01-02', ...]
for date in dates:
    response = table.query(
        IndexName='GSI2',
        KeyConditionExpression='GSI2PK = :gsi2pk',
        ExpressionAttributeValues={':gsi2pk': date}
    )
```

### GSI3: Repeated Issues Index

**Purpose**: Track and identify repeated issues

**Key Structure**:
- `GSI3PK`: `ISSUE#CATEGORY#{category}#HASH#{issue_hash}`
- `GSI3SK`: Timestamp or frequency count

**Access Patterns**:
1. Find all occurrences of a specific issue
2. Get most frequent issues by category
3. Track issue resolution over time

**Query Example**:
```python
# Find all occurrences of a specific issue
response = table.query(
    IndexName='GSI3',
    KeyConditionExpression='GSI3PK = :gsi3pk',
    ExpressionAttributeValues={
        ':gsi3pk': f'ISSUE#CATEGORY#security#HASH#abc123'
    }
)

# Get most frequent issues (using issue frequency entity)
response = table.query(
    IndexName='GSI3',
    KeyConditionExpression='GSI3PK = :gsi3pk',
    ExpressionAttributeValues={
        ':gsi3pk': 'ISSUE#CATEGORY#security'
    },
    ScanIndexForward=False  # Highest frequency first
)
```

### GSI4: Status and Time Index

**Purpose**: Query reviews by status

**Key Structure**:
- `GSI4PK`: `STATUS#{status}` (e.g., `STATUS#completed`)
- `GSI4SK`: `CREATED#{iso_timestamp}`

**Access Patterns**:
1. Get all completed reviews
2. Get pending reviews
3. Get failed reviews for investigation

**Query Example**:
```python
# Get all completed reviews
response = table.query(
    IndexName='GSI4',
    KeyConditionExpression='GSI4PK = :gsi4pk',
    ExpressionAttributeValues={
        ':gsi4pk': 'STATUS#completed'
    },
    ScanIndexForward=False  # Most recent first
)

# Get pending reviews older than 1 hour
one_hour_ago = (datetime.utcnow() - timedelta(hours=1)).isoformat()
response = table.query(
    IndexName='GSI4',
    KeyConditionExpression='GSI4PK = :gsi4pk AND GSI4SK < :timestamp',
    ExpressionAttributeValues={
        ':gsi4pk': 'STATUS#pending',
        ':timestamp': f'CREATED#{one_hour_ago}'
    }
)
```

## Example Items

### Example 1: Initial Run (Version 1)

```json
{
  "PK": "REVIEW#550e8400-e29b-41d4-a716-446655440000",
  "SK": "VERSION#1",
  "GSI1PK": "STACK#prod-stack-001",
  "GSI1SK": "CREATED#2024-01-15T10:30:00Z",
  "GSI2PK": "RISK#2024-01-15",
  "GSI2SK": "0.72",
  "GSI3PK": "ISSUE#CATEGORY#security",
  "GSI3SK": "CREATED#2024-01-15T10:30:00Z",
  "GSI4PK": "STATUS#completed",
  "GSI4SK": "CREATED#2024-01-15T10:31:00Z",
  "EntityType": "REVIEW",
  "ReviewId": "550e8400-e29b-41d4-a716-446655440000",
  "Version": 1,
  "PreviousVersionId": null,
  "SpaceliftRunId": "run-abc123",
  "StackId": "prod-stack-001",
  "TerraformCode": "resource \"aws_s3_bucket\" \"example\" {\n  bucket = \"my-bucket\"\n}",
  "Status": "completed",
  "OverallRiskScore": 0.72,
  "SecurityFindings": {
    "total": 3,
    "high": 2,
    "medium": 1,
    "low": 0,
    "findings": [
      {
        "finding_id": "find-001",
        "category": "security",
        "severity": "high",
        "title": "Public S3 Bucket",
        "description": "S3 bucket is publicly accessible without proper access controls",
        "line_number": 5,
        "file_path": "main.tf",
        "recommendation": "Add aws_s3_bucket_public_access_block resource",
        "confidence_score": 0.95
      }
    ]
  },
  "CostAnalysis": {
    "estimatedMonthlyCost": 1200.50,
    "estimatedAnnualCost": 14406.00,
    "resourceCount": 5,
    "costOptimizations": [
      {
        "finding_id": "cost-001",
        "category": "cost",
        "severity": "medium",
        "title": "Over-Provisioned Instance",
        "estimated_cost_impact": 800.00
      }
    ]
  },
  "ReliabilityScore": 0.65,
  "SpaceliftContext": {
    "run_id": "run-abc123",
    "stack_id": "prod-stack-001",
    "status": "FINISHED",
    "previous_status": "TRACKED",
    "changed_files": ["main.tf"],
    "commit_sha": "abc123def456",
    "branch": "main"
  },
  "CreatedAt": "2024-01-15T10:30:00Z",
  "UpdatedAt": "2024-01-15T10:31:00Z",
  "CreatedBy": "system@spacelift",
  "Metadata": {
    "model_used": "gpt-4-turbo",
    "review_duration_ms": 4500,
    "code_length": 1250
  }
}
```

### Example 2: Failed Run (Version 1)

```json
{
  "PK": "REVIEW#660e8400-e29b-41d4-a716-446655440001",
  "SK": "VERSION#1",
  "GSI1PK": "STACK#prod-stack-001",
  "GSI1SK": "CREATED#2024-01-15T11:00:00Z",
  "GSI2PK": "RISK#2024-01-15",
  "GSI2SK": "1.0",
  "GSI3PK": "ISSUE#CATEGORY#error",
  "GSI3SK": "CREATED#2024-01-15T11:00:00Z",
  "GSI4PK": "STATUS#failed",
  "GSI4SK": "CREATED#2024-01-15T11:01:00Z",
  "EntityType": "REVIEW",
  "ReviewId": "660e8400-e29b-41d4-a716-446655440001",
  "Version": 1,
  "PreviousVersionId": null,
  "SpaceliftRunId": "run-xyz789",
  "StackId": "prod-stack-001",
  "TerraformCode": "resource \"aws_s3_bucket\" \"example\" {...}",
  "Status": "failed",
  "OverallRiskScore": null,
  "ErrorDetails": {
    "error_type": "AI_SERVICE_ERROR",
    "error_message": "OpenAI API rate limit exceeded",
    "error_code": "RATE_LIMIT",
    "retry_after": 60,
    "stack_trace": "..."
  },
  "SpaceliftContext": {
    "run_id": "run-xyz789",
    "stack_id": "prod-stack-001",
    "status": "FAILED",
    "previous_status": "TRACKED",
    "changed_files": ["main.tf"],
    "commit_sha": "def456ghi789",
    "branch": "main"
  },
  "CreatedAt": "2024-01-15T11:00:00Z",
  "UpdatedAt": "2024-01-15T11:01:00Z",
  "CreatedBy": "system@spacelift",
  "Metadata": {
    "failure_reason": "AI service unavailable",
    "retry_count": 0
  }
}
```

### Example 3: Fix-Applied Run (Version 3)

```json
{
  "PK": "REVIEW#550e8400-e29b-41d4-a716-446655440000",
  "SK": "VERSION#3",
  "GSI1PK": "STACK#prod-stack-001",
  "GSI1SK": "CREATED#2024-01-16T10:30:00Z",
  "GSI2PK": "RISK#2024-01-16",
  "GSI2SK": "0.35",
  "GSI3PK": "ISSUE#CATEGORY#security",
  "GSI3SK": "CREATED#2024-01-16T10:30:00Z",
  "GSI4PK": "STATUS#completed",
  "GSI4SK": "CREATED#2024-01-16T10:31:00Z",
  "EntityType": "REVIEW",
  "ReviewId": "550e8400-e29b-41d4-a716-446655440000",
  "Version": 3,
  "PreviousVersionId": "REVIEW#550e8400-e29b-41d4-a716-446655440000#VERSION#2",
  "SpaceliftRunId": "run-def456",
  "StackId": "prod-stack-001",
  "TerraformCode": "resource \"aws_s3_bucket\" \"example\" {\n  bucket = \"my-bucket\"\n}\n\nresource \"aws_s3_bucket_public_access_block\" \"example\" {\n  bucket = aws_s3_bucket.example.id\n  block_public_acls = true\n  block_public_policy = true\n  ignore_public_acls = true\n  restrict_public_buckets = true\n}",
  "Status": "completed",
  "OverallRiskScore": 0.35,
  "FixApplied": true,
  "FixDetails": {
    "fix_version": 3,
    "previous_version": 2,
    "fixes_applied": [
      {
        "finding_id": "find-001",
        "fix_id": "fix-001",
        "original_code": "resource \"aws_s3_bucket\" \"example\" {...}",
        "applied_code": "resource \"aws_s3_bucket\" \"example\" {...}\nresource \"aws_s3_bucket_public_access_block\" {...}",
        "effectiveness_score": 0.95,
        "applied_at": "2024-01-16T10:30:00Z"
      }
    ],
    "risk_reduction": 0.37,
    "findings_resolved": 2,
    "findings_remaining": 1
  },
  "SecurityFindings": {
    "total": 1,
    "high": 0,
    "medium": 1,
    "low": 0,
    "findings": [
      {
        "finding_id": "find-002",
        "category": "security",
        "severity": "medium",
        "title": "Missing Encryption",
        "description": "S3 bucket does not have encryption enabled",
        "line_number": 5,
        "file_path": "main.tf",
        "recommendation": "Enable server-side encryption",
        "confidence_score": 0.90
      }
    ]
  },
  "CostAnalysis": {
    "estimatedMonthlyCost": 1200.50,
    "estimatedAnnualCost": 14406.00,
    "resourceCount": 6,
    "costOptimizations": []
  },
  "ReliabilityScore": 0.75,
  "SpaceliftContext": {
    "run_id": "run-def456",
    "stack_id": "prod-stack-001",
    "status": "FINISHED",
    "previous_status": "FINISHED",
    "changed_files": ["main.tf"],
    "commit_sha": "ghi789jkl012",
    "branch": "main"
  },
  "CreatedAt": "2024-01-16T10:30:00Z",
  "UpdatedAt": "2024-01-16T10:31:00Z",
  "CreatedBy": "system@spacelift",
  "Metadata": {
    "model_used": "gpt-4-turbo",
    "review_duration_ms": 4200,
    "code_length": 1450,
    "fix_effectiveness": 0.95
  }
}
```

## Access Patterns

### Pattern 1: Get Latest Review for a Run

```python
def get_latest_review_by_run(spacelift_run_id):
    # Query by Spacelift run ID (requires GSI or scan)
    # Alternative: Store run_id in GSI1PK for direct lookup
    response = table.query(
        IndexName='GSI1',
        KeyConditionExpression='GSI1PK = :gsi1pk',
        FilterExpression='SpaceliftRunId = :run_id',
        ExpressionAttributeValues={
            ':gsi1pk': f'RUN#{spacelift_run_id}',
            ':run_id': spacelift_run_id
        },
        ScanIndexForward=False,
        Limit=1
    )
    return response['Items'][0] if response['Items'] else None
```

### Pattern 2: Get All Versions of a Review

```python
def get_review_versions(review_id):
    response = table.query(
        KeyConditionExpression='PK = :pk',
        ExpressionAttributeValues={
            ':pk': f'REVIEW#{review_id}'
        },
        ScanIndexForward=True  # Chronological order
    )
    return response['Items']
```

### Pattern 3: Get Stack History

```python
def get_stack_history(stack_id, limit=50):
    response = table.query(
        IndexName='GSI1',
        KeyConditionExpression='GSI1PK = :gsi1pk',
        ExpressionAttributeValues={
            ':gsi1pk': f'STACK#{stack_id}'
        },
        ScanIndexForward=False,  # Most recent first
        Limit=limit
    )
    return response['Items']
```

### Pattern 4: Get High-Risk Reviews for Date Range

```python
def get_high_risk_reviews(start_date, end_date, min_risk=0.7):
    reviews = []
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        response = table.query(
            IndexName='GSI2',
            KeyConditionExpression='GSI2PK = :gsi2pk AND GSI2SK >= :min_risk',
            ExpressionAttributeValues={
                ':gsi2pk': f'RISK#{date_str}',
                ':min_risk': str(min_risk)
            }
        )
        reviews.extend(response['Items'])
        current_date += timedelta(days=1)
    return reviews
```

### Pattern 5: Find Repeated Issues

```python
def get_repeated_issues(stack_id, min_occurrences=3):
    response = table.query(
        IndexName='GSI3',
        KeyConditionExpression='GSI3PK = :gsi3pk',
        ExpressionAttributeValues={
            ':gsi3pk': f'ISSUE#STACK#{stack_id}'
        }
    )
    # Filter by occurrence count
    return [
        item for item in response['Items']
        if item.get('OccurrenceCount', 0) >= min_occurrences
    ]
```

### Pattern 6: Get Pending Reviews

```python
def get_pending_reviews(older_than_minutes=60):
    cutoff_time = (datetime.utcnow() - timedelta(minutes=older_than_minutes)).isoformat()
    response = table.query(
        IndexName='GSI4',
        KeyConditionExpression='GSI4PK = :gsi4pk AND GSI4SK < :cutoff',
        ExpressionAttributeValues={
            ':gsi4pk': 'STATUS#pending',
            ':cutoff': f'CREATED#{cutoff_time}'
        }
    )
    return response['Items']
```

## Hot Partition Avoidance

### Strategy 1: Partition Key Design

**Problem**: All reviews for a popular stack hitting same partition

**Solution**: Include date/time component in partition key for time-based queries

```python
# Instead of: STACK#{stack_id}
# Use: STACK#{stack_id}#DATE#{date}
GSI1PK = f"STACK#{stack_id}#DATE#{date}"
```

### Strategy 2: Write Sharding

**Problem**: High write volume to single partition

**Solution**: Distribute writes across partitions using random suffix

```python
# For high-volume writes, add random suffix
import random
suffix = random.randint(0, 9)
GSI1PK = f"STACK#{stack_id}#SHARD#{suffix}"
```

### Strategy 3: Read Distribution

**Problem**: Hot reads on recent data

**Solution**: Use consistent read distribution and caching

```python
# Use eventually consistent reads for non-critical queries
response = table.query(
    ...,
    ConsistentRead=False  # Eventually consistent
)

# Cache frequently accessed data
# Use CloudFront or ElastiCache for hot data
```

### Strategy 4: GSI Projection Strategy

**Minimize GSI size** to reduce write amplification:

```python
# Only project necessary attributes to GSI
GSIProjection = {
    'ProjectionType': 'INCLUDE',
    'NonKeyAttributes': ['Status', 'RiskScore']  # Only essential fields
}
```

## Compliance & Audit Guarantees

### 1. Immutability

**Guarantee**: Once written, records are never modified

**Implementation**:
- Version-based writes only
- No `UpdateItem` operations
- Conditional writes prevent overwrites
- Point-in-time recovery enabled

**Evidence**:
- CloudTrail logs all write operations
- Version history preserved
- No update operations in logs

### 2. Audit Trail

**Guarantee**: Complete history of all changes

**Implementation**:
- Every version stored
- Previous version ID tracked
- Timestamps on all records
- CreatedBy attribute for attribution

**Evidence**:
```python
# Query full audit trail
def get_audit_trail(review_id):
    versions = get_review_versions(review_id)
    trail = []
    for version in versions:
        trail.append({
            'version': version['Version'],
            'timestamp': version['CreatedAt'],
            'changed_by': version.get('CreatedBy'),
            'changes': diff_versions(version, previous_version)
        })
    return trail
```

### 3. Data Retention

**Guarantee**: Data retained per compliance requirements

**Implementation**:
- TTL attribute for archival (optional)
- Point-in-time recovery (35 days default)
- Automated backups
- Glacier archival for long-term retention

**Configuration**:
```python
# Set TTL for archival (7 years for compliance)
ttl_timestamp = int((datetime.utcnow() + timedelta(days=2555)).timestamp())
item['TTL'] = ttl_timestamp
```

### 4. Access Logging

**Guarantee**: All access logged and auditable

**Implementation**:
- CloudTrail logs all API calls
- DynamoDB Streams for change data capture
- Access patterns logged
- Unauthorized access attempts logged

**Monitoring**:
```python
# CloudTrail event example
{
    "eventTime": "2024-01-15T10:30:00Z",
    "eventName": "QueryTable",
    "userIdentity": {
        "type": "AssumedRole",
        "arn": "arn:aws:sts::123456789012:assumed-role/LambdaExecutionRole/..."
    },
    "requestParameters": {
        "tableName": "terraform-spacelift-ai-reviewer-reviews-prod",
        "keyConditionExpression": "PK = :pk"
    }
}
```

### 5. Encryption

**Guarantee**: All data encrypted at rest and in transit

**Implementation**:
- KMS CMK for encryption at rest
- TLS 1.2+ for encryption in transit
- VPC endpoints for private connectivity
- Key rotation enabled

**Configuration**:
```python
# DynamoDB table with KMS encryption
table_config = {
    'SSESpecification': {
        'Enabled': True,
        'SSEType': 'KMS',
        'KMSMasterKeyId': 'arn:aws:kms:us-east-1:123456789012:key/abc-123'
    }
}
```

### 6. Access Control

**Guarantee**: Least privilege access enforced

**Implementation**:
- IAM policies with resource-based conditions
- Tag-based access control
- VPC endpoint policies
- Cross-account access via roles

**Policy Example**:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:Query",
        "dynamodb:GetItem"
      ],
      "Resource": "arn:aws:dynamodb:*:*:table/terraform-*",
      "Condition": {
        "StringEquals": {
          "dynamodb:LeadingKeys": "${aws:userid}"
        }
      }
    }
  ]
}
```

## Best Practices

### 1. Item Size Management

- Keep items under 400 KB
- Store large Terraform code in S3, reference in DynamoDB
- Use compression for large text fields

### 2. Query Optimization

- Use specific partition keys
- Limit result sets
- Use projection expressions
- Implement pagination

### 3. Write Optimization

- Batch writes where possible
- Use conditional writes
- Minimize GSI projections
- Use eventually consistent reads for non-critical queries

### 4. Monitoring

- Monitor read/write capacity
- Track hot partitions
- Monitor GSI lag
- Set up CloudWatch alarms

## Summary

This single-table design provides:
- ✅ Efficient queries via GSIs
- ✅ Immutable version history
- ✅ Compliance-ready audit trail
- ✅ Hot partition avoidance
- ✅ Scalable architecture
- ✅ Complete audit guarantees

The design supports all required access patterns while maintaining data integrity, compliance, and performance.

