variable "name" {
  description = "Name prefix for resources"
  type        = string
}

variable "bucket_name" {
  description = "S3 bucket name for frontend assets"
  type        = string
}

variable "price_class" {
  description = "CloudFront price class"
  type        = string
  default     = "PriceClass_100"
}

variable "use_custom_domain" {
  description = "Use custom domain for CloudFront"
  type        = bool
  default     = false
}

variable "custom_domains" {
  description = "Custom domain names for CloudFront"
  type        = list(string)
  default     = []
}

variable "acm_certificate_arn" {
  description = "ACM certificate ARN for custom domain"
  type        = string
  default     = ""
}

variable "enable_waf" {
  description = "Enable WAF for CloudFront"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}

