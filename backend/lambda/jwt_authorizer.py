"""
JWT Authorizer for API Gateway

Validates JWT tokens from Cognito and enforces role-based access control.
"""

import json
import os
import jwt
import requests
from typing import Dict, Any, Optional
from functools import lru_cache
from datetime import datetime
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

from logger import StructuredLogger

logger = StructuredLogger('jwt-authorizer', os.environ.get('ENVIRONMENT'))

# Cognito configuration
COGNITO_USER_POOL_ID = os.environ.get('COGNITO_USER_POOL_ID')
COGNITO_CLIENT_ID = os.environ.get('COGNITO_CLIENT_ID')
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')

# JWKS URL
JWKS_URL = f"https://cognito-idp.{AWS_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}/.well-known/jwks.json"


@lru_cache(maxsize=1)
def get_jwks():
    """Get JSON Web Key Set from Cognito (cached)"""
    try:
        response = requests.get(JWKS_URL, timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error('Error fetching JWKS', error=e)
        raise


def get_signing_key(token: str, jwks: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Get the signing key for the token"""
    try:
        # Decode token header to get kid
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get('kid')
        
        if not kid:
            return None
        
        # Find key in JWKS
        for key in jwks.get('keys', []):
            if key.get('kid') == kid:
                return key
        
        return None
    except Exception as e:
        logger.error('Error getting signing key', error=e)
        return None


def jwk_to_pem(jwk_dict: Dict[str, Any]) -> str:
    """Convert JWK to PEM format for PyJWT"""
    from cryptography.hazmat.primitives.asymmetric import rsa
    import base64
    
    # Extract key components
    n = base64.urlsafe_b64decode(jwk_dict['n'] + '==')
    e = base64.urlsafe_b64decode(jwk_dict['e'] + '==')
    
    # Convert to integers
    n_int = int.from_bytes(n, 'big')
    e_int = int.from_bytes(e, 'big')
    
    # Create RSA public key
    public_key = rsa.RSAPublicNumbers(e_int, n_int).public_key(default_backend())
    
    # Serialize to PEM
    pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    return pem.decode('utf-8')


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify and decode JWT token.
    
    Returns:
        Decoded token payload or None if invalid
    """
    try:
        # Get JWKS
        jwks = get_jwks()
        
        # Get signing key
        key = get_signing_key(token, jwks)
        if not key:
            logger.warning('Signing key not found for token')
            return None
        
        # Convert JWK to PEM
        public_key_pem = jwk_to_pem(key)
        
        # Decode and verify token
        decoded = jwt.decode(
            token,
            public_key_pem,
            algorithms=['RS256'],
            audience=COGNITO_CLIENT_ID,
            issuer=f"https://cognito-idp.{AWS_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}"
        )
        
        return decoded
    except jwt.ExpiredSignatureError:
        logger.warning('Token expired')
        return None
    except jwt.InvalidTokenError as e:
        logger.warning('Invalid token', error=e)
        return None
    except Exception as e:
        logger.error('Error verifying token', error=e)
        return None


def get_user_groups(token_payload: Dict[str, Any]) -> list:
    """Extract user groups from token"""
    # Groups can be in 'cognito:groups' or 'groups' claim
    groups = token_payload.get('cognito:groups', [])
    if not groups:
        groups = token_payload.get('groups', [])
    
    return groups if isinstance(groups, list) else []


def check_permission(groups: list, required_role: str) -> bool:
    """
    Check if user has required role.
    
    Roles hierarchy:
    - Admin: Can do everything
    - Reviewer: Can create and view reviews
    - ReadOnly: Can only view reviews
    """
    if 'admin' in [g.lower() for g in groups]:
        return True  # Admin has all permissions
    
    if required_role == 'readonly':
        return True  # All authenticated users can read
    
    if required_role == 'reviewer':
        return 'reviewer' in [g.lower() for g in groups] or 'admin' in [g.lower() for g in groups]
    
    return False


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    API Gateway Lambda Authorizer.
    
    Event structure:
    {
        "type": "TOKEN",
        "authorizationToken": "Bearer <token>",
        "methodArn": "arn:aws:execute-api:..."
    }
    """
    try:
        # Extract token
        auth_token = event.get('authorizationToken', '')
        if not auth_token:
            logger.security_event(
                event_type='authorization_missing',
                severity='medium',
                method_arn=event.get('methodArn')
            )
            return generate_policy('user', 'Deny', event.get('methodArn'))
        
        # Remove 'Bearer ' prefix if present
        if auth_token.startswith('Bearer '):
            token = auth_token[7:]
        else:
            token = auth_token
        
        # Verify token
        token_payload = verify_token(token)
        if not token_payload:
            logger.security_event(
                event_type='authorization_failed',
                severity='high',
                method_arn=event.get('methodArn')
            )
            return generate_policy('user', 'Deny', event.get('methodArn'))
        
        # Extract user information
        user_id = token_payload.get('sub', 'unknown')
        email = token_payload.get('email', '')
        groups = get_user_groups(token_payload)
        
        # Determine required role from route
        method_arn = event.get('methodArn', '')
        required_role = get_required_role(method_arn)
        
        # Check permissions
        if not check_permission(groups, required_role):
            logger.security_event(
                event_type='authorization_insufficient_permissions',
                severity='medium',
                user_id=user_id,
                required_role=required_role,
                user_groups=groups,
                method_arn=method_arn
            )
            return generate_policy(user_id, 'Deny', method_arn)
        
        # Audit log successful authorization
        logger.audit(
            event_type='authorization_granted',
            user_id=user_id,
            resource=method_arn,
            action='access',
            user_groups=groups,
            required_role=required_role
        )
        
        # Generate allow policy with context
        policy = generate_policy(user_id, 'Allow', method_arn)
        policy['context'] = {
            'user_id': user_id,
            'email': email,
            'groups': ','.join(groups)
        }
        
        return policy
        
    except Exception as e:
        logger.error('Error in JWT authorizer', error=e)
        return generate_policy('user', 'Deny', event.get('methodArn', ''))


def get_required_role(method_arn: str) -> str:
    """
    Determine required role based on API route.
    
    Routes:
    - POST /api/reviews* -> reviewer
    - PUT /api/reviews* -> reviewer
    - GET /api/* -> readonly
    - POST /webhook/* -> (no auth, webhook signature)
    """
    if '/webhook/' in method_arn:
        return 'none'  # Webhooks use signature verification
    
    if 'POST' in method_arn or 'PUT' in method_arn:
        if '/api/reviews' in method_arn:
            return 'reviewer'
        return 'admin'  # Other write operations require admin
    
    # GET requests are readonly
    return 'readonly'


def generate_policy(principal_id: str, effect: str, resource: str) -> Dict[str, Any]:
    """Generate IAM policy for API Gateway"""
    policy = {
        'principalId': principal_id,
        'policyDocument': {
            'Version': '2012-10-17',
            'Statement': [
                {
                    'Action': 'execute-api:Invoke',
                    'Effect': effect,
                    'Resource': resource
                }
            ]
        }
    }
    
    return policy

