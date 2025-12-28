terraform {
  required_version = ">= 1.5.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  backend "s3" {
    # Backend configuration should be provided via backend.hcl
    # See backend.hcl.example for template
    # Initialize with: terraform init -backend-config=backend.hcl
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "Terraform-Spacelift-AI-Reviewer"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

locals {
  project_name = "terraform-spacelift-ai-reviewer"
  common_tags = {
    Project     = local.project_name
    Environment = var.environment
  }
}

