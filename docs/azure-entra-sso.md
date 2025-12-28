# Azure Entra ID SSO Implementation

## Overview

Complete Azure Entra ID (Azure AD) SSO integration with AWS IAM Identity Center, Cognito, and API Gateway JWT validation.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AZURE ENTRA ID                           │
│  - User Directory                                            │
│  - Groups (Admin, Reviewer, ReadOnly)                        │
│  - SAML Identity Provider                                     │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ SAML 2.0
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ AWS IAM      │   │ COGNITO      │   │ API GATEWAY │
│ IDENTITY     │   │ USER POOL    │   │ (JWT Auth)  │
│ CENTER       │   │              │   │             │
│              │   │              │   │             │
│ - SSO        │   │ - OAuth      │   │ - JWT       │
│ - Permission │   │ - SAML       │   │   Validation│
│   Sets       │   │ - JWT Tokens│   │ - RBAC      │
└──────────────┘   └──────────────┘   └──────────────┘
        │                   │                   │
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │  LAMBDA      │
                    │  FUNCTIONS   │
                    └──────────────┘
```

## Authentication Flows

### Flow 1: Frontend Authentication (Cognito)

```
┌──────────┐
│  User    │
└────┬─────┘
     │ 1. Click "Sign in with Azure"
     ▼
┌─────────────────┐
│  Frontend       │
│  (Next.js)      │
└────┬────────────┘
     │ 2. Redirect to Cognito Hosted UI
     ▼
┌─────────────────┐
│  Cognito        │
│  Hosted UI      │
└────┬────────────┘
     │ 3. Redirect to Azure Entra ID
     ▼
┌─────────────────┐
│  Azure Entra ID │
│  (SAML)         │
└────┬────────────┘
     │ 4. User authenticates
     │ 5. SAML assertion
     ▼
┌─────────────────┐
│  Cognito        │
│  (SAML Provider)│
└────┬────────────┘
     │ 6. JWT tokens
     ▼
┌─────────────────┐
│  Frontend       │
│  (Callback)     │
└────┬────────────┘
     │ 7. Store tokens
     ▼
┌─────────────────┐
│  API Requests   │
│  (with JWT)     │
└─────────────────┘
```

### Flow 2: Backend API Access (IAM Identity Center)

```
┌──────────┐
│  User    │
└────┬─────┘
     │ 1. Access AWS Console
     ▼
┌─────────────────┐
│  AWS IAM        │
│  Identity Center│
└────┬────────────┘
     │ 2. SAML request
     ▼
┌─────────────────┐
│  Azure Entra ID │
│  (SAML)         │
└────┬────────────┘
     │ 3. User authenticates
     │ 4. SAML assertion
     ▼
┌─────────────────┐
│  AWS IAM        │
│  Identity Center│
└────┬────────────┘
     │ 5. Assume role
     ▼
┌─────────────────┐
│  Application    │
│  Account Role   │
└─────────────────┘
```

### Flow 3: API Gateway JWT Validation

```
┌──────────┐
│  Client  │
└────┬─────┘
     │ 1. API Request + JWT
     ▼
┌─────────────────┐
│  API Gateway   │
└────┬───────────┘
     │ 2. Invoke Authorizer
     ▼
┌─────────────────┐
│  JWT Authorizer │
│  Lambda         │
└────┬────────────┘
     │ 3. Validate JWT
     │    - Verify signature
     │    - Check expiration
     │    - Extract groups
     │ 4. Check permissions
     ▼
┌─────────────────┐
│  Allow/Deny     │
└─────────────────┘
     │
     ▼
