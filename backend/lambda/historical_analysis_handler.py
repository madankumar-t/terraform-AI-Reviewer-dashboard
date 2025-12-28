"""
Historical Analysis Handler Lambda

Analyzes historical review data for trends, patterns, and insights.
"""

import json
import os
import boto3
from typing import Dict, Any, List
from datetime import datetime, timedelta
from decimal import Decimal

from dynamodb_client import DynamoDBClient
from logger import StructuredLogger

# Initialize services
dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('DYNAMODB_TABLE_NAME')
db_client = DynamoDBClient(table_name)
logger = StructuredLogger('historical-analysis-handler', os.environ.get('ENVIRONMENT'))


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handle historical analysis requests.
    
    Query parameters:
    - stack_id: Filter by stack
    - days: Number of days to analyze (default: 30)
    - analysis_type: Type of analysis (trends, patterns, correlations)
    """
    start_time = datetime.utcnow()
    trace_id = event.get('requestContext', {}).get('requestId', '')
    logger.set_trace_id(trace_id)
    
    try:
        # Parse query parameters
        query_params = event.get('queryStringParameters') or {}
        stack_id = query_params.get('stack_id')
        days = int(query_params.get('days', 30))
        analysis_type = query_params.get('analysis_type', 'trends')
        
        logger.log_request(
            method=event.get('httpMethod', 'GET'),
            path=event.get('path', '/api/analytics/historical'),
            stack_id=stack_id,
            days=days,
            analysis_type=analysis_type
        )
        
        # Perform analysis based on type
        if analysis_type == 'trends':
            result = analyze_trends(stack_id, days)
        elif analysis_type == 'patterns':
            result = analyze_patterns(stack_id, days)
        elif analysis_type == 'correlations':
            result = analyze_correlations(stack_id, days)
        else:
            return create_response(400, {'error': f'Unknown analysis type: {analysis_type}'})
        
        # Log response
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000
        logger.log_response(200, duration)
        logger.performance('historical_analysis', duration, analysis_type=analysis_type)
        
        return create_response(200, result)
        
    except Exception as e:
        logger.error('Error in historical analysis', error=e)
        duration = (datetime.utcnow() - start_time).total_seconds() * 1000
        logger.log_response(500, duration)
        return create_response(500, {'error': 'Internal server error', 'message': str(e)})


def analyze_trends(stack_id: str = None, days: int = 30) -> Dict[str, Any]:
    """Analyze risk and finding trends over time"""
    cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
    
    # Get reviews for the period
    if stack_id:
        reviews = db_client.query_reviews_by_stack(stack_id, days=days)
    else:
        reviews = db_client.query_reviews(days=days)
    
    # Group by date
    daily_data = {}
    for review in reviews:
        created_at = review.get('created_at', '')
        if created_at:
            date = created_at.split('T')[0]
            if date not in daily_data:
                daily_data[date] = {
                    'date': date,
                    'count': 0,
                    'risk_scores': [],
                    'security_findings': 0,
                    'cost_findings': 0,
                    'reliability_findings': 0
                }
            
            daily_data[date]['count'] += 1
            
            ai_result = review.get('ai_review_result', {})
            if ai_result:
                risk_score = ai_result.get('overall_risk_score')
                if risk_score is not None:
                    daily_data[date]['risk_scores'].append(float(risk_score))
                
                security = ai_result.get('security_analysis', {})
                daily_data[date]['security_findings'] += security.get('total_findings', 0)
                
                cost = ai_result.get('cost_analysis', {})
                daily_data[date]['cost_findings'] += len(cost.get('cost_optimizations', []))
                
                reliability = ai_result.get('reliability_analysis', {})
                daily_data[date]['reliability_findings'] += len(reliability.get('single_points_of_failure', []))
    
    # Calculate averages
    trend_data = []
    for date, data in sorted(daily_data.items()):
        avg_risk = sum(data['risk_scores']) / len(data['risk_scores']) if data['risk_scores'] else 0.0
        trend_data.append({
            'date': date,
            'review_count': data['count'],
            'average_risk_score': avg_risk,
            'total_security_findings': data['security_findings'],
            'total_cost_findings': data['cost_findings'],
            'total_reliability_findings': data['reliability_findings']
        })
    
    # Calculate overall trends
    if len(trend_data) >= 2:
        first_half = trend_data[:len(trend_data)//2]
        second_half = trend_data[len(trend_data)//2:]
        
        first_avg_risk = sum(d['average_risk_score'] for d in first_half) / len(first_half) if first_half else 0
        second_avg_risk = sum(d['average_risk_score'] for d in second_half) / len(second_half) if second_half else 0
        
        risk_trend = 'improving' if second_avg_risk < first_avg_risk else 'degrading' if second_avg_risk > first_avg_risk else 'stable'
    else:
        risk_trend = 'insufficient_data'
    
    return {
        'analysis_type': 'trends',
        'period_days': days,
        'stack_id': stack_id,
        'trend_data': trend_data,
        'summary': {
            'total_reviews': len(reviews),
            'risk_trend': risk_trend,
            'average_risk_score': sum(d['average_risk_score'] for d in trend_data) / len(trend_data) if trend_data else 0.0
        }
    }


def analyze_patterns(stack_id: str = None, days: int = 30) -> Dict[str, Any]:
    """Analyze patterns in findings and issues"""
    reviews = db_client.query_reviews(days=days) if not stack_id else db_client.query_reviews_by_stack(stack_id, days=days)
    
    # Collect all findings
    finding_patterns = {}
    issue_frequency = {}
    
    for review in reviews:
        ai_result = review.get('ai_review_result', {})
        if not ai_result:
            continue
        
        # Security findings
        for finding in ai_result.get('security_analysis', {}).get('findings', []):
            title = finding.get('title', '')
            category = finding.get('category', '')
            key = f"{category}:{title}"
            
            if key not in finding_patterns:
                finding_patterns[key] = {
                    'title': title,
                    'category': category,
                    'severity': finding.get('severity'),
                    'count': 0,
                    'stacks': set(),
                    'first_seen': review.get('created_at'),
                    'last_seen': review.get('created_at')
                }
            
            finding_patterns[key]['count'] += 1
            if stack_id:
                finding_patterns[key]['stacks'].add(stack_id)
            else:
                finding_patterns[key]['stacks'].add(review.get('spacelift_context', {}).get('stack_id', 'unknown'))
            
            if review.get('created_at') < finding_patterns[key]['first_seen']:
                finding_patterns[key]['first_seen'] = review.get('created_at')
            if review.get('created_at') > finding_patterns[key]['last_seen']:
                finding_patterns[key]['last_seen'] = review.get('created_at')
    
    # Convert sets to lists for JSON serialization
    for key, pattern in finding_patterns.items():
        pattern['stacks'] = list(pattern['stacks'])
        pattern['stack_count'] = len(pattern['stacks'])
    
    # Sort by frequency
    sorted_patterns = sorted(
        finding_patterns.values(),
        key=lambda x: x['count'],
        reverse=True
    )
    
    return {
        'analysis_type': 'patterns',
        'period_days': days,
        'stack_id': stack_id,
        'patterns': sorted_patterns[:20],  # Top 20
        'summary': {
            'total_patterns': len(finding_patterns),
            'most_common': sorted_patterns[0] if sorted_patterns else None
        }
    }


def analyze_correlations(stack_id: str = None, days: int = 30) -> Dict[str, Any]:
    """Analyze correlations between findings and outcomes"""
    reviews = db_client.query_reviews(days=days) if not stack_id else db_client.query_reviews_by_stack(stack_id, days=days)
    
    # Correlate findings with risk scores
    correlations = {
        'security_to_risk': [],
        'cost_to_risk': [],
        'reliability_to_risk': []
    }
    
    for review in reviews:
        ai_result = review.get('ai_review_result', {})
        if not ai_result:
            continue
        
        risk_score = ai_result.get('overall_risk_score', 0.0)
        
        security = ai_result.get('security_analysis', {})
        correlations['security_to_risk'].append({
            'finding_count': security.get('total_findings', 0),
            'risk_score': float(risk_score)
        })
        
        cost = ai_result.get('cost_analysis', {})
        correlations['cost_to_risk'].append({
            'optimization_count': len(cost.get('cost_optimizations', [])),
            'risk_score': float(risk_score)
        })
        
        reliability = ai_result.get('reliability_analysis', {})
        correlations['reliability_to_risk'].append({
            'spof_count': len(reliability.get('single_points_of_failure', [])),
            'risk_score': float(risk_score)
        })
    
    return {
        'analysis_type': 'correlations',
        'period_days': days,
        'stack_id': stack_id,
        'correlations': correlations,
        'summary': {
            'total_data_points': len(reviews)
        }
    }


def create_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Create API Gateway response"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(body, default=str)  # Handle Decimal serialization
    }

