import boto3
import os
import json
from typing import Optional

class SecretsManager:
    def __init__(self):
        self.client = boto3.client('secretsmanager')
    
    def get_secret(self, secret_name: str) -> Optional[str]:
        """Retrieve a secret from AWS Secrets Manager"""
        try:
            response = self.client.get_secret_value(SecretId=secret_name)
            if 'SecretString' in response:
                return response['SecretString']
            else:
                return response['SecretBinary'].decode('utf-8')
        except Exception as e:
            print(f"Error retrieving secret {secret_name}: {str(e)}")
            return None
    
    def get_openai_key(self) -> Optional[str]:
        """Get OpenAI API key"""
        secret_name = os.environ.get('OPENAI_SECRET_NAME')
        if not secret_name:
            return None
        return self.get_secret(secret_name)
    
    def get_anthropic_key(self) -> Optional[str]:
        """Get Anthropic API key"""
        secret_name = os.environ.get('ANTHROPIC_SECRET_NAME')
        if not secret_name:
            return None
        return self.get_secret(secret_name)
    
    def get_spacelift_secret(self) -> Optional[str]:
        """Get Spacelift webhook secret"""
        secret_name = os.environ.get('SPACELIFT_SECRET_NAME')
        if not secret_name:
            return None
        return self.get_secret(secret_name)

