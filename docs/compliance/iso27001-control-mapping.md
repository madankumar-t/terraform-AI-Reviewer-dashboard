# ISO 27001 Control Mapping

## Overview

This document maps ISO 27001:2022 Annex A controls to implementation evidence in the Terraform + Spacelift AI Reviewer platform.

## A.5 - Information Security Policies

### A.5.1 - Policies for Information Security

**Control**: A set of policies for information security shall be defined, approved by management, published, communicated to and acknowledged by relevant personnel, and reviewed and updated on a regular basis.

**Implementation Evidence**:
- ✅ Security policies documented
- ✅ IAM policies defined
- ✅ Security group rules documented
- ✅ Access control policies

**Evidence Location**:
- Documentation: `docs/platform-architecture.md`
- IAM Policies: Terraform code
- Security Groups: Terraform code

## A.7 - Human Resource Security

### A.7.2 - During Employment

**Control**: Management shall require all personnel to apply information security in accordance with the established policies and procedures of the organization.

**Implementation Evidence**:
- ✅ Azure Entra ID user management
- ✅ Role-based access control
- ✅ Access reviews
- ✅ Training records (external)

**Evidence Location**:
- Azure AD: User assignments
- IAM Identity Center: Permission sets
- Cognito: User pool

## A.8 - Asset Management

### A.8.1 - Inventory of Information Assets

**Control**: An inventory of information and other associated assets, including owners, shall be developed and maintained.

**Implementation Evidence**:
- ✅ AWS Resource inventory (Terraform state)
- ✅ Asset tagging strategy
- ✅ Resource ownership documented

**Evidence Location**:
- Terraform State: All resources
- AWS Resource Groups: Tagged resources
- Documentation: Resource inventory

### A.8.2 - Ownership of Information Assets

**Control**: Assets maintained in the inventory shall be owned by designated owners.

**Implementation Evidence**:
- ✅ Resource tags with owner information
- ✅ IAM role ownership
- ✅ Documentation of ownership

**Evidence Location**:
- Terraform: Resource tags
- AWS Console: Resource tags
- Documentation: Ownership matrix

## A.9 - Access Control

### A.9.1 - Business Requirements of Access Control

**Control**: Access to information and other associated assets shall be based on business and security requirements.

**Implementation Evidence**:
- ✅ Role-based access control (Admin, Reviewer, ReadOnly)
- ✅ IAM policies aligned with business needs
- ✅ Access control matrix

**Evidence Location**:
- IAM Roles: `terraform-spacelift-ai-reviewer-*`
- Documentation: `docs/azure-entra-sso.md`
- Access Control Matrix: This document

### A.9.2 - User Access Management

**Control**: The allocation and use of privileged access rights shall be restricted and controlled.

**Implementation Evidence**:
- ✅ Azure Entra ID user provisioning
- ✅ IAM Identity Center permission sets
- ✅ Least privilege IAM roles
- ✅ Access reviews

**Evidence Location**:
- Azure AD: User groups
- IAM Identity Center: Permission assignments
- CloudTrail: Access logs

### A.9.4 - Access Control to Network and Network Services

**Control**: Users and systems shall only be provided access to the network and network services that they have been specifically authorized to use.

**Implementation Evidence**:
- ✅ VPC isolation
- ✅ Security groups
- ✅ Network ACLs
- ✅ Private endpoints

**Evidence Location**:
- VPC: `terraform/vpc.tf`
- Security Groups: `terraform/security_groups.tf`
- VPC Endpoints: `terraform/vpc.tf`

## A.10 - Cryptography

### A.10.1 - Cryptographic Controls

**Control**: Cryptographic controls shall be used in accordance with all relevant agreements, legislation, and regulations.

**Implementation Evidence**:
- ✅ Encryption at rest (AES-256)
- ✅ Encryption in transit (TLS 1.2+)
- ✅ KMS key management
- ✅ Certificate management

**Evidence Location**:
- DynamoDB: Encryption configuration
- S3: Encryption configuration
- API Gateway: TLS configuration
- CloudFront: TLS configuration

## A.12 - Operations Security

### A.12.1 - Operational Procedures and Responsibilities

**Control**: Operating procedures shall be documented, maintained, and made available to all personnel who need them.

**Implementation Evidence**:
- ✅ Deployment procedures
- ✅ Runbooks
- ✅ Incident response procedures
- ✅ Change management procedures

