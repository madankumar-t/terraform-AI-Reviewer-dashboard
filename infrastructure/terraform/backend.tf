# Remote State Configuration
# Initialize with: terraform init -backend-config=backend.hcl

terraform {
  backend "s3" {
    # These values should be provided via backend.hcl or -backend-config
    # bucket         = "terraform-state-account-id-region"
    # key            = "terraform-spacelift-ai-reviewer/terraform.tfstate"
    # region         = "us-east-1"
    # dynamodb_table = "terraform-state-lock"
    # encrypt        = true
    # kms_key_id     = "arn:aws:kms:region:account-id:key/key-id"
  }
}

