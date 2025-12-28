import boto3
import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from decimal import Decimal
from models import Review, AnalyticsResponse

class DynamoDBClient:
    def __init__(self, table_name: str):
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(table_name)
    
    def _serialize(self, obj: Any) -> Any:
        """Convert Python types to DynamoDB-compatible types"""
        if isinstance(obj, dict):
            return {k: self._serialize(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._serialize(item) for item in obj]
        elif isinstance(obj, float):
            return Decimal(str(obj))
        elif isinstance(obj, bool):
            return obj
        elif isinstance(obj, (int, str)):
            return obj
        else:
            return str(obj)
    
    def _deserialize(self, obj: Any) -> Any:
        """Convert DynamoDB types to Python types"""
        if isinstance(obj, dict):
            return {k: self._deserialize(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._deserialize(item) for item in obj]
        elif isinstance(obj, Decimal):
            return float(obj)
        else:
            return obj
    
    def create_review(self, review: Review) -> Dict[str, Any]:
        """Create a new review with versioning"""
        item = {
            'PK': f'REVIEW#{review.review_id}',
            'SK': f'VERSION#{review.version}',
            'GSI1PK': f'SPACELIFT_RUN#{review.spacelift_run_id}' if review.spacelift_run_id else f'REVIEW#{review.review_id}',
            'GSI1SK': f'CREATED#{review.created_at}',
            'GSI2PK': f'STATUS#{review.status}',
            'GSI2SK': f'CREATED#{review.created_at}',
            **review.dict()
        }
        
        serialized_item = self._serialize(item)
        self.table.put_item(Item=serialized_item)
        
        return self._deserialize(serialized_item)
    
    def get_review(self, review_id: str, version: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Get a review by ID, optionally by version"""
        if version:
            response = self.table.get_item(
                Key={
                    'PK': f'REVIEW#{review_id}',
                    'SK': f'VERSION#{version}'
                }
            )
        else:
            # Get latest version
            response = self.table.query(
                KeyConditionExpression='PK = :pk',
                ExpressionAttributeValues={
                    ':pk': f'REVIEW#{review_id}'
                },
                ScanIndexForward=False,
                Limit=1
            )
            items = response.get('Items', [])
            if not items:
                return None
            return self._deserialize(items[0])
        
        item = response.get('Item')
        if not item:
            return None
        
        return self._deserialize(item)
    
    def update_review(self, review_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a review and create a new version"""
        # Get current version
        current = self.get_review(review_id)
        if not current:
            raise ValueError(f"Review {review_id} not found")
        
        # Increment version
        new_version = current.get('version', 1) + 1
        
        # Create new version
        previous_version_id = f"{review_id}#VERSION#{current.get('version', 1)}"
        new_review = Review(**{**current, **update_data, 'version': new_version, 'previous_version_id': previous_version_id})
        
        return self.create_review(new_review)
    
    def query_reviews(self, spacelift_run_id: Optional[str] = None, 
                     status: Optional[str] = None, limit: int = 50,
                     days: Optional[int] = None) -> List[Dict[str, Any]]:
        """Query reviews by various criteria"""
        if spacelift_run_id:
            response = self.table.query(
                IndexName='GSI1',
                KeyConditionExpression='GSI1PK = :gsi1pk',
                ExpressionAttributeValues={
                    ':gsi1pk': f'SPACELIFT_RUN#{spacelift_run_id}'
                },
                ScanIndexForward=False,
                Limit=limit
            )
        elif status:
            response = self.table.query(
                IndexName='GSI2',
                KeyConditionExpression='GSI2PK = :gsi2pk',
                ExpressionAttributeValues={
                    ':gsi2pk': f'STATUS#{status}'
                },
                ScanIndexForward=False,
                Limit=limit
            )
        else:
            # Scan for all reviews (latest versions only)
            filter_expr = 'begins_with(PK, :prefix)'
            expr_values = {':prefix': 'REVIEW#'}
            
            # Add date filter if specified
            if days:
                from datetime import datetime, timedelta
                cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
                filter_expr += ' AND GSI1SK >= :cutoff'
                expr_values[':cutoff'] = f'CREATED#{cutoff_date}'
            
            response = self.table.scan(
                FilterExpression=filter_expr,
                ExpressionAttributeValues=expr_values,
                Limit=limit
            )
        
        items = response.get('Items', [])
        
        # Deduplicate by review_id, keeping latest version
        seen = {}
        for item in items:
            deserialized = self._deserialize(item)
            review_id = deserialized.get('review_id')
            if review_id and (review_id not in seen or deserialized.get('version', 0) > seen[review_id].get('version', 0)):
                seen[review_id] = deserialized
        
            return list(seen.values())
    
    def query_reviews_by_stack(self, stack_id: str, days: Optional[int] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Query reviews for a specific stack"""
        key_condition = 'GSI1PK = :gsi1pk'
        expr_values = {':gsi1pk': f'STACK#{stack_id}'}
        
        # Add date filter if specified
        if days:
            from datetime import datetime, timedelta
            cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
            key_condition += ' AND GSI1SK >= :cutoff'
            expr_values[':cutoff'] = f'CREATED#{cutoff_date}'
        
        response = self.table.query(
            IndexName='GSI1',
            KeyConditionExpression=key_condition,
            ExpressionAttributeValues=expr_values,
            ScanIndexForward=False,
            Limit=limit
        )
        
        items = response.get('Items', [])
        return [self._deserialize(item) for item in items]
    
    def get_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get analytics data for the last N days"""
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        # Get all reviews from the period
        response = self.table.scan(
            FilterExpression='begins_with(PK, :prefix) AND GSI1SK >= :cutoff',
            ExpressionAttributeValues={
                ':prefix': 'REVIEW#',
                ':cutoff': f'CREATED#{cutoff_date}'
            }
        )
        
        items = [self._deserialize(item) for item in response.get('Items', [])]
        
        # Deduplicate and get latest versions
        reviews = {}
        for item in items:
            review_id = item.get('review_id')
            if review_id and (review_id not in reviews or item.get('version', 0) > reviews[review_id].get('version', 0)):
                reviews[review_id] = item
        
        review_list = list(reviews.values())
        
        # Calculate analytics
        total_reviews = len(review_list)
        reviews_by_status = {}
        reviews_by_risk = {'low': 0, 'medium': 0, 'high': 0}
        risk_scores = []
        all_findings = []
        
        for review in review_list:
            status = review.get('status', 'unknown')
            reviews_by_status[status] = reviews_by_status.get(status, 0) + 1
            
            ai_result = review.get('ai_review_result')
            if ai_result:
                risk_score = ai_result.get('overall_risk_score', 0)
                risk_scores.append(risk_score)
                
                if risk_score < 0.33:
                    reviews_by_risk['low'] += 1
                elif risk_score < 0.67:
                    reviews_by_risk['medium'] += 1
                else:
                    reviews_by_risk['high'] += 1
                
                # Collect findings
                security = ai_result.get('security_analysis', {})
                for finding in security.get('findings', []):
                    all_findings.append(finding)
        
        # Top findings by frequency
        finding_counts = {}
        for finding in all_findings:
            title = finding.get('title', 'Unknown')
            finding_counts[title] = finding_counts.get(title, 0) + 1
        
        top_findings = sorted(finding_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Trend data (daily)
        trend_data = {}
        for review in review_list:
            created_at = review.get('created_at', '')
            if created_at:
                date = created_at.split('T')[0]
                trend_data[date] = trend_data.get(date, 0) + 1
        
        trend_list = [{'date': k, 'count': v} for k, v in sorted(trend_data.items())]
        
        return {
            'total_reviews': total_reviews,
            'reviews_by_status': reviews_by_status,
            'reviews_by_risk': reviews_by_risk,
            'average_risk_score': sum(risk_scores) / len(risk_scores) if risk_scores else 0.0,
            'trend_data': trend_list,
            'top_findings': [{'title': title, 'count': count} for title, count in top_findings]
        }

