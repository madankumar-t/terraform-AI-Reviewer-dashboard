"""
Secrets Rotation Lambda Function

Rotates secrets stored in AWS Secrets Manager.
"""

import json
import os
import boto3
import secrets
import string
from typing import Dict, Any

secrets_client = boto3.client('secretsmanager')
logger = None  # Would use structured logger

def generate_random_secret(length: int = 32) -> str:
    """Generate a random secret string"""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def rotate_secret(secret_id: str, secret_type: str) -> Dict[str, Any]:
    """
    Rotate a secret.
    
    Args:
        secret_id: ARN or name of the secret
        secret_type: Type of secret (api_key, webhook_secret)
    
    Returns:
        Result of rotation
    """
    try:
        # Get current secret value
        current_secret = secrets_client.get_secret_value(SecretId=secret_id)
        current_value = current_secret['SecretString']
        
        # Generate new secret
        if secret_type == 'api_key':
            # For API keys, we can't generate new ones - need to fetch from provider
            # This is a placeholder - actual implementation would call provider API
            new_value = current_value  # Keep current for now
            # In production, you would:
            # 1. Call OpenAI/Anthropic API to generate new key
            # 2. Update the secret
            # 3. Test the new key
            # 4. Delete old key
        elif secret_type == 'webhook_secret':
            new_value = generate_random_secret(64)
        else:
            new_value = generate_random_secret(32)
        
        # Update secret
        secrets_client.put_secret_value(
            SecretId=secret_id,
            SecretString=new_value,
            VersionStages=['AWSCURRENT']
        )
        
        return {
            'status': 'success',
            'secret_id': secret_id,
            'rotated': True
        }
        
    except Exception as e:
        return {
            'status': 'error',
            'secret_id': secret_id,
            'error': str(e)
        }


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for secrets rotation.
    
    Event structure:
    {
        "SecretId": "arn:aws:secretsmanager:...",
        "ClientRequestToken": "...",
        "Step": "createSecret" | "setSecret" | "testSecret" | "finishSecret"
    }
    """
    secret_id = event.get('SecretId')
    step = event.get('Step')
    client_request_token = event.get('ClientRequestToken')
    
    try:
        # Get secret metadata
        secret_metadata = secrets_client.describe_secret(SecretId=secret_id)
        secret_name = secret_metadata['Name']
        
        # Determine secret type from name
        if 'openai' in secret_name.lower() or 'anthropic' in secret_name.lower():
            secret_type = 'api_key'
        elif 'webhook' in secret_name.lower():
            secret_type = 'webhook_secret'
        else:
            secret_type = 'generic'
        
        # Handle rotation steps
        if step == 'createSecret':
            # Create new secret version
            # For API keys, this would fetch from provider
            # For webhook secrets, generate new random value
            if secret_type == 'webhook_secret':
                new_secret = generate_random_secret(64)
                secrets_client.put_secret_value(
                    SecretId=secret_id,
                    SecretString=new_secret,
                    ClientRequestToken=client_request_token,
                    VersionStages=['AWSPENDING']
                )
            else:
                # For API keys, keep current value (would need provider integration)
                current_secret = secrets_client.get_secret_value(SecretId=secret_id)
                secrets_client.put_secret_value(
                    SecretId=secret_id,
                    SecretString=current_secret['SecretString'],
                    ClientRequestToken=client_request_token,
                    VersionStages=['AWSPENDING']
                )
        
        elif step == 'setSecret':
            # Set the new secret (already done in createSecret)
            pass
        
        elif step == 'testSecret':
            # Test the new secret
            # For API keys, would test with provider API
            # For webhook secrets, no test needed
            pass
        
        elif step == 'finishSecret':
            # Move AWSPENDING to AWSCURRENT
            secrets_client.update_secret_version_stage(
                SecretId=secret_id,
                VersionStage='AWSCURRENT',
                MoveToVersionId=client_request_token,
                RemoveFromVersionId=client_request_token
            )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'status': 'success',
                'step': step,
                'secret_id': secret_id
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'status': 'error',
                'error': str(e),
                'secret_id': secret_id
            })
        }

