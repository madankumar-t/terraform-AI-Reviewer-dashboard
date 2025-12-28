"""
Evidence Collector Lambda Function

Automated evidence collection for SOC2 and ISO 27001 compliance.
"""

import json
import os
import boto3
from datetime import datetime, timedelta
from typing import Dict, Any, List
import traceback

# AWS Clients
logs_client = boto3.client('logs')
dynamodb = boto3.client('dynamodb')
iam = boto3.client('iam')
cloudwatch = boto3.client('cloudwatch')
s3 = boto3.client('s3')

# Configuration
EVIDENCE_BUCKET = os.environ.get('EVIDENCE_BUCKET')
TABLE_NAME = os.environ.get('TABLE_NAME')
LOG_GROUP_PREFIX = os.environ.get('LOG_GROUP_PREFIX', '/aws/lambda/terraform-spacelift-ai-reviewer')


def collect_cloudwatch_logs(start_time: int, end_time: int, log_group: str, filter_pattern: str = None) -> List[Dict]:
    """Collect logs from CloudWatch"""
    try:
        kwargs = {
            'logGroupName': log_group,
            'startTime': start_time,
            'endTime': end_time,
            'limit': 10000
        }
        
        if filter_pattern:
            kwargs['filterPattern'] = filter_pattern
        
        response = logs_client.filter_log_events(**kwargs)
        return response.get('events', [])
    except Exception as e:
        print(f"Error collecting logs from {log_group}: {str(e)}")
        return []


def collect_dynamodb_evidence(start_date: str, end_date: str) -> Dict[str, Any]:
    """Collect evidence from DynamoDB"""
    evidence = {
        "total_reviews": 0,
        "reviews_by_status": {},
        "reviews_by_risk": {},
        "version_history": []
    }
    
    try:
        # Scan for reviews in date range
        response = dynamodb.scan(
            TableName=TABLE_NAME,
            FilterExpression='created_at BETWEEN :start AND :end',
            ExpressionAttributeValues={
                ':start': {'S': start_date},
                ':end': {'S': end_date}
            }
        )
        
        evidence["total_reviews"] = response.get('Count', 0)
        
        # Process items
        for item in response.get('Items', []):
            status = item.get('status', {}).get('S', 'unknown')
            evidence["reviews_by_status"][status] = evidence["reviews_by_status"].get(status, 0) + 1
            
            # Risk score if available
            if 'ai_review_result' in item:
                risk_score = item['ai_review_result'].get('M', {}).get('overall_risk_score', {}).get('N', '0')
                risk_level = 'high' if float(risk_score) > 0.67 else 'medium' if float(risk_score) > 0.33 else 'low'
                evidence["reviews_by_risk"][risk_level] = evidence["reviews_by_risk"].get(risk_level, 0) + 1
        
        return evidence
        
    except Exception as e:
        print(f"Error collecting DynamoDB evidence: {str(e)}")
        return evidence


def collect_iam_evidence() -> Dict[str, Any]:
    """Collect IAM evidence"""
    evidence = {
        "roles": [],
        "policies": [],
        "summary": {
            "total_roles": 0,
            "total_policies": 0
        }
    }
    
    try:
        # List roles
        response = iam.list_roles(PathPrefix='/terraform-spacelift-ai-reviewer/')
        
        for role in response.get('Roles', []):
            evidence["roles"].append({
                "role_name": role['RoleName'],
                "arn": role['Arn'],
                "created_date": role['CreateDate'].isoformat()
            })
            evidence["summary"]["total_roles"] += 1
        
        # List policies
        policy_response = iam.list_policies(Scope='Local', PathPrefix='/terraform-spacelift-ai-reviewer/')
        
        for policy in policy_response.get('Policies', []):
            evidence["policies"].append({
                "policy_name": policy['PolicyName'],
                "arn": policy['Arn'],
                "created_date": policy['CreateDate'].isoformat()
            })
            evidence["summary"]["total_policies"] += 1
        
        return evidence
        
    except Exception as e:
        print(f"Error collecting IAM evidence: {str(e)}")
        return evidence


def collect_cloudwatch_metrics(start_time: datetime, end_time: datetime) -> Dict[str, Any]:
    """Collect CloudWatch metrics"""
    evidence = {
        "lambda_metrics": {},
        "api_gateway_metrics": {},
        "dynamodb_metrics": {}
    }
    
    try:
        # Lambda metrics
        functions = ['api-handler', 'ai-reviewer', 'jwt-authorizer']
        
        for func in functions:
            response = cloudwatch.get_metric_statistics(
                Namespace='AWS/Lambda',
                MetricName='Invocations',
                Dimensions=[{'Name': 'FunctionName', 'Value': f'terraform-spacelift-ai-reviewer-{func}-prod'}],
                StartTime=start_time,
                EndTime=end_time,
                Period=3600,
                Statistics=['Sum']
            )
            
            evidence["lambda_metrics"][func] = {
                "invocations": sum([d['Sum'] for d in response.get('Datapoints', [])])
            }
        
        # API Gateway metrics
        response = cloudwatch.get_metric_statistics(
            Namespace='AWS/ApiGateway',
            MetricName='Count',
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,
            Statistics=['Sum']
        )
        
        evidence["api_gateway_metrics"]["total_requests"] = sum([d['Sum'] for d in response.get('Datapoints', [])])
        
        return evidence
        
    except Exception as e:
        print(f"Error collecting CloudWatch metrics: {str(e)}")
        return evidence


