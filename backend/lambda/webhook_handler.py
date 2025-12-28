import json
import os
import boto3
import hmac
import hashlib
from typing import Dict, Any
from datetime import datetime
import uuid

from secrets_manager import SecretsManager
from dynamodb_client import DynamoDBClient
from models import Review
from logger import StructuredLogger

dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('DYNAMODB_TABLE_NAME')
db_client = DynamoDBClient(table_name)

lambda_client = boto3.client('lambda')
secrets_manager = SecretsManager()
logger = StructuredLogger('spacelift-webhook-handler', os.environ.get('ENVIRONMENT'))

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Spacelift webhook handler"""
    start_time = datetime.utcnow()
    trace_id = event.get('requestContext', {}).get('requestId', str(uuid.uuid4()))
    logger.set_trace_id(trace_id)
    
    try:
        # Verify webhook signature
        headers = {k.lower(): v for k, v in event.get('headers', {}).items()}
        body = event.get('body', '{}')
        
        # Log request
        logger.log_request(
            method=event.get('httpMethod', 'POST'),
            path=event.get('path', '/webhook/spacelift'),
            ip_address=event.get('requestContext', {}).get('identity', {}).get('sourceIp')
        )
        
        # Get webhook secret
        webhook_secret = secrets_manager.get_spacelift_secret()
        
        if webhook_secret:
            signature = headers.get('x-spacelift-signature', '')
            if not verify_signature(body, signature, webhook_secret):
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
        
        event_type = payload.get('event', {}).get('type', '')
        logger.info(f'Spacelift webhook received', event_type=event_type)
        
        # Handle different Spacelift events
        if event_type == 'run:finished' or event_type == 'run:tracked':
            result = handle_run_event(payload, trace_id)
        elif event_type == 'run:plan_finished':
            result = handle_plan_event(payload, trace_id)
        else:
            logger.info(f'Unhandled event type: {event_type}')
            result = create_response(200, {'message': f'Event type {event_type} not handled'})
        
        # Log response
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000
        logger.log_response(result['statusCode'], duration)
        
        return result
            
    except json.JSONDecodeError as e:
        logger.error('Invalid JSON in webhook payload', error=e)
        return create_response(400, {'error': f'Invalid JSON: {str(e)}'})
    except Exception as e:
        logger.error('Error processing Spacelift webhook', error=e)
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000
        logger.log_response(500, duration)
        return create_response(500, {'error': 'Internal server error', 'message': str(e)})


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

def verify_signature(body: str, signature: str, secret: str) -> bool:
    """Verify Spacelift webhook signature"""
    try:
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            body.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    except Exception:
        return False

def handle_run_event(payload: Dict[str, Any], trace_id: str) -> Dict[str, Any]:
    """Handle Spacelift run events"""
    try:
        run_data = payload.get('run', {})
        spacelift_run_id = run_data.get('id')
        stack_id = run_data.get('stack', {}).get('id')
        status = run_data.get('state', '')
        
        logger.info(
            f'Processing Spacelift run event',
            spacelift_run_id=spacelift_run_id,
            stack_id=stack_id,
            status=status
        )
        
        # Extract Terraform code if available
        terraform_code = ""
        if 'terraform' in run_data:
            terraform_code = run_data.get('terraform', {}).get('code', '')
        
        # Build Spacelift context
        spacelift_context = {
            'run_id': spacelift_run_id,
            'stack_id': stack_id,
            'status': status,
            'previous_status': run_data.get('previous_state', ''),
            'changed_files': run_data.get('changed_files', []),
            'commit_sha': run_data.get('commit', {}).get('sha', ''),
            'branch': run_data.get('branch', ''),
            'event_type': payload.get('event', {}).get('type', '')
        }
        
        # Create review record first
        review = Review(
            review_id=str(uuid.uuid4()),
            terraform_code=terraform_code,
            spacelift_run_id=spacelift_run_id,
            spacelift_context=spacelift_context,
            status='pending',
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat()
        )
        
        # Audit log: Review creation
        logger.audit(
            event_type='review_created',
            user_id='spacelift',
            resource=f'review/{review.review_id}',
            action='create',
            spacelift_run_id=spacelift_run_id,
            stack_id=stack_id
        )
        
        db_client.create_review(review)
        logger.info(f'Review created: {review.review_id}', review_id=review.review_id)
        
        # Invoke AI reviewer Lambda
        ai_reviewer_function = os.environ.get('AI_REVIEWER_FUNCTION_NAME')
        if not ai_reviewer_function:
            logger.error('AI reviewer function not configured')
            return create_response(500, {'error': 'AI reviewer function not configured'})
        
        invoke_payload = {
            'review_id': review.review_id,
            'terraform_code': terraform_code,
            'spacelift_context': spacelift_context,
            'spacelift_run_id': spacelift_run_id
        }
        
        try:
            lambda_client.invoke(
                FunctionName=ai_reviewer_function,
                InvocationType='Event',  # Async
                Payload=json.dumps(invoke_payload)
            )
            logger.info(f'AI reviewer invoked for review: {review.review_id}')
        except Exception as e:
            logger.error(f'Failed to invoke AI reviewer', error=e)
            # Continue - review is created
        
        return create_response(200, {
            'message': 'Review initiated',
            'review_id': review.review_id,
            'spacelift_run_id': spacelift_run_id,
            'review_status': 'pending'
        })
        
    except Exception as e:
        logger.error('Error handling run event', error=e)
        return create_response(500, {'error': str(e)})

def handle_plan_event(payload: Dict[str, Any], trace_id: str) -> Dict[str, Any]:
    """Handle Spacelift plan events"""
    logger.info('Processing Spacelift plan event')
    # Similar to run event but for plan-specific data
    return handle_run_event(payload, trace_id)

