"""
GitHub Webhook Handler Lambda

Handles GitHub webhook events with signature verification.
"""

import json
import os
import boto3
import hmac
import hashlib
from typing import Dict, Any
from datetime import datetime
import uuid

from logger import StructuredLogger

# Initialize services
lambda_client = boto3.client('lambda')
secrets_manager = boto3.client('secretsmanager')
logger = StructuredLogger('github-webhook-handler', os.environ.get('ENVIRONMENT'))

# Get secrets
github_webhook_secret_name = os.environ.get('GITHUB_WEBHOOK_SECRET_NAME')
pr_review_function = os.environ.get('PR_REVIEW_FUNCTION_NAME')


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle GitHub webhook events.
    
    Supports:
    - pull_request (opened, synchronize, closed)
    - push (for branch updates)
    """
    start_time = datetime.utcnow()
    trace_id = event.get('requestContext', {}).get('requestId', str(uuid.uuid4()))
    logger.set_trace_id(trace_id)
    
    try:
        # Get headers and body
        headers = {k.lower(): v for k, v in event.get('headers', {}).items()}
        body = event.get('body', '')
        
        # Verify webhook signature
        signature = headers.get('x-hub-signature-256', '')
        if not verify_github_signature(body, signature):
            logger.security_event(
                event_type='webhook_signature_invalid',
                severity='high',
                source_ip=event.get('requestContext', {}).get('identity', {}).get('sourceIp')
            )
            return create_response(401, {'error': 'Invalid signature'})
        
        # Parse webhook payload
        if isinstance(body, str):
            payload = json.loads(body)
        else:
            payload = body
        
        event_type = headers.get('x-github-event', '')
        logger.info(f'GitHub webhook received', event_type=event_type, delivery_id=headers.get('x-github-delivery'))
        
        # Handle different event types
        if event_type == 'pull_request':
            return handle_pull_request_event(payload, trace_id)
        elif event_type == 'push':
            return handle_push_event(payload, trace_id)
        else:
            logger.info(f'Unhandled event type: {event_type}')
            return create_response(200, {'message': f'Event type {event_type} not handled'})
            
    except json.JSONDecodeError as e:
        logger.error('Invalid JSON in webhook payload', error=e)
        return create_response(400, {'error': 'Invalid JSON'})
    except Exception as e:
        logger.error('Error processing GitHub webhook', error=e)
        return create_response(500, {'error': 'Internal server error', 'message': str(e)})


def verify_github_signature(body: str, signature: str) -> bool:
    """
    Verify GitHub webhook signature.
    
    GitHub uses HMAC SHA256 with the webhook secret.
    """
    try:
        # Get webhook secret
        if not github_webhook_secret_name:
            logger.warning('GitHub webhook secret not configured')
            return False
        
        response = secrets_manager.get_secret_value(SecretId=github_webhook_secret_name)
        secret = response['SecretString']
        
        # Calculate expected signature
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            body.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # GitHub sends signature as "sha256=<hex>"
        if signature.startswith('sha256='):
            signature = signature[7:]
        
        # Compare signatures
        return hmac.compare_digest(signature, expected_signature)
    except Exception as e:
        logger.error('Error verifying GitHub signature', error=e)
        return False


def handle_pull_request_event(payload: Dict[str, Any], trace_id: str) -> Dict[str, Any]:
    """Handle pull request webhook event"""
    action = payload.get('action', '')
    pr = payload.get('pull_request', {})
    
    logger.info(
        f'Pull request event: {action}',
        pr_number=pr.get('number'),
        repository=payload.get('repository', {}).get('full_name'),
        branch=pr.get('head', {}).get('ref')
    )
    
    # Only process opened and synchronize events
    if action not in ['opened', 'synchronize']:
        return create_response(200, {'message': f'Action {action} not processed'})
    
    # Extract PR information
    pr_number = pr.get('number')
    repository = payload.get('repository', {}).get('full_name')
    branch = pr.get('head', {}).get('ref')
    commit_sha = pr.get('head', {}).get('sha')
    author = pr.get('user', {}).get('login')
    title = pr.get('title')
    
    # Get changed files
    changed_files = []
    files = payload.get('pull_request', {}).get('files', [])
    for file in files:
        if file.get('filename', '').endswith('.tf'):
            changed_files.append(file.get('filename'))
    
    # Get Terraform code from PR
    # Note: In production, you'd fetch the actual file contents from GitHub API
    terraform_code = payload.get('terraform_code', '')  # Would need to fetch from GitHub
    
    if not terraform_code:
        logger.warning('No Terraform code found in PR', pr_number=pr_number)
        return create_response(200, {'message': 'No Terraform files changed'})
    
    # Invoke PR review handler
    review_payload = {
        'terraform_code': terraform_code,
        'pr_number': pr_number,
        'repository': repository,
        'branch': branch,
        'commit_sha': commit_sha,
        'author': author,
        'title': title,
        'changed_files': changed_files
    }
    
    try:
        lambda_client.invoke(
            FunctionName=pr_review_function,
            InvocationType='Event',  # Async
            Payload=json.dumps(review_payload)
        )
        logger.info(f'PR review triggered for PR #{pr_number}')
    except Exception as e:
        logger.error(f'Failed to invoke PR review handler', error=e)
        return create_response(500, {'error': 'Failed to trigger review'})
    
    return create_response(200, {
        'message': 'PR review triggered',
        'pr_number': pr_number
    })


def handle_push_event(payload: Dict[str, Any], trace_id: str) -> Dict[str, Any]:
    """Handle push webhook event"""
    ref = payload.get('ref', '')
    repository = payload.get('repository', {}).get('full_name')
    
    logger.info(
        'Push event received',
        ref=ref,
        repository=repository,
        commits_count=len(payload.get('commits', []))
    )
    
    # Only process pushes to main/master branches
    if not ref.startswith('refs/heads/main') and not ref.startswith('refs/heads/master'):
        return create_response(200, {'message': 'Push to non-main branch, skipping'})
    
    # Process push event (could trigger review of changed Terraform files)
    # Implementation depends on requirements
    
    return create_response(200, {'message': 'Push event processed'})


def create_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Create API Gateway response"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(body)
    }

