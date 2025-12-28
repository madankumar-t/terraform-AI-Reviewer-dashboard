import json
import os
import boto3
from typing import Dict, Any, Optional
from datetime import datetime
import uuid
import traceback

from models import (
    Review, AIReviewResult, SecurityAnalysis, CostAnalysis, 
    ReliabilityAnalysis, Finding, FixSuggestion, RiskLevel
)
from dynamodb_client import DynamoDBClient
from bedrock_service import BedrockService
from logger import StructuredLogger

dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('DYNAMODB_TABLE_NAME')
db_client = DynamoDBClient(table_name)
bedrock_region = os.environ.get('BEDROCK_REGION', 'us-east-1')
bedrock_service = BedrockService(region=bedrock_region)
logger = StructuredLogger('ai-reviewer', os.environ.get('ENVIRONMENT'))

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """AI Reviewer Lambda handler"""
    start_time = datetime.utcnow()
    trace_id = context.aws_request_id if context else str(uuid.uuid4())
    logger.set_trace_id(trace_id)
    
    try:
        # Extract review data from event
        review_id = event.get('review_id')
        terraform_code = event.get('terraform_code', '')
        spacelift_context = event.get('spacelift_context', {})
        spacelift_run_id = event.get('spacelift_run_id')
        
        # If no review_id, create a new review first
        if not review_id:
            if not terraform_code:
                return {
                    'statusCode': 400,
                    'body': json.dumps({'error': 'terraform_code is required'})
                }
            
            # Create review
            from models import Review
            import uuid
            from datetime import datetime
            
            review = Review(
                review_id=str(uuid.uuid4()),
                terraform_code=terraform_code,
                spacelift_run_id=spacelift_run_id,
                spacelift_context=spacelift_context,
                status='pending',
                created_at=datetime.utcnow().isoformat(),
                updated_at=datetime.utcnow().isoformat()
            )
            
            db_client.create_review(review)
            review_id = review.review_id
        else:
            # Get existing review to verify it exists
            existing = db_client.get_review(review_id)
            if not existing:
                return {
                    'statusCode': 404,
                    'body': json.dumps({'error': 'Review not found'})
                }
            terraform_code = existing.get('terraform_code', terraform_code)
            spacelift_context = existing.get('spacelift_context', spacelift_context)
        
        logger.info(f'Starting AI review', review_id=review_id)
        
        # Update review status to in_progress
        db_client.update_review(review_id, {'status': 'in_progress'})
        
        # Perform AI review using Bedrock
        review_start = datetime.utcnow()
        ai_result = bedrock_service.review_terraform(
            terraform_code=terraform_code,
            spacelift_context=spacelift_context,
            prompt_type='pr_review'
        )
        review_duration = (datetime.utcnow() - review_start).total_seconds() * 1000
        logger.performance('ai_review', review_duration, review_id=review_id)
        
        # Set review_id in result
        ai_result.review_id = review_id
        
        # Audit log
        logger.audit(
            event_type='review_completed',
            user_id='ai_reviewer',
            resource=f'review/{review_id}',
            action='complete',
            risk_score=ai_result.overall_risk_score
        )
        
        # Update review with results
        updated_review = db_client.update_review(review_id, {
            'status': 'completed',
            'ai_review_result': ai_result.dict()
        })
        
        logger.info(f'AI review completed', review_id=review_id, risk_score=ai_result.overall_risk_score)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'review_id': review_id,
                'status': 'completed',
                'ai_review_result': ai_result.dict()
            })
        }
        
    except Exception as e:
        logger.error('Error in AI reviewer', error=e, review_id=event.get('review_id'))
        
        # Update review status to failed
        review_id = event.get('review_id')
        if review_id:
            try:
                db_client.update_review(review_id, {
                    'status': 'failed'
                })
                logger.audit(
                    event_type='review_failed',
                    user_id='ai_reviewer',
                    resource=f'review/{review_id}',
                    action='fail',
                    error=str(e)
                )
            except Exception as update_error:
                logger.error('Error updating review status to failed', error=update_error)
        
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000
        logger.performance('ai_review', duration, status='failed')
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'AI review failed',
                'message': str(e)
            })
        }

