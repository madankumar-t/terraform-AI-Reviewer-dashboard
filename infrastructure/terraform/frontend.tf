# Frontend Infrastructure - CloudFront + S3

module "frontend" {
  source = "./modules/frontend"

  name       = "${local.project_name}-${var.environment}"
  bucket_name = "${local.project_name}-frontend-${var.environment}-${data.aws_caller_identity.current.account_id}"

  use_custom_domain = var.frontend_custom_domain != ""
  custom_domains    = var.frontend_custom_domain != "" ? [var.frontend_custom_domain] : []
  acm_certificate_arn = var.frontend_acm_certificate_arn

  enable_waf = var.enable_frontend_waf
  price_class = var.cloudfront_price_class

  tags = local.common_tags
}

data "aws_caller_identity" "current" {}

