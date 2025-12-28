"""
Trend Aggregation Handler Lambda

Aggregates and calculates trends from review data.
Runs on schedule to pre-compute trend data.
"""

import json
import os
import boto3
import uuid
from typing import Dict, Any, List
from datetime import datetime, timedelta
from decimal import Decimal

from dynamodb_client import DynamoDBClient
from logger import StructuredLogger

# Initialize services
dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('DYNAMODB_TABLE_NAME')
db_client = DynamoDBClient(table_name)
logger = StructuredLogger('trend-aggregation-handler', os.environ.get('ENVIRONMENT'))


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Aggregate trend data for all stacks.
    
    Can be triggered by:
    - EventBridge schedule (daily)
    - Manual invocation
    - API request
    """
    start_time = datetime.utcnow()
    trace_id = context.aws_request_id if context else str(uuid.uuid4())
    logger.set_trace_id(trace_id)
    
    try:
        logger.info('Starting trend aggregation')
        
        # Get aggregation period (default: last 30 days)
        days = int(event.get('days', 30))
        
        # Aggregate trends for all stacks
        stacks = get_all_stacks()
        logger.info(f'Aggregating trends for {len(stacks)} stacks', stack_count=len(stacks))
        
        aggregated_data = {}
        for stack_id in stacks:
            try:
                stack_trends = aggregate_stack_trends(stack_id, days)
                aggregated_data[stack_id] = stack_trends
            except Exception as e:
                logger.error(f'Error aggregating trends for stack {stack_id}', error=e)
                continue
        
        # Store aggregated data in DynamoDB
        store_aggregated_trends(aggregated_data)
        
        # Calculate global trends
        global_trends = calculate_global_trends(aggregated_data)
        
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000
        logger.performance('trend_aggregation', duration, stacks_processed=len(stacks))
        logger.info('Trend aggregation completed', stacks_processed=len(stacks))
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Trend aggregation completed',
                'stacks_processed': len(stacks),
                'global_trends': global_trends,
                'duration_ms': duration
            }, default=str)
        }
        
    except Exception as e:
        logger.error('Error in trend aggregation', error=e)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error', 'message': str(e)})
        }


def get_all_stacks() -> List[str]:
    """Get list of all unique stack IDs from reviews"""
    # Query DynamoDB to get distinct stack IDs
    # This is a simplified version - in production, you might maintain a separate index
    reviews = db_client.query_reviews(limit=1000)  # Get recent reviews
    
    stacks = set()
    for review in reviews:
        stack_id = review.get('spacelift_context', {}).get('stack_id')
        if stack_id:
            stacks.add(stack_id)
    
    return list(stacks)


def aggregate_stack_trends(stack_id: str, days: int) -> Dict[str, Any]:
    """Aggregate trend data for a specific stack"""
    reviews = db_client.query_reviews_by_stack(stack_id, days=days)
    
    if not reviews:
        return {
            'stack_id': stack_id,
            'period_days': days,
            'review_count': 0,
            'trends': {}
        }
    
    # Calculate metrics
    risk_scores = []
    security_findings = []
    cost_findings = []
    reliability_findings = []
    
    for review in reviews:
        ai_result = review.get('ai_review_result', {})
        if ai_result:
            risk_score = ai_result.get('overall_risk_score')
            if risk_score is not None:
                risk_scores.append(float(risk_score))
            
            security = ai_result.get('security_analysis', {})
            security_findings.append(security.get('total_findings', 0))
            
            cost = ai_result.get('cost_analysis', {})
            cost_findings.append(len(cost.get('cost_optimizations', [])))
            
            reliability = ai_result.get('reliability_analysis', {})
            reliability_findings.append(len(reliability.get('single_points_of_failure', [])))
    
    # Calculate trends
    avg_risk = sum(risk_scores) / len(risk_scores) if risk_scores else 0.0
    avg_security = sum(security_findings) / len(security_findings) if security_findings else 0.0
    avg_cost = sum(cost_findings) / len(cost_findings) if cost_findings else 0.0
    avg_reliability = sum(reliability_findings) / len(reliability_findings) if reliability_findings else 0.0
    
    # Calculate trend direction (comparing first half vs second half)
    if len(reviews) >= 4:
        first_half = reviews[:len(reviews)//2]
        second_half = reviews[len(reviews)//2:]
        
        first_avg_risk = calculate_average_risk(first_half)
        second_avg_risk = calculate_average_risk(second_half)
        
        risk_trend = 'improving' if second_avg_risk < first_avg_risk else 'degrading' if second_avg_risk > first_avg_risk else 'stable'
    else:
        risk_trend = 'insufficient_data'
    
    return {
        'stack_id': stack_id,
        'period_days': days,
        'review_count': len(reviews),
        'trends': {
            'average_risk_score': avg_risk,
            'average_security_findings': avg_security,
            'average_cost_findings': avg_cost,
            'average_reliability_findings': avg_reliability,
            'risk_trend': risk_trend,
            'last_updated': datetime.utcnow().isoformat()
        }
    }


def calculate_average_risk(reviews: List[Dict[str, Any]]) -> float:
    """Calculate average risk score from reviews"""
    risk_scores = []
    for review in reviews:
        ai_result = review.get('ai_review_result', {})
        if ai_result:
            risk_score = ai_result.get('overall_risk_score')
            if risk_score is not None:
                risk_scores.append(float(risk_score))
    
    return sum(risk_scores) / len(risk_scores) if risk_scores else 0.0


def calculate_global_trends(aggregated_data: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate global trends across all stacks"""
    if not aggregated_data:
        return {}
    
    all_risk_scores = []
    improving_stacks = 0
    degrading_stacks = 0
    stable_stacks = 0
    
    for stack_id, data in aggregated_data.items():
        trends = data.get('trends', {})
        risk_score = trends.get('average_risk_score', 0.0)
        if risk_score > 0:
            all_risk_scores.append(risk_score)
        
        risk_trend = trends.get('risk_trend', 'unknown')
        if risk_trend == 'improving':
            improving_stacks += 1
        elif risk_trend == 'degrading':
            degrading_stacks += 1
        elif risk_trend == 'stable':
            stable_stacks += 1
    
    return {
        'total_stacks': len(aggregated_data),
        'global_average_risk': sum(all_risk_scores) / len(all_risk_scores) if all_risk_scores else 0.0,
        'improving_stacks': improving_stacks,
        'degrading_stacks': degrading_stacks,
        'stable_stacks': stable_stacks,
        'last_updated': datetime.utcnow().isoformat()
    }


def store_aggregated_trends(aggregated_data: Dict[str, Dict[str, Any]]):
    """Store aggregated trends in DynamoDB"""
    table = dynamodb.Table(table_name)
    
    for stack_id, data in aggregated_data.items():
        # Store as STACK_STATS entity
        item = {
            'PK': f'STACK#{stack_id}',
            'SK': 'TRENDS',
            'GSI1PK': f'STACK#{stack_id}',
            'GSI1SK': 'TRENDS',
            'EntityType': 'STACK_TRENDS',
            'StackId': stack_id,
            'TrendData': data,
            'UpdatedAt': datetime.utcnow().isoformat()
        }
        
        try:
            table.put_item(Item=item)
            logger.debug(f'Stored trends for stack: {stack_id}')
        except Exception as e:
            logger.error(f'Error storing trends for stack {stack_id}', error=e)

