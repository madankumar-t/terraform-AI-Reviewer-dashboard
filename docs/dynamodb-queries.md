# DynamoDB Query Patterns and Examples

## Common Query Patterns

### 1. Get Latest Review by Review ID

```python
def get_latest_review(review_id):
    """Get the most recent version of a review"""
    response = table.query(
        KeyConditionExpression='PK = :pk',
        ExpressionAttributeValues={
            ':pk': f'REVIEW#{review_id}'
        },
        ScanIndexForward=False,  # Descending order (newest first)
        Limit=1
    )
    return response['Items'][0] if response['Items'] else None
```

### 2. Get All Versions of a Review

```python
def get_all_versions(review_id):
    """Get complete version history for a review"""
    response = table.query(
        KeyConditionExpression='PK = :pk',
        ExpressionAttributeValues={
            ':pk': f'REVIEW#{review_id}'
        },
        ScanIndexForward=True  # Ascending order (oldest first)
    )
    return response['Items']
```

### 3. Get Reviews by Stack (Chronological)

```python
def get_stack_reviews(stack_id, limit=50):
    """Get all reviews for a stack, most recent first"""
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

### 4. Get Reviews by Date Range

```python
def get_reviews_by_date_range(stack_id, start_date, end_date):
    """Get reviews for a stack within date range"""
    response = table.query(
        IndexName='GSI1',
        KeyConditionExpression='GSI1PK = :gsi1pk AND GSI1SK BETWEEN :start AND :end',
        ExpressionAttributeValues={
            ':gsi1pk': f'STACK#{stack_id}',
            ':start': f'CREATED#{start_date.isoformat()}',
            ':end': f'CREATED#{end_date.isoformat()}'
        }
    )
    return response['Items']
```

### 5. Get High-Risk Reviews for a Date

```python
def get_high_risk_reviews(date, min_risk=0.7):
    """Get all high-risk reviews for a specific date"""
    date_str = date.strftime('%Y-%m-%d')
    response = table.query(
        IndexName='GSI2',
        KeyConditionExpression='GSI2PK = :gsi2pk AND GSI2SK >= :min_risk',
        ExpressionAttributeValues={
            ':gsi2pk': f'RISK#{date_str}',
            ':min_risk': str(min_risk)
        }
    )
    return response['Items']
```

### 6. Get Risk Trend Over Time

```python
def get_risk_trend(start_date, end_date):
    """Get risk scores over time period"""
    trend_data = {}
    current_date = start_date
    
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        response = table.query(
            IndexName='GSI2',
            KeyConditionExpression='GSI2PK = :gsi2pk',
            ExpressionAttributeValues={
                ':gsi2pk': f'RISK#{date_str}'
            }
        )
        
        if response['Items']:
            scores = [float(item['GSI2SK']) for item in response['Items']]
            trend_data[date_str] = {
                'count': len(scores),
                'average': sum(scores) / len(scores),
                'max': max(scores),
                'min': min(scores)
            }
        
        current_date += timedelta(days=1)
    
    return trend_data
```

### 7. Find Repeated Issues

```python
def find_repeated_issues(stack_id, category=None, min_occurrences=3):
    """Find issues that occur multiple times"""
    if category:
        gsi3pk = f'ISSUE#CATEGORY#{category}'
    else:
        gsi3pk = 'ISSUE#CATEGORY#'
    
    response = table.query(
        IndexName='GSI3',
        KeyConditionExpression='begins_with(GSI3PK, :prefix)',
        ExpressionAttributeValues={
            ':prefix': gsi3pk
        }
    )
    
    # Group by issue hash
    issue_counts = {}
    for item in response['Items']:
        issue_hash = item.get('IssueHash')
        if issue_hash:
            if issue_hash not in issue_counts:
                issue_counts[issue_hash] = {
                    'count': 0,
                    'details': item
                }
            issue_counts[issue_hash]['count'] += 1
    
    # Filter by minimum occurrences
    return [
        info for hash, info in issue_counts.items()
        if info['count'] >= min_occurrences
    ]
```

### 8. Get Pending Reviews

```python
def get_pending_reviews(older_than_minutes=None):
    """Get all pending reviews, optionally filtered by age"""
    if older_than_minutes:
        cutoff = (datetime.utcnow() - timedelta(minutes=older_than_minutes)).isoformat()
        response = table.query(
            IndexName='GSI4',
            KeyConditionExpression='GSI4PK = :gsi4pk AND GSI4SK < :cutoff',
            ExpressionAttributeValues={
                ':gsi4pk': 'STATUS#pending',
                ':cutoff': f'CREATED#{cutoff}'
            }
        )
    else:
        response = table.query(
            IndexName='GSI4',
            KeyConditionExpression='GSI4PK = :gsi4pk',
            ExpressionAttributeValues={
                ':gsi4pk': 'STATUS#pending'
            }
        )
    
    return response['Items']