def save_evidence_to_s3(evidence_type: str, evidence_data: Dict[str, Any], date: datetime):
    """Save evidence to S3"""
    try:
        # Organize by framework and control
        if evidence_type == "daily":
            key = f"soc2/cc2-communication/daily-logs-{date.strftime('%Y-%m-%d')}.json"
        elif evidence_type == "weekly":
            week = date.isocalendar()[1]
            key = f"soc2/cc4-monitoring/weekly-report-{date.strftime('%Y')}-W{week:02d}.json"
        elif evidence_type == "monthly":
            key = f"access-reviews/{date.strftime('%Y')}/access-review-{date.strftime('%Y-%m')}.json"
        else:
            key = f"evidence/{evidence_type}-{date.strftime('%Y-%m-%d')}.json"
        
        # Add metadata
        evidence_data["metadata"] = {
            "collection_date": datetime.utcnow().isoformat(),
            "collection_type": evidence_type,
            "evidence_period": {
                "start": date.isoformat(),
                "end": datetime.utcnow().isoformat()
            }
        }
        
        # Upload to S3
        s3.put_object(
            Bucket=EVIDENCE_BUCKET,
            Key=key,
            Body=json.dumps(evidence_data, indent=2, default=str),
            ContentType='application/json',
            ServerSideEncryption='AES256'
        )
        
        print(f"Evidence saved to s3://{EVIDENCE_BUCKET}/{key}")
        return key
        
    except Exception as e:
        print(f"Error saving evidence to S3: {str(e)}")
        raise


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for evidence collection.
    
    Event structure:
    {
        "collection_type": "daily" | "weekly" | "monthly"
    }
    """
    try:
        collection_type = event.get('collection_type', 'daily')
        now = datetime.utcnow()
        
        # Determine date range
        if collection_type == "daily":
            start_date = now - timedelta(days=1)
            end_date = now
        elif collection_type == "weekly":
            start_date = now - timedelta(days=7)
            end_date = now
        elif collection_type == "monthly":
            start_date = now - timedelta(days=30)
            end_date = now
        else:
            start_date = now - timedelta(days=1)
            end_date = now
        
        start_timestamp = int(start_date.timestamp() * 1000)
        end_timestamp = int(end_date.timestamp() * 1000)
        
        # Collect evidence
        evidence = {
            "collection_type": collection_type,
            "collection_date": now.isoformat(),
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "evidence": {}
        }
        
        # CloudWatch Logs
        print("Collecting CloudWatch logs...")
        log_groups = [
            f"{LOG_GROUP_PREFIX}-api-handler-prod",
            f"{LOG_GROUP_PREFIX}-jwt-authorizer-prod"
        ]
        
        evidence["evidence"]["cloudwatch_logs"] = {}
        for log_group in log_groups:
            events = collect_cloudwatch_logs(start_timestamp, end_timestamp, log_group)
            evidence["evidence"]["cloudwatch_logs"][log_group] = {
                "event_count": len(events),
                "sample_events": events[:10]  # Sample for size
            }
        
        # DynamoDB Evidence
        print("Collecting DynamoDB evidence...")
        evidence["evidence"]["dynamodb"] = collect_dynamodb_evidence(
            start_date.isoformat(),
            end_date.isoformat()
        )
        
        # IAM Evidence (monthly only)
        if collection_type == "monthly":
            print("Collecting IAM evidence...")
            evidence["evidence"]["iam"] = collect_iam_evidence()
        
        # CloudWatch Metrics
        print("Collecting CloudWatch metrics...")
        evidence["evidence"]["cloudwatch_metrics"] = collect_cloudwatch_metrics(start_date, end_date)
        
        # Save to S3
        print("Saving evidence to S3...")
        s3_key = save_evidence_to_s3(collection_type, evidence, start_date)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'status': 'success',
                'collection_type': collection_type,
                'evidence_saved': s3_key,
                'evidence_summary': {
                    'log_events': sum([len(v.get('event_count', 0)) for v in evidence["evidence"]["cloudwatch_logs"].values()]),
                    'dynamodb_reviews': evidence["evidence"]["dynamodb"].get('total_reviews', 0)
                }
            })
        }
        
    except Exception as e:
        error_msg = {
            'status': 'error',
            'error': str(e),
            'traceback': traceback.format_exc()
        }
        
        print(f"Error in evidence collection: {json.dumps(error_msg)}")
        
        return {
            'statusCode': 500,
            'body': json.dumps(error_msg)
        }