**Evidence Location**:
- Documentation: `DEPLOYMENT.md`
- Runbooks: `docs/runbooks/`
- Change logs: Git history

### A.12.2 - Protection from Malware

**Control**: Detection, prevention, and recovery controls to protect against malware shall be implemented.

**Implementation Evidence**:
- ✅ WAF protection (CloudFront)
- ✅ Input validation
- ✅ Code scanning (external)
- ✅ Dependency scanning (external)

**Evidence Location**:
- WAF: `terraform/modules/frontend/main.tf`
- Input Validation: Lambda function code
- Security scanning: External tools

### A.12.4 - Logging and Monitoring

**Control**: Event logs recording user activities, exceptions, faults, and information security events shall be produced, kept, and regularly reviewed.

**Implementation Evidence**:
- ✅ CloudWatch Logs for all services
- ✅ VPC Flow Logs
- ✅ CloudTrail for API calls
- ✅ Application logs
- ✅ Log retention policies

**Evidence Location**:
- CloudWatch Log Groups: `/aws/lambda/*`, `/aws/apigateway/*`
- VPC Flow Logs: `/aws/vpc/*`
- CloudTrail: AWS CloudTrail logs

### A.12.6 - Management of Technical Vulnerabilities

**Control**: Information about technical vulnerabilities of information systems being used shall be obtained in a timely fashion, the organization's exposure to such vulnerabilities evaluated, and appropriate measures taken to address the associated risk.

**Implementation Evidence**:
- ✅ Dependency updates
- ✅ Security patch management
- ✅ Vulnerability scanning (external)
- ✅ Security advisories monitoring

**Evidence Location**:
- Dependency files: `package.json`, `requirements.txt`
- Security patches: Git history
- Vulnerability reports: External tools

## A.14 - System Acquisition, Development, and Maintenance

### A.14.2 - Security in Development and Support Processes

**Control**: Rules for the development of software and systems shall be established and applied.

**Implementation Evidence**:
- ✅ Code review process
- ✅ Version control (Git)
- ✅ Testing procedures
- ✅ Secure coding practices

**Evidence Location**:
- Git Repository: All code changes
- Code Reviews: PR history
- Testing: Test files

### A.14.3 - Test Data

**Control**: Test data shall be selected, protected, and used in accordance with the organization's test data policy.

**Implementation Evidence**:
- ✅ Test data isolation
- ✅ Test environment separation
- ✅ Data masking (if applicable)

**Evidence Location**:
- Test environments: Separate AWS accounts
- Test data: Isolated from production

## A.17 - Information Security Aspects of Business Continuity Management

### A.17.1 - Planning Information Security Continuity

**Control**: Information security continuity shall be embedded in the organization's business continuity management systems.

**Implementation Evidence**:
- ✅ Backup procedures
- ✅ Disaster recovery plan
- ✅ High availability design
- ✅ Multi-AZ deployment

**Evidence Location**:
- DynamoDB: Point-in-time recovery
- S3: Versioning
- Terraform State: Versioned in S3
- Documentation: DR plan

## A.18 - Compliance

### A.18.1 - Compliance with Legal and Contractual Requirements

**Control**: All relevant statutory, regulatory, and contractual requirements and the organization's approach to meet these requirements shall be explicitly identified, documented, and kept up to date.

**Implementation Evidence**:
- ✅ Compliance mapping documents
- ✅ Legal requirement tracking
- ✅ Contract compliance

**Evidence Location**:
- Documentation: This document
- Compliance matrix: `docs/compliance/`

### A.18.2 - Information Security Reviews

**Control**: Information security shall be reviewed independently at planned intervals or when significant changes occur.

**Implementation Evidence**:
- ✅ Security audits
- ✅ Access reviews
- ✅ Configuration reviews
- ✅ Penetration testing (external)

**Evidence Location**:
- Audit reports: External
- Access review reports: Automated
- Configuration compliance: AWS Config

## Evidence Collection Schedule

| Control Category | Frequency | Automation |
|-----------------|----------|------------|
| Access Control | Monthly | Automated |
| Logging | Daily | Automated |
| Vulnerability Management | Weekly | Automated |
| Configuration Compliance | Weekly | Automated |
| Security Reviews | Quarterly | Manual + Automated |
| Business Continuity | Annually | Manual |

