# Security Groups for Lambda Functions

resource "aws_security_group" "lambda" {
  name        = "${local.project_name}-lambda-${var.environment}"
  description = "Security group for Lambda functions"
  vpc_id      = module.vpc.vpc_id

  egress {
    description = "HTTPS to AWS services"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "HTTPS to DynamoDB"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [module.vpc.vpc_cidr]
  }

  egress {
    description = "HTTPS to Bedrock"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [module.vpc.vpc_cidr]
  }

  tags = merge(
    local.common_tags,
    {
      Name = "${local.project_name}-lambda-sg-${var.environment}"
    }
  )
}

