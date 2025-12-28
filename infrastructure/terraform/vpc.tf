# VPC Configuration for Application Account

module "vpc" {
  source = "./modules/vpc"

  name                 = "${local.project_name}-${var.environment}"
  vpc_cidr             = var.vpc_cidr
  public_subnet_cidrs  = var.public_subnet_cidrs
  private_subnet_cidrs = var.private_subnet_cidrs
  enable_nat_gateway   = true
  enable_flow_logs     = true
  flow_log_retention_days = 30

  tags = local.common_tags
}

# VPC Endpoint for Bedrock (Private)
resource "aws_vpc_endpoint" "bedrock" {
  vpc_id              = module.vpc.vpc_id
  service_name        = "com.amazonaws.${var.aws_region}.bedrock-runtime"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = module.vpc.private_subnet_ids
  security_group_ids  = [aws_security_group.bedrock_endpoint.id]
  private_dns_enabled = true

  tags = merge(
    local.common_tags,
    {
      Name = "${local.project_name}-bedrock-endpoint-${var.environment}"
    }
  )
}

# Security Group for Bedrock Endpoint
resource "aws_security_group" "bedrock_endpoint" {
  name        = "${local.project_name}-bedrock-endpoint-${var.environment}"
  description = "Security group for Bedrock VPC endpoint"
  vpc_id      = module.vpc.vpc_id

  ingress {
    description     = "HTTPS from VPC"
    from_port       = 443
    to_port         = 443
    protocol        = "tcp"
    cidr_blocks     = [module.vpc.vpc_cidr]
  }

  egress {
    description = "All outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(
    local.common_tags,
    {
      Name = "${local.project_name}-bedrock-endpoint-sg-${var.environment}"
    }
  )
}

