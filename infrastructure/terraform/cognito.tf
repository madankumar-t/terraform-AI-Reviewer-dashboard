# Amazon Cognito User Pool for Frontend Authentication

resource "aws_cognito_user_pool" "main" {
  name = "${local.project_name}-user-pool-${var.environment}"

  # Password policy
  password_policy {
    minimum_length    = 12
    require_lowercase = true
    require_uppercase = true
    require_numbers   = true
    require_symbols   = true
  }

  # MFA configuration
  mfa_configuration = "OPTIONAL"

  software_token_mfa_configuration {
    enabled = true
  }

  # Account recovery
  account_recovery_setting {
    recovery_mechanism {
      name     = "verified_email"
      priority = 1
    }
  }

  # User pool attributes
  schema {
    name                = "email"
    attribute_data_type = "String"
    mutable             = true
    required            = true
  }

  schema {
    name                = "groups"
    attribute_data_type = "String"
    mutable             = true
    required            = false
  }

  # Identity provider - Azure Entra ID
  saml_provider {
    metadata_document = var.azure_entra_metadata_xml
  }

  tags = local.common_tags
}

# Cognito User Pool Client (for frontend)
resource "aws_cognito_user_pool_client" "frontend" {
  name         = "${local.project_name}-frontend-client-${var.environment}"
  user_pool_id = aws_cognito_user_pool.main.id

  generate_secret = false  # Public client for frontend

  # OAuth settings
  allowed_oauth_flows                  = ["code", "implicit"]
  allowed_oauth_scopes                 = ["email", "openid", "profile"]
  allowed_oauth_flows_user_pool_client = true

  # Callback URLs
  callback_urls = var.cognito_callback_urls
  logout_urls   = var.cognito_logout_urls

  # Token validity
  id_token_validity      = 60  # minutes
  access_token_validity  = 60  # minutes
  refresh_token_validity = 30  # days

  # Prevent user existence errors
  prevent_user_existence_errors = "ENABLED"

  # Supported identity providers
  supported_identity_providers = ["AzureAD"]
}

# Cognito Identity Pool (for AWS resource access)
resource "aws_cognito_identity_pool" "main" {
  identity_pool_name               = "${local.project_name}-identity-pool-${var.environment}"
  allow_unauthenticated_identities = false

  cognito_identity_providers {
    client_id               = aws_cognito_user_pool_client.frontend.id
    provider_name           = aws_cognito_user_pool.main.endpoint
    server_side_token_check = true
  }

  tags = local.common_tags
}

# IAM Role for Authenticated Users
resource "aws_iam_role" "cognito_authenticated" {
  name = "${local.project_name}-cognito-authenticated-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = "cognito-identity.amazonaws.com"
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "cognito-identity.amazonaws.com:aud" = aws_cognito_identity_pool.main.id
          }
          "ForAnyValue:StringLike" = {
            "cognito-identity.amazonaws.com:amr" = "authenticated"
          }
        }
      }
    ]
  })

  tags = local.common_tags
}

# IAM Policy for Authenticated Users
resource "aws_iam_role_policy" "cognito_authenticated" {
  name = "${local.project_name}-cognito-authenticated-policy-${var.environment}"
  role = aws_iam_role.cognito_authenticated.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "execute-api:Invoke"
        ]
        Resource = [
          "${aws_apigatewayv2_api.main.execution_arn}/*/*"
        ]
      }
    ]
  })
}

# Attach role to identity pool
resource "aws_cognito_identity_pool_roles_attachment" "main" {
  identity_pool_id = aws_cognito_identity_pool.main.id

  roles = {
    "authenticated" = aws_iam_role.cognito_authenticated.arn
  }
}

# Cognito Domain
resource "aws_cognito_user_pool_domain" "main" {
  domain       = "${local.project_name}-${var.environment}"
  user_pool_id = aws_cognito_user_pool.main.id
}

