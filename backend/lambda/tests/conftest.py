"""
Pytest configuration for Lambda function tests
"""

import pytest
import os
import sys
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture
def mock_dynamodb():
    """Mock DynamoDB client"""
    with patch('dynamodb_client.dynamodb') as mock:
        yield mock

@pytest.fixture
def mock_secrets_manager():
    """Mock Secrets Manager client"""
    with patch('secrets_manager.secrets_client') as mock:
        yield mock

@pytest.fixture
def mock_bedrock():
    """Mock Bedrock client"""
    with patch('bedrock_service.bedrock_client') as mock:
        yield mock

@pytest.fixture
def sample_event():
    """Sample API Gateway event"""
    return {
        "requestContext": {
            "http": {
                "method": "GET",
                "path": "/api/reviews"
            },
            "requestId": "test-request-id"
        },
        "rawPath": "/api/reviews",
        "queryStringParameters": None,
        "headers": {
            "Authorization": "Bearer mock-token"
        }
    }

@pytest.fixture
def sample_context():
    """Sample Lambda context"""
    context = MagicMock()
    context.function_name = "test-function"
    context.function_version = "$LATEST"
    context.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:test-function"
    context.memory_limit_in_mb = 512
    context.aws_request_id = "test-request-id"
    return context

@pytest.fixture(autouse=True)
def set_env_vars(monkeypatch):
    """Set environment variables for tests"""
    monkeypatch.setenv("DYNAMODB_TABLE_NAME", "test-reviews")
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("AWS_REGION", "us-east-1")

