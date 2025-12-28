# SOC2 Control Mapping

## Overview

This document maps SOC2 Trust Service Criteria (TSC) controls to implementation evidence in the Terraform + Spacelift AI Reviewer platform.

## Common Criteria (CC) Series

### CC2 - Communication and Information

**Control**: The entity obtains or generates and uses relevant, quality information to support the functioning of internal control.

**Implementation Evidence**:
- ✅ Structured logging in all Lambda functions (`lambda/logger.py`)
- ✅ CloudWatch Logs for all services
- ✅ API Gateway access logs
- ✅ DynamoDB audit trail (versioned records)
- ✅ Review metadata stored with each review

**Evidence Location**:
- CloudWatch Log Groups: `/aws/lambda/*`
- DynamoDB Table: `reviews` (all versions)
- CloudWatch Logs: `/aws/apigateway/*`

**Automated Evidence**:
- Daily log aggregation reports
- Review metadata exports
- API usage statistics

### CC4 - Monitoring Activities

**Control**: The entity selects, develops, and performs ongoing and/or separate evaluations to ascertain whether the components of internal control are present and functioning.

**Implementation Evidence**:
- ✅ CloudWatch Alarms for errors and performance
- ✅ CloudWatch Dashboard for real-time monitoring
- ✅ SNS notifications for critical events
- ✅ Automated health checks
- ✅ Performance metrics collection

**Evidence Location**:
- CloudWatch Dashboard: `terraform-spacelift-ai-reviewer-dashboard`
- CloudWatch Alarms: `terraform-spacelift-ai-reviewer-*-errors`
- SNS Topic: `terraform-spacelift-ai-reviewer-alerts`

**Automated Evidence**:
- Weekly monitoring reports
- Alarm trigger logs
- Dashboard snapshots

### CC6 - Logical and Physical Access

**Control**: The entity restricts logical and physical access to information assets, protected functions, and protected facilities.

**Implementation Evidence**:
- ✅ IAM roles with least privilege
- ✅ JWT authorization at API Gateway
- ✅ Azure Entra ID SSO integration
- ✅ Role-based access control (Admin, Reviewer, ReadOnly)
- ✅ Security groups for network isolation
- ✅ VPC isolation for Lambda functions
- ✅ Secrets in AWS Secrets Manager

**Evidence Location**:
- IAM Roles: `terraform-spacelift-ai-reviewer-*`
- IAM Policies: Attached to roles
- CloudTrail: All API calls logged
- Cognito: User access logs
- IAM Identity Center: SSO access logs

**Automated Evidence**:
- Monthly access review reports
- IAM policy audit
- Security group reviews
- Failed access attempt logs

### CC7 - System Operations

**Control**: The entity uses detection and monitoring procedures to identify (1) changes to configurations that result in the introduction of new vulnerabilities, and (2) susceptibilities to newly discovered vulnerabilities.

**Implementation Evidence**:
- ✅ Infrastructure as Code (Terraform)
- ✅ Version control (Git)
- ✅ Change management process
- ✅ Automated deployments
- ✅ Configuration drift detection
- ✅ Security patch management

**Evidence Location**:
- Terraform State: S3 bucket (versioned)
- Git Repository: All changes tracked
- CloudWatch Events: Deployment events
- AWS Config: Configuration compliance

**Automated Evidence**:
- Change logs from Git
- Terraform plan outputs
- Deployment history
- Configuration compliance reports

## Availability (A) Series

### A1.1 - System Availability

**Control**: The entity maintains, monitors, and evaluates current processing capacity and use of systems (infrastructure, data, and software) to manage capacity demand and to enable the implementation of additional capacity to help meet its objectives.

**Implementation Evidence**:
- ✅ Auto-scaling for DynamoDB (on-demand)
- ✅ Lambda concurrency limits
- ✅ CloudWatch metrics for capacity
- ✅ Performance monitoring

**Evidence Location**:
- CloudWatch Metrics: `AWS/Lambda`, `AWS/DynamoDB`
- DynamoDB Metrics: Read/Write capacity

**Automated Evidence**:
- Monthly capacity reports
- Performance trend analysis

## Processing Integrity (PI) Series

### PI1.1 - Processing Integrity

**Control**: The entity implements policies and procedures over system inputs, including controls over completeness and accuracy, to help meet the entity's objectives.

**Implementation Evidence**:
- ✅ Input validation in Lambda functions
- ✅ Pydantic models for data validation
- ✅ Webhook signature verification
- ✅ JWT token validation
- ✅ Terraform code validation

**Evidence Location**:
- Lambda function code: Input validation logic
- CloudWatch Logs: Validation errors
- API Gateway: Request validation

**Automated Evidence**:
- Input validation error reports
- Webhook verification logs

## Confidentiality (C) Series

### C1.1 - Confidentiality

**Control**: The entity identifies and maintains confidential information to meet the entity's objectives related to confidentiality.

**Implementation Evidence**:
- ✅ Encryption at rest (DynamoDB, S3, CloudWatch)
- ✅ Encryption in transit (HTTPS, TLS)
- ✅ Secrets in AWS Secrets Manager
- ✅ VPC isolation
- ✅ Private endpoints

**Evidence Location**:
- DynamoDB: Encryption configuration
- S3: Encryption configuration
- Secrets Manager: Secret encryption
- VPC: Private endpoint configuration

**Automated Evidence**:
- Encryption status reports
- Secret rotation logs
- Network security reviews

## Privacy (P) Series

### P1.1 - Privacy

**Control**: The entity collects, uses, retains, discloses, and disposes of personal information in conformity with the commitments in the entity's privacy notice and with criteria set forth in generally accepted privacy principles.

**Implementation Evidence**:
- ✅ User data in Cognito (encrypted)
- ✅ Audit logs for data access
- ✅ Data retention policies
- ✅ Access controls

**Evidence Location**:
- Cognito: User data storage
- CloudWatch Logs: Access logs
- DynamoDB: Data retention

**Automated Evidence**:
- Data access reports
- Retention compliance reports

## Evidence Collection Schedule

| Evidence Type | Frequency | Automation |
|--------------|----------|------------|
| Access Reviews | Monthly | Automated |
| Log Aggregation | Daily | Automated |
| Monitoring Reports | Weekly | Automated |
| Configuration Compliance | Weekly | Automated |
| Capacity Reports | Monthly | Automated |
| Security Reviews | Quarterly | Manual + Automated |