┌─────────────────┐
│  Lambda Handler │
│  (if allowed)   │
└─────────────────┘
```

## Role-Based Access Control

### Roles

**Admin**:
- Full access to all resources
- Can create, read, update, delete reviews
- Can access all analytics
- Can manage system configuration

**Reviewer**:
- Can create reviews
- Can view own reviews
- Can view analytics
- Cannot delete reviews
- Cannot modify system settings

**ReadOnly**:
- Can view reviews
- Can view analytics
- Cannot create or modify reviews
- Cannot access admin functions

### Permission Mapping

| Route | Method | Admin | Reviewer | ReadOnly |
|-------|--------|-------|----------|----------|
| `/api/reviews` | GET | ✅ | ✅ | ✅ |
| `/api/reviews` | POST | ✅ | ✅ | ❌ |
| `/api/reviews/{id}` | GET | ✅ | ✅ | ✅ |
| `/api/reviews/{id}` | PUT | ✅ | ✅ | ❌ |
| `/api/analytics` | GET | ✅ | ✅ | ✅ |
| `/api/analytics/historical` | GET | ✅ | ✅ | ✅ |
| `/webhook/*` | POST | ✅ | ✅ | ❌ |

## Trust Policies

### Cognito Identity Pool Trust Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "cognito-identity.amazonaws.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "cognito-identity.amazonaws.com:aud": "${identity_pool_id}"
        },
        "ForAnyValue:StringLike": {
          "cognito-identity.amazonaws.com:amr": "authenticated"
        }
      }
    }
  ]
}
```

### Cross-Account Role Trust Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::MANAGEMENT_ACCOUNT:root"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "sts:ExternalId": "${external_id}"
        },
        "StringLike": {
          "aws:PrincipalTag/Role": "Reviewer"
        }
      }
    },
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::MANAGEMENT_ACCOUNT:saml-provider/AzureAD"
      },
      "Action": "sts:AssumeRoleWithSAML",
      "Condition": {
        "StringEquals": {
          "SAML:aud": "https://signin.aws.amazon.com/saml"
        }
      }
    }
  ]
}
```

## Configuration Steps

### 1. Configure Azure Entra ID

1. **Create Enterprise Application**:
   - Register new application in Azure AD
   - Configure SAML SSO
   - Set identifier: `urn:amazon:cognito:sp:${user_pool_id}`
   - Set reply URL: `https://${domain}.auth.${region}.amazoncognito.com/saml2/idpresponse`

2. **Configure User Attributes**:
   - Map `email` → `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress`
   - Map `groups` → `http://schemas.microsoft.com/ws/2008/06/identity/claims/groups`

3. **Create Groups**:
   - `aws-admins` → Maps to Admin role
   - `aws-reviewers` → Maps to Reviewer role
   - `aws-readonly` → Maps to ReadOnly role

4. **Assign Users to Groups**

### 2. Configure AWS IAM Identity Center

1. **Enable IAM Identity Center** (Management Account)

2. **Configure External Identity Provider**:
   - Upload Azure AD SAML metadata
   - Configure attribute mapping

3. **Create Permission Sets**:
   - AdminAccess
   - ReviewerAccess
   - ReadOnlyAccess

4. **Assign Groups to Accounts**:
   - Map Azure groups to permission sets
   - Assign to application accounts

### 3. Configure Cognito

1. **Create User Pool** with SAML provider

2. **Configure Azure AD as Identity Provider**:
   - Upload SAML metadata
   - Configure attribute mapping

3. **Create User Pool Client**:
   - Enable OAuth flows
   - Configure callback URLs

4. **Create Identity Pool**:
   - Link to User Pool
   - Configure authenticated role

### 4. Deploy Infrastructure

```bash
cd terraform
terraform init
terraform apply
```

## JWT Token Structure

### ID Token Payload

```json
{
  "sub": "user-uuid",
  "email": "user@example.com",
  "cognito:groups": ["aws-reviewers"],
  "cognito:username": "user@example.com",
  "aud": "cognito-client-id",
  "iss": "https://cognito-idp.region.amazonaws.com/pool-id",
  "exp": 1234567890,
  "iat": 1234567890
}
```

## Security Considerations

### Token Validation

1. **Signature Verification**: Verify JWT signature using JWKS
2. **Expiration Check**: Validate token expiration
3. **Audience Check**: Verify token audience matches client ID
4. **Issuer Check**: Verify token issuer matches Cognito

### Role Enforcement

1. **API Gateway**: JWT authorizer enforces roles
2. **Lambda Functions**: Additional checks if needed
3. **DynamoDB**: Resource-based policies

### Best Practices

1. **Token Storage**: Store tokens securely (httpOnly cookies recommended)
2. **Token Refresh**: Implement token refresh mechanism
3. **HTTPS Only**: All authentication over HTTPS
4. **MFA**: Enable MFA in Cognito
5. **Session Management**: Implement proper session timeout

## Troubleshooting

### Common Issues

1. **Token Expired**:
   - Implement token refresh
   - Redirect to login

2. **Invalid Signature**:
   - Check JWKS URL
   - Verify Cognito configuration

3. **Missing Groups**:
   - Verify Azure AD group mapping
   - Check Cognito attribute mapping

4. **Cross-Account Access Denied**:
   - Verify trust policy
   - Check external ID
   - Verify IAM Identity Center assignments

## References

- [AWS IAM Identity Center Documentation](https://docs.aws.amazon.com/singlesignon/)
- [Amazon Cognito Documentation](https://docs.aws.amazon.com/cognito/)
- [Azure Entra ID SAML](https://learn.microsoft.com/en-us/azure/active-directory/develop/single-sign-on-saml-protocol)