```

### 9. Get Failed Reviews

```python
def get_failed_reviews(limit=50):
    """Get all failed reviews for investigation"""
    response = table.query(
        IndexName='GSI4',
        KeyConditionExpression='GSI4PK = :gsi4pk',
        ExpressionAttributeValues={
            ':gsi4pk': 'STATUS#failed'
        },
        ScanIndexForward=False,  # Most recent first
        Limit=limit
    )
    return response['Items']
```

### 10. Get Reviews by Spacelift Run ID

```python
def get_review_by_run_id(spacelift_run_id):
    """Get review(s) for a specific Spacelift run"""
    # Option 1: If run_id is in GSI1PK
    response = table.query(
        IndexName='GSI1',
        KeyConditionExpression='GSI1PK = :gsi1pk',
        ExpressionAttributeValues={
            ':gsi1pk': f'RUN#{spacelift_run_id}'
        }
    )
    
    # Option 2: If using filter expression
    response = table.scan(
        FilterExpression='SpaceliftRunId = :run_id',
        ExpressionAttributeValues={
            ':run_id': spacelift_run_id
        }
    )
    
    return response['Items']
```

### 11. Get Stack Statistics

```python
def get_stack_statistics(stack_id):
    """Get aggregated statistics for a stack"""
    response = table.get_item(
        Key={
            'PK': f'STACK#{stack_id}',
            'SK': 'STATS'
        }
    )
    return response.get('Item')
```

### 12. Compare Review Versions

```python
def compare_versions(review_id, version1, version2):
    """Compare two versions of a review"""
    v1 = table.get_item(
        Key={
            'PK': f'REVIEW#{review_id}',
            'SK': f'VERSION#{version1}'
        }
    ).get('Item')
    
    v2 = table.get_item(
        Key={
            'PK': f'REVIEW#{review_id}',
            'SK': f'VERSION#{version2}'
        }
    ).get('Item')
    
    if not v1 or not v2:
        return None
    
    return {
        'risk_score_change': v2.get('OverallRiskScore', 0) - v1.get('OverallRiskScore', 0),
        'findings_change': {
            'security': v2.get('SecurityFindings', {}).get('total', 0) - v1.get('SecurityFindings', {}).get('total', 0),
            'cost': len(v2.get('CostAnalysis', {}).get('costOptimizations', [])) - len(v1.get('CostAnalysis', {}).get('costOptimizations', [])),
        },
        'fixes_applied': v2.get('FixApplied', False),
        'time_delta': (datetime.fromisoformat(v2['CreatedAt']) - datetime.fromisoformat(v1['CreatedAt'])).total_seconds()
    }
```

### 13. Get Reviews with Fixes Applied

```python
def get_reviews_with_fixes(stack_id=None):
    """Get all reviews where fixes were applied"""
    if stack_id:
        # Query by stack, filter by FixApplied
        response = table.query(
            IndexName='GSI1',
            KeyConditionExpression='GSI1PK = :gsi1pk',
            FilterExpression='FixApplied = :fix_applied',
            ExpressionAttributeValues={
                ':gsi1pk': f'STACK#{stack_id}',
                ':fix_applied': True
            }
        )
    else:
        # Scan with filter (less efficient)
        response = table.scan(
            FilterExpression='FixApplied = :fix_applied',
            ExpressionAttributeValues={
                ':fix_applied': True
            }
        )
    
    return response['Items']
```

### 14. Get Most Frequent Issues

```python
def get_most_frequent_issues(stack_id, limit=10):
    """Get the most frequently occurring issues for a stack"""
    response = table.query(
        IndexName='GSI3',
        KeyConditionExpression='GSI3PK = :gsi3pk',
        ExpressionAttributeValues={
            ':gsi3pk': f'ISSUE#STACK#{stack_id}'
        },
        ScanIndexForward=False,  # Highest frequency first
        Limit=limit
    )
    return response['Items']
```

### 15. Get Audit Trail

```python
def get_audit_trail(review_id):
    """Get complete audit trail for a review"""
    versions = get_all_versions(review_id)
    
    audit_trail = []
    for i, version in enumerate(versions):
        audit_entry = {
            'version': version['Version'],
            'timestamp': version['CreatedAt'],
            'created_by': version.get('CreatedBy'),
            'status': version.get('Status'),
            'risk_score': version.get('OverallRiskScore'),
            'changes': []
        }
        
        # Compare with previous version
        if i > 0:
            prev_version = versions[i-1]
            changes = detect_changes(prev_version, version)
            audit_entry['changes'] = changes
        
        audit_trail.append(audit_entry)
    
    return audit_trail

