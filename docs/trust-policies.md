# Trust Policies Reference

## Overview

Complete trust policy configurations for Azure Entra ID SSO integration with AWS services.

## 1. Cognito Identity Pool Trust Policy

### Authenticated Users Role

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

**Purpose**: Allows authenticated Cognito users to assume role for API Gateway access.

**Conditions**:
- Identity pool ID must match
- User must be authenticated (not unauthenticated)

## 2. Cross-Account Role Trust Policies

### Reviewer Role (Application Account)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowManagementAccount",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::${management_account_id}:root"
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
      "Sid": "AllowSAMLFederation",
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::${management_account_id}:saml-provider/AzureAD"
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

**Purpose**: Allows users from management account to assume reviewer role in application account.

**Conditions**:
- External ID must match (prevents confused deputy)
- Principal must have Reviewer tag (from IAM Identity Center)
- SAML assertion audience must be AWS sign-in URL

### Admin Role (Application Account)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowManagementAccountAdmin",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::${management_account_id}:root"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "sts:ExternalId": "${external_id}"
        },
        "StringLike": {
          "aws:PrincipalTag/Role": "Admin"
        }
      }
    },
    {
      "Sid": "AllowSAMLFederationAdmin",
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::${management_account_id}:saml-provider/AzureAD"
      },
      "Action": "sts:AssumeRoleWithSAML",
      "Condition": {
        "StringEquals": {
          "SAML:aud": "https://signin.aws.amazon.com/saml",
          "SAML:NameQualifier": "${azure_tenant_id}"
        }
      }
    }
  ]
}
```

**Purpose**: Allows admin users to assume admin role with full permissions.

**Conditions**:
- External ID required
- Admin role tag required
- SAML NameQualifier matches Azure tenant

### ReadOnly Role (Application Account)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowManagementAccountReadOnly",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::${management_account_id}:root"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "sts:ExternalId": "${external_id}"
        },
        "StringLike": {
          "aws:PrincipalTag/Role": "ReadOnly"
        }
      }
    },
    {
      "Sid": "AllowSAMLFederationReadOnly",
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::${management_account_id}:saml-provider/AzureAD"
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

**Purpose**: Allows read-only access for viewing reviews and analytics.

## 3. IAM Identity Center Trust Relationship

### Azure Entra ID as Identity Provider

**Configuration** (via AWS Console or CLI):
- Identity Provider Type: External Identity Provider
- Protocol: SAML 2.0
- Metadata Source: Azure Entra ID SAML metadata XML

**Attribute Mapping**:
- `NameID` → AWS username
- `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress` → Email
- `http://schemas.microsoft.com/ws/2008/06/identity/claims/groups` → Groups

**Trust Relationship**:
- Azure AD trusts IAM Identity Center
- IAM Identity Center trusts Azure AD
- Mutual trust via SAML

## 4. Cognito User Pool Trust Relationship

### Azure Entra ID as SAML Provider

**Configuration**:
- Provider Type: SAML
- Metadata Document: Azure Entra ID SAML metadata XML
- Attribute Mapping:
  - `email` → `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress`
  - `groups` → `http://schemas.microsoft.com/ws/2008/06/identity/claims/groups`

**Trust Relationship**:
- Cognito trusts Azure AD (via SAML)
- Azure AD trusts Cognito (via reply URL)

## 5. API Gateway Authorizer Trust

### JWT Authorizer Lambda Trust

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "apigateway.amazonaws.com"
      },
      "Action": "lambda:InvokeFunction",
      "Resource": "arn:aws:lambda:${region}:${account}:function:${function_name}",
      "Condition": {
        "ArnLike": {
          "aws:SourceArn": "arn:aws:execute-api:${region}:${account}:${api_id}/authorizers/*"
        }
      }
    }
  ]
}
```

**Purpose**: Allows API Gateway to invoke JWT authorizer Lambda.

## 6. Session Policies

### Reviewer Session Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:Query",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem"
      ],
      "Resource": [
        "arn:aws:dynamodb:${region}:${account}:table/${table_name}",
        "arn:aws:dynamodb:${region}:${account}:table/${table_name}/index/*"
      ],
      "Condition": {
        "StringEquals": {
          "dynamodb:LeadingKeys": "${aws:userid}"
        }
      }
    }
  ]
}
```

**Purpose**: Further restricts permissions at session level.

## Security Best Practices

### 1. External ID Usage

**Purpose**: Prevents confused deputy attacks

**Implementation**:
- Unique external ID per account relationship
- Stored in Secrets Manager
- Rotated periodically

### 2. Principal Tag Conditions

**Purpose**: Ensures only users with correct permission sets can assume roles

**Implementation**:
- IAM Identity Center tags users with role
- Trust policy checks tag
- Prevents privilege escalation

### 3. SAML Audience Validation

**Purpose**: Ensures SAML assertions are for AWS, not other services

**Implementation**:
- Validate `SAML:aud` claim
- Must equal `https://signin.aws.amazon.com/saml`

### 4. Time-Based Conditions

**Example** (optional):
```json
{
  "Condition": {
    "DateGreaterThan": {
      "aws:CurrentTime": "${session_start}"
    },
    "DateLessThan": {
      "aws:CurrentTime": "${session_end}"
    }
  }
}
```

## Multi-Account Trust Chain

```
Management Account
    │
    │ IAM Identity Center
    │ - User authenticated via Azure AD
    │ - Permission set assigned
    │
    ▼
Application Account
    │
    │ Cross-Account Role
    │ - Trust: Management Account
    │ - External ID: Required
    │ - Role Tag: Required
    │
    ▼
Application Resources
    │
    │ IAM Policy
    │ - Based on role
    │ - Resource-specific
    │
    ▼
DynamoDB / Lambda
```

## Troubleshooting

### Common Trust Policy Issues

1. **Access Denied**:
   - Check external ID matches
   - Verify principal ARN
   - Check role tag conditions

2. **SAML Assertion Rejected**:
   - Verify audience claim
   - Check issuer
   - Validate signature

3. **JWT Validation Failed**:
   - Check JWKS URL
   - Verify token expiration
   - Check audience/issuer

## References

- [AWS IAM Trust Policies](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_create_for-idp_saml.html)
- [Cognito Identity Pools](https://docs.aws.amazon.com/cognito/latest/developerguide/identity-pools.html)
- [IAM Identity Center Trust](https://docs.aws.amazon.com/singlesignon/latest/userguide/manage-your-identity-source-idp.html)

