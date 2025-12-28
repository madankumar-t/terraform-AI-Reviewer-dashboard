# Azure Entra ID SSO Setup Guide

## Step-by-Step Configuration

### Part 1: Configure Azure Entra ID

#### 1.1 Create Enterprise Application

1. Go to Azure Portal → Azure Active Directory → Enterprise Applications
2. Click "New application" → "Create your own application"
3. Name: "Terraform AI Reviewer"
4. Select "Integrate any other application you don't find in the gallery"

#### 1.2 Configure SAML SSO

1. In the application, go to "Single sign-on" → "SAML"
2. **Basic SAML Configuration**:
   - Identifier (Entity ID): `urn:amazon:cognito:sp:${COGNITO_USER_POOL_ID}`
   - Reply URL (Assertion Consumer Service URL): 
     `https://${COGNITO_DOMAIN}.auth.${REGION}.amazoncognito.com/saml2/idpresponse`
   - Sign-on URL: `https://${COGNITO_DOMAIN}.auth.${REGION}.amazoncognito.com`

3. **User Attributes & Claims**:
   - Add claim: `email` → `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress`
   - Add claim: `groups` → `http://schemas.microsoft.com/ws/2008/06/identity/claims/groups`

4. **SAML Signing Certificate**:
   - Download certificate (Base64)
   - Note the certificate thumbprint

#### 1.3 Create Security Groups

1. Go to Azure AD → Groups → New group
2. Create groups:
   - `aws-admins` (Type: Security)
   - `aws-reviewers` (Type: Security)
   - `aws-readonly` (Type: Security)

3. Assign users to groups

#### 1.4 Get SAML Metadata

1. In SAML configuration, click "SAML Signing Certificate"
2. Download "Federation Metadata XML"
3. Save for Terraform configuration

### Part 2: Configure AWS IAM Identity Center

#### 2.1 Enable IAM Identity Center

1. Go to AWS Console → IAM Identity Center
2. Enable IAM Identity Center (if not already enabled)
3. Note the instance ARN

#### 2.2 Configure External Identity Provider

1. Go to Settings → Identity source → Change identity source
2. Select "External identity provider"
3. Upload Azure AD SAML metadata XML
4. Configure attribute mapping:
   - `NameID` → `${user:name}`
   - `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress` → `${user:email}`
   - `http://schemas.microsoft.com/ws/2008/06/identity/claims/groups` → `${user:groups}`

5. Save configuration

#### 2.3 Create Permission Sets

**AdminAccess**:
- Attach managed policy: `AdministratorAccess`

**ReviewerAccess** (Custom):
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
        "dynamodb:UpdateItem",
        "lambda:InvokeFunction"
      ],
      "Resource": "*"
    }
  ]
}
```

**ReadOnlyAccess**:
- Attach managed policy: `ReadOnlyAccess`

#### 2.4 Assign Groups to Accounts

1. Go to AWS accounts → Select account
2. Go to "Users and groups" tab
3. Click "Assign users or groups"
4. Select Azure AD group
5. Select permission set
6. Review and assign

### Part 3: Configure Amazon Cognito

#### 3.1 Create User Pool

1. Go to Cognito → User pools → Create user pool
2. Configure:
   - Sign-in options: Email
   - Password policy: Strong
   - MFA: Optional

#### 3.2 Add Azure AD as Identity Provider

1. Go to User pool → Sign-in experience → Federated identity provider sign-in
2. Add identity provider → SAML
3. Upload Azure AD SAML metadata XML
4. Configure attribute mapping:
   - `email` → `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress`
   - `groups` → `http://schemas.microsoft.com/ws/2008/06/identity/claims/groups`

5. Save

#### 3.3 Create User Pool Client

1. Go to User pool → App integration → App clients
2. Create app client:
   - Name: "Frontend Client"
   - Generate client secret: No (public client)
   - Allowed OAuth flows: Authorization code grant, Implicit grant
   - Allowed OAuth scopes: email, openid, profile
   - Callback URLs: `http://localhost:3000/auth/callback`
   - Sign-out URLs: `http://localhost:3000`

#### 3.4 Create Identity Pool

