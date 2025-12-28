# Authentication Flow Diagrams

## Complete Authentication Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           AZURE ENTRA ID                                    │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  User Directory                                                      │  │
│  │  - Users                                                              │  │
│  │  - Groups: aws-admins, aws-reviewers, aws-readonly                    │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Enterprise Application (SAML Provider)                               │  │
│  │  - SAML 2.0                                                          │  │
│  │  - Attribute Mapping                                                 │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                            │
                            │ SAML 2.0
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ AWS IAM      │   │ COGNITO      │   │ API GATEWAY  │
│ IDENTITY     │   │ USER POOL    │   │              │
│ CENTER       │   │              │   │              │
│              │   │              │   │              │
│ Permission   │   │ OAuth 2.0    │   │ JWT          │
│ Sets         │   │ SAML         │   │ Authorizer   │
│              │   │ JWT Tokens    │   │              │
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

## Flow 1: Frontend Authentication (Cognito + Azure Entra ID)

```
┌──────────┐
│  User    │
│ Browser  │
└────┬─────┘
     │
     │ 1. Navigate to /auth/login
     │    Click "Sign in with Azure"
     ▼
┌─────────────────────────────────┐
│  Frontend (Next.js)              │
│  - AuthService.signInWithAzure() │
└────┬────────────────────────────┘
     │
     │ 2. Redirect to Cognito Hosted UI
     │    https://domain.auth.region.amazoncognito.com/
     │    /oauth2/authorize?identity_provider=AzureAD
     ▼
┌─────────────────────────────────┐
│  Cognito Hosted UI              │
│  - Detects Azure AD provider    │
│  - Redirects to Azure            │
└────┬────────────────────────────┘
     │
     │ 3. Redirect to Azure Entra ID
     │    https://login.microsoftonline.com/...
     ▼
┌─────────────────────────────────┐
│  Azure Entra ID                 │
│  - User authenticates            │
│  - MFA if required              │
│  - Generates SAML assertion      │
└────┬────────────────────────────┘
     │
     │ 4. POST SAML assertion to Cognito
     │    https://domain.auth.region.amazoncognito.com/
     │    /saml2/idpresponse
     ▼
┌─────────────────────────────────┐
│  Cognito                        │
│  - Validates SAML assertion     │
│  - Creates/updates user          │
│  - Maps groups                  │
│  - Generates JWT tokens          │
└────┬────────────────────────────┘
     │
     │ 5. Redirect to callback URL
     │    /auth/callback?code=...
     ▼
┌─────────────────────────────────┐
│  Frontend Callback Handler       │
│  - Exchanges code for tokens     │
│  - Stores tokens                 │
│  - Redirects to dashboard        │
└────┬────────────────────────────┘
     │
     │ 6. User authenticated
     │    Token stored in localStorage
     ▼
┌─────────────────────────────────┐
│  Dashboard                      │
│  - Makes API calls with JWT      │
└─────────────────────────────────┘
```

## Flow 2: API Request with JWT

```
┌──────────┐
│  Frontend│
│  (Next.js)│
└────┬─────┘
     │
     │ 1. API Request
     │    GET /api/reviews
     │    Authorization: Bearer <jwt_token>
     ▼
┌─────────────────────────────────┐
│  API Gateway                    │
│  - Receives request             │
│  - Extracts Authorization header│
└────┬────────────────────────────┘
     │
     │ 2. Invoke JWT Authorizer
     ▼
┌─────────────────────────────────┐
│  JWT Authorizer Lambda          │
│  ┌──────────────────────────┐   │
│  │ 1. Extract token          │   │
│  │ 2. Fetch JWKS from Cognito│   │
│  │ 3. Verify signature      │   │
│  │ 4. Check expiration      │   │
│  │ 5. Extract groups        │   │
│  │ 6. Check permissions     │   │
│  └──────────────────────────┘   │
└────┬────────────────────────────┘
     │
     │ 3. Generate IAM Policy
     │    Allow/Deny
     ▼
┌─────────────────────────────────┐
│  API Gateway                    │
│  - Evaluates policy             │
│  - Allows or denies request     │
└────┬────────────────────────────┘
     │
     │ 4. If allowed, invoke handler
     ▼
┌─────────────────────────────────┐
│  Lambda Handler                 │
│  - Process request              │
│  - Access DynamoDB              │
│  - Return response              │
└─────────────────────────────────┘
```

