"""
Test API Handler Lambda Function Locally
"""

import json
import sys
import os
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock environment variables
os.environ['DYNAMODB_TABLE_NAME'] = 'test-reviews'
os.environ['ENVIRONMENT'] = 'test'

def test_get_reviews():
    """Test GET /api/reviews endpoint"""
    from api_handler import handler
    
    event = {
        "requestContext": {
            "http": {
                "method": "GET",
                "path": "/api/reviews"
            }
        },
        "rawPath": "/api/reviews",
        "queryStringParameters": None
    }
    
    context = {}
    
    # Mock DynamoDB
    with patch('api_handler.dynamodb') as mock_dynamodb:
        mock_dynamodb.scan.return_value = {
            'Items': [
                {
                    'PK': {'S': 'REVIEW#test-1'},
                    'SK': {'S': 'METADATA'},
                    'review_id': {'S': 'test-1'},
                    'status': {'S': 'completed'}
                }
            ],
            'Count': 1
        }
        
        response = handler(event, context)
        
        print("Response Status:", response['statusCode'])
        print("Response Body:", json.dumps(json.loads(response['body']), indent=2))
        
        assert response['statusCode'] == 200

def test_create_review():
    """Test POST /api/reviews endpoint"""
    from api_handler import handler
    
    event = {
        "requestContext": {
            "http": {
                "method": "POST",
                "path": "/api/reviews"
            }
        },
        "rawPath": "/api/reviews",
        "body": json.dumps({
            "terraform_code": "resource \"aws_s3_bucket\" \"test\" {}",
            "spacelift_run_id": "test-run-123"
        })
    }
    
    context = {}
    
    # Mock DynamoDB
    with patch('api_handler.dynamodb') as mock_dynamodb:
        mock_dynamodb.put_item.return_value = {}
        
        response = handler(event, context)
        
        print("Response Status:", response['statusCode'])
        print("Response Body:", json.dumps(json.loads(response['body']), indent=2))
        
        assert response['statusCode'] == 201

if __name__ == "__main__":
    print("Testing API Handler...")
    test_get_reviews()
    test_create_review()
    print("All tests passed!")

