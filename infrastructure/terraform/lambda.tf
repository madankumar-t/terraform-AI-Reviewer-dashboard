data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../lambda"
  output_path = "${path.module}/lambda-deployment.zip"
  excludes    = ["__pycache__", "*.pyc", ".pytest_cache"]
}

resource "aws_lambda_function" "api_handler" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = "${local.project_name}-api-${var.environment}"
  role             = aws_iam_role.lambda_execution_role.arn
  handler          = "api_handler.handler"
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  runtime          = "python3.11"
  timeout          = 30
  memory_size      = 512

  vpc_config {
    subnet_ids         = module.vpc.private_subnet_ids
    security_group_ids = [aws_security_group.lambda.id]
  }

  environment {
    variables = {
      DYNAMODB_TABLE_NAME = aws_dynamodb_table.reviews.name
      ENVIRONMENT         = var.environment
      OPENAI_SECRET_NAME  = aws_secretsmanager_secret.openai_api_key.name
      ANTHROPIC_SECRET_NAME = aws_secretsmanager_secret.anthropic_api_key.name
      SPACELIFT_SECRET_NAME = aws_secretsmanager_secret.spacelift_webhook_secret.name
    }
  }

  tags = local.common_tags
}

resource "aws_lambda_function" "ai_reviewer" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = "${local.project_name}-ai-reviewer-${var.environment}"
  role             = aws_iam_role.lambda_execution_role.arn
  handler          = "ai_reviewer.handler"
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  runtime          = "python3.11"
  timeout          = 300
  memory_size      = 2048

  vpc_config {
    subnet_ids         = module.vpc.private_subnet_ids
    security_group_ids = [aws_security_group.lambda.id]
  }

  environment {
    variables = {
      DYNAMODB_TABLE_NAME = aws_dynamodb_table.reviews.name
      ENVIRONMENT         = var.environment
      OPENAI_SECRET_NAME  = aws_secretsmanager_secret.openai_api_key.name
      ANTHROPIC_SECRET_NAME = aws_secretsmanager_secret.anthropic_api_key.name
      AWS_REGION          = var.aws_region
    }
  }

  tags = local.common_tags
}

resource "aws_lambda_function" "webhook_handler" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = "${local.project_name}-webhook-${var.environment}"
  role             = aws_iam_role.lambda_execution_role.arn
  handler          = "webhook_handler.handler"
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  runtime          = "python3.11"
  timeout          = 30
  memory_size      = 512

  environment {
    variables = {
      DYNAMODB_TABLE_NAME = aws_dynamodb_table.reviews.name
      ENVIRONMENT         = var.environment
      AI_REVIEWER_FUNCTION_NAME = aws_lambda_function.ai_reviewer.function_name
      SPACELIFT_SECRET_NAME = aws_secretsmanager_secret.spacelift_webhook_secret.name
    }
  }

  tags = local.common_tags
}

resource "aws_lambda_function" "pr_review_handler" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = "${local.project_name}-pr-review-${var.environment}"
  role             = aws_iam_role.lambda_execution_role.arn
  handler          = "pr_review_handler.handler"
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  runtime          = "python3.11"
  timeout          = 30
  memory_size      = 512

  environment {
    variables = {
      DYNAMODB_TABLE_NAME = aws_dynamodb_table.reviews.name
      ENVIRONMENT         = var.environment
      AI_REVIEWER_FUNCTION_NAME = aws_lambda_function.ai_reviewer.function_name
      BEDROCK_REGION     = var.aws_region
    }
  }

  tags = local.common_tags
}

resource "aws_lambda_function" "github_webhook_handler" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = "${local.project_name}-github-webhook-${var.environment}"
  role             = aws_iam_role.lambda_execution_role.arn
  handler          = "github_webhook_handler.handler"
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  runtime          = "python3.11"
  timeout          = 30
  memory_size      = 512

  environment {
    variables = {
      DYNAMODB_TABLE_NAME = aws_dynamodb_table.reviews.name
      ENVIRONMENT         = var.environment
      GITHUB_WEBHOOK_SECRET_NAME = aws_secretsmanager_secret.github_webhook_secret.name
      PR_REVIEW_FUNCTION_NAME = aws_lambda_function.pr_review_handler.function_name
    }
  }

  tags = local.common_tags
}

resource "aws_lambda_function" "historical_analysis_handler" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = "${local.project_name}-historical-analysis-${var.environment}"
  role             = aws_iam_role.lambda_execution_role.arn
  handler          = "historical_analysis_handler.handler"
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  runtime          = "python3.11"
  timeout          = 60
  memory_size      = 1024

  environment {
    variables = {
      DYNAMODB_TABLE_NAME = aws_dynamodb_table.reviews.name
      ENVIRONMENT         = var.environment
    }
  }

  tags = local.common_tags
}

resource "aws_lambda_function" "trend_aggregation_handler" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = "${local.project_name}-trend-aggregation-${var.environment}"
  role             = aws_iam_role.lambda_execution_role.arn
  handler          = "trend_aggregation_handler.handler"
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  runtime          = "python3.11"
  timeout          = 300
  memory_size      = 1024

  environment {
    variables = {
      DYNAMODB_TABLE_NAME = aws_dynamodb_table.reviews.name
      ENVIRONMENT         = var.environment
    }
  }

  tags = local.common_tags
}

resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api_handler.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}

resource "aws_lambda_permission" "webhook_api_gateway" {
  statement_id  = "AllowExecutionFromAPIGatewayWebhook"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.webhook_handler.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}

resource "aws_lambda_permission" "pr_review_api_gateway" {
  statement_id  = "AllowExecutionFromAPIGatewayPRReview"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.pr_review_handler.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}

resource "aws_lambda_permission" "github_webhook_api_gateway" {
  statement_id  = "AllowExecutionFromAPIGatewayGitHub"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.github_webhook_handler.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}

resource "aws_lambda_permission" "historical_analysis_api_gateway" {
  statement_id  = "AllowExecutionFromAPIGatewayHistorical"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.historical_analysis_handler.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/*/*"
}

resource "aws_lambda_permission" "trend_aggregation_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.trend_aggregation_handler.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.trend_aggregation_schedule.arn
}

resource "aws_lambda_function" "jwt_authorizer" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = "${local.project_name}-jwt-authorizer-${var.environment}"
  role             = aws_iam_role.lambda_execution_role.arn
  handler          = "jwt_authorizer.handler"
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  runtime          = "python3.11"
  timeout          = 5
  memory_size      = 256

  environment {
    variables = {
      COGNITO_USER_POOL_ID = aws_cognito_user_pool.main.id
      COGNITO_CLIENT_ID    = aws_cognito_user_pool_client.frontend.id
      AWS_REGION           = var.aws_region
      ENVIRONMENT          = var.environment
    }
  }

  tags = local.common_tags
}

resource "aws_lambda_permission" "jwt_authorizer_api_gateway" {
  statement_id  = "AllowExecutionFromAPIGatewayJWT"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.jwt_authorizer.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.main.execution_arn}/authorizers/*"
}

resource "aws_lambda_permission" "ai_reviewer_invoke" {
  statement_id  = "AllowExecutionFromWebhook"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ai_reviewer.function_name
  principal     = "lambda.amazonaws.com"
  source_arn    = aws_lambda_function.webhook_handler.arn
}