## Flow 3: AWS Console Access (IAM Identity Center)

```
┌──────────┐
│  User    │
└────┬─────┘
     │
     │ 1. Access AWS Console
     │    https://console.aws.amazon.com/
     ▼
┌─────────────────────────────────┐
│  AWS IAM Identity Center        │
│  - Detects no session           │
│  - Redirects to Azure AD         │
└────┬────────────────────────────┘
     │
     │ 2. SAML AuthnRequest
     │    Redirect to Azure
     ▼
┌─────────────────────────────────┐
│  Azure Entra ID                 │
│  - User authenticates            │
│  - MFA if required              │
│  - Generates SAML response       │
└────┬────────────────────────────┘
     │
     │ 3. POST SAML response
     │    To IAM Identity Center
     ▼
┌─────────────────────────────────┐
│  AWS IAM Identity Center        │
│  - Validates SAML response       │
│  - Maps groups to permission sets│
│  - Determines target account     │
└────┬────────────────────────────┘
     │
     │ 4. Assume role in target account
     │    Based on permission set
     ▼
┌─────────────────────────────────┐
│  Application Account            │
│  ┌──────────────────────────┐   │
│  │ Cross-Account Role        │   │
│  │ - Reviewer Role          │   │
│  │ - ReadOnly Role          │   │
│  │ - Admin Role             │   │
│  └──────────────────────────┘   │
└────┬────────────────────────────┘
     │
     │ 5. User has access
     ▼
┌─────────────────────────────────┐
│  AWS Console                    │
│  - User can access resources    │
│  - Based on role permissions    │
└─────────────────────────────────┘
```

## Flow 4: Multi-Account Role Assumption

```
┌─────────────────────────────────────────────────────────────┐
│                    MANAGEMENT ACCOUNT                       │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  IAM Identity Center                                 │   │
│  │  - User authenticated via Azure AD                   │   │
│  │  - Permission set: ReviewerAccess                    │   │
│  │  - Target: Application Account                        │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ AssumeRole
                            │ (with External ID)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    APPLICATION ACCOUNT                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Cross-Account Role                                   │   │
│  │  - Trust: Management Account                         │   │
│  │  - External ID: Required                             │   │
│  │  - Permissions: Reviewer (DynamoDB, Lambda)          │   │
│  └──────────────────────────────────────────────────────┘   │
│                            │                                 │
│                            │ Access Resources                │
│                            ▼                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  DynamoDB / Lambda                                   │   │
│  │  - Based on role permissions                         │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## JWT Token Validation Process

```
┌─────────────────────────────────────────────────────────────┐
│                    JWT AUTHORIZER                            │
│                                                              │
│  1. Extract Token                                            │
│     Authorization: Bearer <token>                            │
│                                                              │
│  2. Fetch JWKS                                               │
│     GET https://cognito-idp.region.amazonaws.com/            │
│         pool-id/.well-known/jwks.json                        │
│                                                              │
│  3. Decode Token Header                                      │
│     { "alg": "RS256", "kid": "abc123" }                      │
│                                                              │
│  4. Find Key in JWKS                                         │
│     Match kid from header to JWKS                            │
│                                                              │
│  5. Verify Signature                                         │
│     - Use public key from JWKS                              │
│     - Verify RS256 signature                                │
│                                                              │
│  6. Validate Claims                                          │
│     - exp: Not expired                                       │
│     - aud: Matches client ID                                 │
│     - iss: Matches Cognito issuer                            │
│                                                              │
│  7. Extract User Info                                        │
│     - sub: User ID                                           │
│     - email: User email                                     │
│     - cognito:groups: User groups                           │
│                                                              │
│  8. Check Permissions                                        │
│     - Determine required role from route                    │
│     - Check if user groups include role                    │
│                                                              │
│  9. Generate Policy                                          │
│     - Allow: If authorized                                   │
│     - Deny: If not authorized                                │
│     - Context: User info                                    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Role-Based Access Control Logic

