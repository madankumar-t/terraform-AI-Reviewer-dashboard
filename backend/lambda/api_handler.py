import json
import os
import boto3
from typing import Dict, Any, Optional
from datetime import datetime
from decimal import Decimal
import uuid

from dynamodb_client import DynamoDBClient
from models import Review, ReviewCreateRequest, ReviewUpdateRequest, AnalyticsResponse
from logger import StructuredLogger

dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('DYNAMODB_TABLE_NAME')
db_client = DynamoDBClient(table_name)
logger = StructuredLogger('api-handler', os.environ.get('ENVIRONMENT'))

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)

def create_response(status_code: int, body: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
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
        'body': json.dumps(body, cls=DecimalEncoder)
    }

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Main API handler for review endpoints"""
    start_time = datetime.utcnow()
    trace_id = event.get('requestContext', {}).get('requestId', str(uuid.uuid4()))
    logger.set_trace_id(trace_id)
    
    try:
        route_key = event.get('routeKey', '')
        path_parameters = event.get('pathParameters') or {}
        query_parameters = event.get('queryStringParameters') or {}
        body = event.get('body', '{}')
        headers = event.get('headers', {})
        
        # Log request
        logger.log_request(
            method=event.get('requestContext', {}).get('http', {}).get('method', 'GET'),
            path=event.get('path', ''),
            user_id=headers.get('x-user-id'),
            route_key=route_key
        )
        
        # Handle OPTIONS for CORS
        if event.get('requestContext', {}).get('http', {}).get('method') == 'OPTIONS':
            return create_response(200, {'message': 'OK'})
        
        # Route handling
        if route_key == 'GET /api/reviews':
            return get_reviews(query_parameters)
        elif route_key == 'GET /api/reviews/{reviewId}':
            review_id = path_parameters.get('reviewId')
            return get_review(review_id)
        elif route_key == 'POST /api/reviews':
            return create_review(json.loads(body))
        elif route_key == 'PUT /api/reviews/{reviewId}':
            review_id = path_parameters.get('reviewId')
            return update_review(review_id, json.loads(body))
        elif route_key == 'GET /api/analytics':
            return get_analytics(query_parameters)
        else:
            logger.warning('Route not found', route_key=route_key)
            return create_response(404, {'error': 'Route not found'})
        
        # Log response
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000
        logger.log_response(200, duration)
            
    except json.JSONDecodeError as e:
        logger.error('Invalid JSON in request', error=e)
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000
        logger.log_response(400, duration)
        return create_response(400, {'error': f'Invalid JSON: {str(e)}'})
    except Exception as e:
        logger.error('Error in API handler', error=e)
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000
        logger.log_response(500, duration)
        return create_response(500, {'error': 'Internal server error', 'message': str(e)})

def get_reviews(query_params: Dict[str, Any]) -> Dict[str, Any]:
    """Get list of reviews with optional filtering"""
    try:
        spacelift_run_id = query_params.get('spaceliftRunId')
        status = query_params.get('status')
        limit = int(query_params.get('limit', 50))
        
        reviews = db_client.query_reviews(
            spacelift_run_id=spacelift_run_id,
            status=status,
            limit=limit
        )
        
        return create_response(200, {
            'reviews': reviews,
            'count': len(reviews)
        })
    except Exception as e:
        return create_response(500, {'error': str(e)})

def get_review(review_id: str) -> Dict[str, Any]:
    """Get a specific review by ID"""
    try:
        if not review_id:
            return create_response(400, {'error': 'reviewId is required'})
        
        review = db_client.get_review(review_id)
        
        if not review:
            return create_response(404, {'error': 'Review not found'})
        
        return create_response(200, review)
    except Exception as e:
        return create_response(500, {'error': str(e)})

def create_review(data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new review"""
    try:
        # Validate request
        request = ReviewCreateRequest(**data)
        
        review = Review(
            review_id=str(uuid.uuid4()),
            terraform_code=data.get('terraform_code', ''),
            spacelift_run_id=data.get('spacelift_run_id'),
            spacelift_context=data.get('spacelift_context', {}),
            status='pending',
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat()
        )
        
        # Audit log
        logger.audit(
            event_type='review_created',
            user_id=data.get('user_id', 'api'),
            resource=f'review/{review.review_id}',
            action='create'
        )
        
        db_client.create_review(review)
        logger.info(f'Review created: {review.review_id}', review_id=review.review_id)
        
        return create_response(201, review.dict())
    except Exception as e:
        logger.error('Error creating review', error=e)
        return create_response(400, {'error': str(e)})

def update_review(review_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Update an existing review"""
    try:
        if not review_id:
            return create_response(400, {'error': 'reviewId is required'})
        
        request = ReviewUpdateRequest(**data)
        
        review = db_client.get_review(review_id)
        if not review:
            return create_response(404, {'error': 'Review not found'})
        
        # Audit log
        logger.audit(
            event_type='review_updated',
            user_id=data.get('user_id', 'api'),
            resource=f'review/{review_id}',
            action='update',
            changes=list(request.dict(exclude_unset=True).keys())
        )
        
        # Update fields
        update_data = request.dict(exclude_unset=True)
        update_data['updated_at'] = datetime.utcnow().isoformat()
        
        updated_review = db_client.update_review(review_id, update_data)
        logger.info(f'Review updated: {review_id}', review_id=review_id, version=updated_review.get('version'))
        
        return create_response(200, updated_review)
    except Exception as e:
        logger.error('Error updating review', error=e, review_id=review_id)
        return create_response(400, {'error': str(e)})

def get_analytics(query_params: Dict[str, Any]) -> Dict[str, Any]:
    """Get analytics data"""
    try:
        days = int(query_params.get('days', 30))
        
        analytics = db_client.get_analytics(days=days)
        
        return create_response(200, analytics)
    except Exception as e:
        return create_response(500, {'error': str(e)})