1. Go to Cognito → Identity pools → Create identity pool
2. Configure:
   - Identity pool name: "terraform-ai-reviewer-identity-pool"
   - Authentication providers: Cognito user pool
   - User pool ID: Select your user pool
   - App client ID: Select your app client

3. Create IAM roles:
   - Authenticated role: Custom role with API Gateway access
   - Unauthenticated role: None (disabled)

#### 3.5 Configure Domain

1. Go to User pool → App integration → Domain
2. Create domain: `terraform-ai-reviewer-${environment}`
3. Note the domain URL

### Part 4: Deploy Terraform

#### 4.1 Update Variables

```hcl
# terraform.tfvars
azure_admin_group_id = "azure-group-object-id-for-admins"
azure_reviewer_group_id = "azure-group-object-id-for-reviewers"
azure_readonly_group_id = "azure-group-object-id-for-readonly"
azure_entra_metadata_xml = "<xml>...</xml>"  # From Azure AD
application_account_id = "123456789012"
management_account_id = "987654321098"
cross_account_external_id = "unique-external-id"
cognito_callback_urls = ["https://yourdomain.com/auth/callback"]
cognito_logout_urls = ["https://yourdomain.com"]
```

#### 4.2 Deploy

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

### Part 5: Configure Frontend

#### 5.1 Update Environment Variables

```bash
# .env.local
NEXT_PUBLIC_COGNITO_USER_POOL_ID=us-east-1_XXXXXXXXX
NEXT_PUBLIC_COGNITO_CLIENT_ID=xxxxxxxxxxxxxxxxxx
NEXT_PUBLIC_COGNITO_DOMAIN=terraform-ai-reviewer-prod
NEXT_PUBLIC_AWS_REGION=us-east-1
NEXT_PUBLIC_API_URL=https://your-api-gateway-url.execute-api.us-east-1.amazonaws.com
```

#### 5.2 Install Dependencies

```bash
npm install
```

#### 5.3 Test Authentication

1. Start dev server: `npm run dev`
2. Navigate to `/auth/login`
3. Click "Sign in with Azure AD"
4. Complete Azure AD authentication
5. Verify callback and token storage

## Verification Checklist

### Azure Entra ID
- [ ] Enterprise application created
- [ ] SAML SSO configured
- [ ] User attributes mapped
- [ ] Security groups created
- [ ] Users assigned to groups
- [ ] SAML metadata downloaded

### AWS IAM Identity Center
- [ ] IAM Identity Center enabled
- [ ] External identity provider configured
- [ ] Attribute mapping configured
- [ ] Permission sets created
- [ ] Groups assigned to accounts

### Amazon Cognito
- [ ] User pool created
- [ ] Azure AD added as SAML provider
- [ ] User pool client created
- [ ] Identity pool created
- [ ] Domain configured
- [ ] IAM roles created

### Terraform
- [ ] All resources deployed
- [ ] JWT authorizer created
- [ ] API Gateway routes configured
- [ ] Cross-account roles created

### Frontend
- [ ] Environment variables set
- [ ] Dependencies installed
- [ ] Authentication flow works
- [ ] Token storage working
- [ ] API calls include JWT

## Troubleshooting

### Issue: "Invalid signature" in JWT authorizer

**Solution**:
- Verify JWKS URL is correct
- Check Cognito user pool ID
- Ensure token is not expired

### Issue: "Access denied" in API Gateway

**Solution**:
- Check user groups in token
- Verify required role for route
- Check JWT authorizer logs

### Issue: Azure AD sign-in redirects but doesn't complete

**Solution**:
- Verify callback URL in Cognito
- Check SAML reply URL in Azure AD
- Verify attribute mapping

### Issue: Cross-account role assumption fails

**Solution**:
- Verify external ID matches
- Check trust policy
- Verify IAM Identity Center assignment
- Check CloudTrail logs

## Security Considerations

1. **External ID**: Use strong, unique external IDs
2. **Token Storage**: Use httpOnly cookies in production
3. **HTTPS**: Always use HTTPS for authentication
4. **MFA**: Enable MFA in both Azure AD and Cognito
5. **Token Expiration**: Set appropriate token lifetimes
6. **Audit Logging**: Monitor all authentication events

## Next Steps

1. Test end-to-end authentication flow
2. Verify role-based access control
3. Test cross-account access
4. Set up monitoring and alerts
5. Document procedures for team