```
┌─────────────────────────────────────────────────────────────┐
│                    PERMISSION CHECK                          │
│                                                              │
│  User Groups: [aws-reviewers]                                │
│  Required Role: reviewer                                     │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Check Hierarchy                                       │  │
│  │  1. Is user in 'admin' group?                         │  │
│  │     → YES: Allow (admin has all permissions)          │  │
│  │     → NO: Continue                                     │  │
│  │                                                         │  │
│  │  2. Required role is 'readonly'?                       │  │
│  │     → YES: Allow (all authenticated users)            │  │
│  │     → NO: Continue                                     │  │
│  │                                                         │  │
│  │  3. Required role is 'reviewer'?                       │  │
│  │     → Check if user in 'reviewer' or 'admin' group    │  │
│  │     → YES: Allow                                       │  │
│  │     → NO: Deny                                         │  │
│  │                                                         │  │
│  │  4. Required role is 'admin'?                         │  │
│  │     → Check if user in 'admin' group                  │  │
│  │     → YES: Allow                                       │  │
│  │     → NO: Deny                                         │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Trust Relationship Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    TRUST RELATIONSHIPS                      │
│                                                              │
│  Azure Entra ID                                              │
│    │                                                         │
│    │ Trusts                                                  │
│    ▼                                                         │
│  AWS IAM Identity Center                                     │
│    │                                                         │
│    │ Trusts (via SAML)                                       │
│    ▼                                                         │
│  Application Account Roles                                   │
│    │                                                         │
│    │ Trusts                                                  │
│    ▼                                                         │
│  Cognito User Pool                                           │
│    │                                                         │
│    │ Trusts (via SAML)                                       │
│    ▼                                                         │
│  Cognito Identity Pool                                       │
│    │                                                         │
│    │ Assumes                                                 │
│    ▼                                                         │
│  Cognito Authenticated Role                                  │
│    │                                                         │
│    │ Can invoke                                              │
│    ▼                                                         │
│  API Gateway                                                 │
│    │                                                         │
│    │ Validates via                                           │
│    ▼                                                         │
│  JWT Authorizer Lambda                                       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Error Flows

### Invalid Token Flow

```
Request with Invalid Token
    │
    ▼
JWT Authorizer
    │
    ├─ Token Expired
    │  └─> Deny Policy
    │      └─> 401 Unauthorized
    │
    ├─ Invalid Signature
    │  └─> Deny Policy
    │      └─> 401 Unauthorized
    │
    └─ Missing Token
       └─> Deny Policy
           └─> 401 Unauthorized
```

### Insufficient Permissions Flow

```
Request with Valid Token
    │
    ▼
JWT Authorizer
    │
    ├─ Token Valid
    │  └─> Extract Groups
    │      └─> Check Permissions
    │          │
    │          ├─ Has Required Role
    │          │  └─> Allow Policy
    │          │      └─> Request Proceeds
    │          │
    │          └─ Missing Required Role
    │             └─> Deny Policy
    │                 └─> 403 Forbidden
```

## Security Boundaries

```
┌─────────────────────────────────────────────────────────────┐
│                    SECURITY BOUNDARIES                      │
│                                                              │
│  External (Untrusted)                                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Internet                                             │  │
│  │  - Unauthenticated requests                          │  │
│  └──────────────────────────────────────────────────────┘  │
│                            │                                │
│                            │ HTTPS/TLS                     │
│                            ▼                                │
│  Authentication Layer (Semi-Trusted)                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Azure Entra ID                                      │  │
│  │  - User authentication                               │  │
│  │  - MFA verification                                  │  │
│  │  - Group membership                                   │  │
│  └──────────────────────────────────────────────────────┘  │
│                            │                                │
│                            │ SAML/JWT                       │
│                            ▼                                │
│  Authorization Layer (Trusted)                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  AWS IAM Identity Center / Cognito                    │  │
│  │  - Token validation                                   │  │
│  │  - Role mapping                                       │  │
│  │  - Permission assignment                              │  │
│  └──────────────────────────────────────────────────────┘  │
│                            │                                │
│                            │ IAM Policy                     │
│                            ▼                                │
│  Application Layer (Trusted)                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Lambda Functions                                     │  │
│  │  - Role-based access                                  │  │
│  │  - Resource access                                    │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