def detect_changes(old_version, new_version):
    """Detect what changed between versions"""
    changes = []
    
    # Status change
    if old_version.get('Status') != new_version.get('Status'):
        changes.append({
            'field': 'Status',
            'old': old_version.get('Status'),
            'new': new_version.get('Status')
        })
    
    # Risk score change
    if old_version.get('OverallRiskScore') != new_version.get('OverallRiskScore'):
        changes.append({
            'field': 'OverallRiskScore',
            'old': old_version.get('OverallRiskScore'),
            'new': new_version.get('OverallRiskScore'),
            'delta': new_version.get('OverallRiskScore') - old_version.get('OverallRiskScore', 0)
        })
    
    # Fix applied
    if new_version.get('FixApplied') and not old_version.get('FixApplied'):
        changes.append({
            'field': 'FixApplied',
            'old': False,
            'new': True,
            'fix_details': new_version.get('FixDetails')
        })
    
    return changes
```

## Batch Operations

### Batch Get Items

```python
def batch_get_reviews(review_ids):
    """Get multiple reviews in a single batch operation"""
    keys = [
        {
            'PK': f'REVIEW#{review_id}',
            'SK': 'VERSION#1'  # Or get latest version separately
        }
        for review_id in review_ids
    ]
    
    response = dynamodb.batch_get_item(
        RequestItems={
            table_name: {
                'Keys': keys
            }
        }
    )
    
    return response.get('Responses', {}).get(table_name, [])
```

### Batch Write Items

```python
def batch_create_findings(findings):
    """Batch create multiple finding records"""
    items = [
        {
            'PutRequest': {
                'Item': {
                    'PK': f'FINDING#{finding["finding_id"]}',
                    'SK': f'REVIEW#{finding["review_id"]}',
                    # ... other attributes
                }
            }
        }
        for finding in findings
    ]
    
    # DynamoDB batch_write_item supports up to 25 items
    for chunk in chunks(items, 25):
        dynamodb.batch_write_item(
            RequestItems={
                table_name: chunk
            }
        )
```

## Pagination

### Query Pagination

```python
def get_reviews_paginated(stack_id, page_size=25, last_evaluated_key=None):
    """Get reviews with pagination"""
    query_params = {
        'IndexName': 'GSI1',
        'KeyConditionExpression': 'GSI1PK = :gsi1pk',
        'ExpressionAttributeValues': {
            ':gsi1pk': f'STACK#{stack_id}'
        },
        'Limit': page_size,
        'ScanIndexForward': False
    }
    
    if last_evaluated_key:
        query_params['ExclusiveStartKey'] = last_evaluated_key
    
    response = table.query(**query_params)
    
    return {
        'items': response['Items'],
        'last_evaluated_key': response.get('LastEvaluatedKey'),
        'count': response.get('Count', 0)
    }
```

## Performance Optimization

### Projection Expressions

```python
def get_review_summary(review_id):
    """Get only essential fields for performance"""
    response = table.query(
        KeyConditionExpression='PK = :pk',
        ExpressionAttributeValues={
            ':pk': f'REVIEW#{review_id}'
        },
        ProjectionExpression='ReviewId, Version, Status, OverallRiskScore, CreatedAt',
        ScanIndexForward=False,
        Limit=1
    )
    return response['Items'][0] if response['Items'] else None
```

### Parallel Queries

```python
import concurrent.futures

def get_multiple_stacks_parallel(stack_ids):
    """Query multiple stacks in parallel"""
    def get_stack_reviews(stack_id):
        return get_stack_reviews(stack_id)
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {
            executor.submit(get_stack_reviews, stack_id): stack_id
            for stack_id in stack_ids
        }
        
        results = {}
        for future in concurrent.futures.as_completed(futures):
            stack_id = futures[future]
            try:
                results[stack_id] = future.result()
            except Exception as e:
                results[stack_id] = {'error': str(e)}
        
        return results
```

## Error Handling

### Retry Logic

```python
import time
from botocore.exceptions import ClientError

def query_with_retry(query_func, max_retries=3, backoff=1):
    """Execute query with exponential backoff retry"""
    for attempt in range(max_retries):
        try:
            return query_func()
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'ProvisionedThroughputExceededException':
                if attempt < max_retries - 1:
                    time.sleep(backoff * (2 ** attempt))
                    continue
            raise
    return None
```

## Monitoring Queries

### Query Metrics

```python
def log_query_metrics(query_name, start_time, item_count, capacity_consumed):
    """Log query performance metrics"""
    duration = time.time() - start_time
    metrics = {
        'query_name': query_name,
        'duration_ms': duration * 1000,
        'item_count': item_count,
        'capacity_consumed': capacity_consumed,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    # Send to CloudWatch
    cloudwatch.put_metric_data(
        Namespace='DynamoDB/Queries',
        MetricData=[
            {
                'MetricName': 'QueryDuration',
                'Value': duration * 1000,
                'Unit': 'Milliseconds',
                'Dimensions': [
                    {'Name': 'QueryName', 'Value': query_name}
                ]
            }
        ]
    )
```

