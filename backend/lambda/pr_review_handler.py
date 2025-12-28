"""
PR Review Handler Lambda

Handles GitHub PR review requests and triggers AI review.
"""

import json
import os
import boto3
from typing import Dict, Any
from datetime import datetime
import uuid

from dynamodb_client import DynamoDBClient
from models import Review
from logger import StructuredLogger

# Initialize services
dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('DYNAMODB_TABLE_NAME')
db_client = DynamoDBClient(table_name)
lambda_client = boto3.client('lambda')
logger = StructuredLogger('pr-review-handler', os.environ.get('ENVIRONMENT'))

# Get AI reviewer function name
ai_reviewer_function = os.environ.get('AI_REVIEWER_FUNCTION_NAME')


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle PR review request.
    
    Expected event structure:
    {
        "httpMethod": "POST",
        "path": "/api/reviews",
        "headers": {...},
        "body": {
            "terraform_code": "...",
            "pr_number": 123,
            "repository": "org/repo",
            "branch": "main",
            "commit_sha": "abc123"
        }
    }
    """
    start_time = datetime.utcnow()
    trace_id = event.get('requestContext', {}).get('requestId', str(uuid.uuid4()))
    logger.set_trace_id(trace_id)
    
    try:
        # Parse request
        body = json.loads(event.get('body', '{}'))
        headers = event.get('headers', {})
        
        # Log request
        logger.log_request(
            method=event.get('httpMethod', 'POST'),
            path=event.get('path', '/api/reviews'),
            user_id=headers.get('x-user-id'),
            ip_address=event.get('requestContext', {}).get('identity', {}).get('sourceIp')
        )
        
        # Validate request
        terraform_code = body.get('terraform_code', '')
        if not terraform_code:
            logger.warning('Missing terraform_code in request')
            return create_response(400, {'error': 'terraform_code is required'})
        
        # Extract PR context
        pr_context = {
            'pr_number': body.get('pr_number'),
            'repository': body.get('repository'),
            'branch': body.get('branch'),
            'commit_sha': body.get('commit_sha'),
            'author': body.get('author'),
            'title': body.get('title'),
            'changed_files': body.get('changed_files', [])
        }
        
        # Create review record
        review_id = str(uuid.uuid4())
        
        review = Review(
            review_id=review_id,
            terraform_code=terraform_code,
            spacelift_run_id=None,
            spacelift_context={
                'source': 'github_pr',
                **pr_context
            },
            status='pending',
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat()
        )
        
        # Audit log: Review creation
        logger.audit(
            event_type='review_created',
            user_id=pr_context.get('author', 'unknown'),
            resource=f'review/{review_id}',
            action='create',
            pr_number=pr_context.get('pr_number'),
            repository=pr_context.get('repository')
        )
        
        # Write to DynamoDB
        db_client.create_review(review)
        logger.info(f'Review created: {review_id}', review_id=review_id)
        
        # Invoke AI reviewer asynchronously
        invoke_payload = {
            'review_id': review_id,
            'terraform_code': terraform_code,
            'spacelift_context': review.spacelift_context,
            'source': 'github_pr'
        }
        
        try:
            lambda_client.invoke(
                FunctionName=ai_reviewer_function,
                InvocationType='Event',  # Async
                Payload=json.dumps(invoke_payload)
            )
            logger.info(f'AI reviewer invoked for review: {review_id}')
        except Exception as e:
            logger.error(f'Failed to invoke AI reviewer', error=e)
            # Continue - review is created, can be processed later
        
        # Calculate duration
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Log response
        logger.log_response(201, duration, review_id=review_id)
        
        return create_response(201, {
            'review_id': review_id,
            'status': 'pending',
            'message': 'Review created and queued for analysis'
        })
        
    except json.JSONDecodeError as e:
        logger.error('Invalid JSON in request body', error=e)
        return create_response(400, {'error': 'Invalid JSON in request body'})
    except Exception as e:
        logger.error('Error processing PR review request', error=e)
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000
        logger.log_response(500, duration)
        return create_response(500, {'error': 'Internal server error', 'message': str(e)})


def create_response(status_code: int, body: Dict[str, Any], headers: Dict[str, str] = None) -> Dict[str, Any]:
    """Create API Gateway response"""
    default_headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,Authorization',
        'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS'
    }
    if headers:
        default_headers.update(headers)
    
    return {
        'statusCode': status_code,
        'headers': default_headers,
        'body': json.dumps(body)
    }

