# Enhanced WAF Rules for Production

# WAF Web ACL for API Gateway
resource "aws_wafv2_web_acl" "api_gateway" {
  name        = "${local.project_name}-api-gateway-waf-${var.environment}"
  description = "WAF for API Gateway"
  scope       = "REGIONAL"

  default_action {
    allow {}
  }

  # AWS Managed Rules - Core Rule Set
  rule {
    name     = "AWSManagedRulesCommonRuleSet"
    priority = 1

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesCommonRuleSet"
        vendor_name = "AWS"
      }
    }

    override_action {
      none {}
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                 = "CommonRuleSetMetric"
      sampled_requests_enabled    = true
    }
  }

  # AWS Managed Rules - Known Bad Inputs
  rule {
    name     = "AWSManagedRulesKnownBadInputsRuleSet"
    priority = 2

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesKnownBadInputsRuleSet"
        vendor_name = "AWS"
      }
    }

    override_action {
      none {}
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                 = "KnownBadInputsMetric"
      sampled_requests_enabled    = true
    }
  }

  # AWS Managed Rules - SQL Injection
  rule {
    name     = "AWSManagedRulesSQLiRuleSet"
    priority = 3

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesSQLiRuleSet"
        vendor_name = "AWS"
      }
    }

    override_action {
      none {}
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                 = "SQLiRuleSetMetric"
      sampled_requests_enabled    = true
    }
  }

  # AWS Managed Rules - Linux Operating System
  rule {
    name     = "AWSManagedRulesLinuxRuleSet"
    priority = 4

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesLinuxRuleSet"
        vendor_name = "AWS"
      }
    }

    override_action {
      none {}
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                 = "LinuxRuleSetMetric"
      sampled_requests_enabled    = true
    }
  }

  # Rate-based Rule - IP-based rate limiting
  rule {
    name     = "RateLimitRule"
    priority = 10

    statement {
      rate_based_statement {
        limit              = var.waf_rate_limit
        aggregate_key_type = "IP"
      }
    }

    action {
      block {}
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                 = "RateLimitMetric"
      sampled_requests_enabled    = true
    }
  }

  # Geo-blocking (optional)
  rule {
    name     = "GeoBlockRule"
    priority = 20

    statement {
      geo_match_statement {
        country_codes = var.blocked_countries
      }
    }

    action {
      block {}
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                 = "GeoBlockMetric"
      sampled_requests_enabled    = true
    }

    count = length(var.blocked_countries) > 0 ? 1 : 0
  }

  # IP Allow List (for trusted sources)
  rule {
    name     = "IPAllowList"
    priority = 30

    statement {
      ip_set_reference_statement {
        arn = aws_wafv2_ip_set.allow_list[0].arn
      }
    }

    action {
      allow {}
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                 = "IPAllowListMetric"
      sampled_requests_enabled    = true
    }

    count = length(var.allowed_ip_ranges) > 0 ? 1 : 0
  }

  # Custom Rule - JWT Token Validation
  rule {
    name     = "JWTTokenValidation"
    priority = 40

    statement {
      byte_match_statement {
        positional_constraint = "CONTAINS"
        search_string         = "Bearer "
        field_to_match {
          single_header {
            name = "authorization"
          }
        }
        text_transformation {
          priority = 0
          type     = "LOWERCASE"
        }
      }
    }

    action {
      allow {}
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                 = "JWTTokenValidationMetric"
      sampled_requests_enabled    = true
    }
  }

  # Custom Rule - Block requests without User-Agent
  rule {
    name     = "RequireUserAgent"
    priority = 50

    statement {
      size_constraint_statement {
        comparison_operator = "EQ"
        size                = 0
        field_to_match {
          single_header {
            name = "user-agent"
          }
        }
        text_transformation {
          priority = 0
          type     = "LOWERCASE"
        }
      }
    }

    action {
      block {}
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                 = "RequireUserAgentMetric"
      sampled_requests_enabled    = true
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                 = "${local.project_name}-waf-metric"
    sampled_requests_enabled    = true
  }

  tags = local.common_tags
}

# IP Set for Allow List
resource "aws_wafv2_ip_set" "allow_list" {
  count = length(var.allowed_ip_ranges) > 0 ? 1 : 0

  name        = "${local.project_name}-allow-list-${var.environment}"
  description = "IP addresses allowed to access API"
  scope       = "REGIONAL"
  ip_address_version = "IPV4"
  addresses         = var.allowed_ip_ranges

  tags = local.common_tags
}

# Associate WAF with API Gateway
resource "aws_wafv2_web_acl_association" "api_gateway" {
  resource_arn = aws_apigatewayv2_api.main.arn
  web_acl_arn  = aws_wafv2_web_acl.api_gateway.arn
}

# WAF Logging
resource "aws_wafv2_web_acl_logging_configuration" "api_gateway" {
  resource_arn            = aws_wafv2_web_acl.api_gateway.arn
  log_destination_configs = [aws_cloudwatch_log_group.waf.arn]
}

resource "aws_cloudwatch_log_group" "waf" {
  name              = "/aws/waf/${local.project_name}-${var.environment}"
  retention_in_days = var.log_retention_days

  tags = local.common_tags
}

