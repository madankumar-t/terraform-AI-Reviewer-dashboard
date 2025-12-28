# Compliance Evidence Checklist

## Overview

Complete checklist for SOC2 and ISO 27001 compliance evidence collection.

## Evidence Collection Schedule

| Evidence Type | Frequency | Owner | Automation |
|--------------|----------|-------|------------|
| Access Reviews | Monthly | Security Team | ✅ Automated |
| Log Aggregation | Daily | DevOps | ✅ Automated |
| Monitoring Reports | Weekly | DevOps | ✅ Automated |
| Configuration Compliance | Weekly | DevOps | ✅ Automated |
| Security Reviews | Quarterly | Security Team | ⚠️ Semi-Automated |
| Disaster Recovery Test | Annually | DevOps | ❌ Manual |

## SOC2 Evidence Checklist

### CC2 - Communication and Information

- [ ] **Daily Log Aggregation** (Automated)
  - CloudWatch Logs exported
  - Log retention verified
  - Evidence file: `evidence/cc2-daily-logs-YYYY-MM-DD.json`

- [ ] **Review Metadata** (Automated)
  - All reviews have metadata
  - Metadata includes user, timestamp
  - Evidence file: `evidence/cc2-review-metadata-YYYY-MM.json`

- [ ] **Information Capture** (Continuous)
  - All API requests logged
  - All review operations logged
  - Evidence: CloudWatch Logs

### CC4 - Monitoring Activities

- [ ] **Weekly Monitoring Report** (Automated)
  - CloudWatch Dashboard snapshot
  - Alarm status summary
  - Evidence file: `evidence/cc4-monitoring-report-YYYY-WW.json`

- [ ] **Alarm Configuration** (Quarterly)
  - All alarms configured
  - Thresholds appropriate
  - Evidence file: `evidence/cc4-alarm-config-YYYY-QX.json`

- [ ] **Performance Metrics** (Weekly)
  - Latency metrics
  - Throughput metrics
  - Evidence file: `evidence/cc4-performance-YYYY-WW.json`

### CC6 - Logical and Physical Access

- [ ] **Monthly Access Review** (Automated)
  - IAM roles reviewed
  - User access reviewed
  - Evidence file: `evidence/access-reviews/access-review-YYYY-MM.json`

- [ ] **Access Logs** (Daily)
  - Authorization events logged
  - Failed access attempts logged
  - Evidence: CloudWatch Logs

- [ ] **IAM Policy Review** (Quarterly)
  - Policies reviewed
  - Least privilege verified
  - Evidence file: `evidence/cc6-iam-review-YYYY-QX.json`

### CC7 - System Operations

- [ ] **Change Management** (Continuous)
  - All changes in Git
  - Change approvals documented
  - Evidence: Git history

- [ ] **Configuration Management** (Weekly)
  - Terraform state reviewed
  - Configuration drift checked
  - Evidence file: `evidence/cc7-config-compliance-YYYY-WW.json`

- [ ] **Deployment Records** (Continuous)
  - Deployment logs
  - Rollback procedures
  - Evidence: CI/CD logs

## ISO 27001 Evidence Checklist

### A.9 - Access Control

- [ ] **User Access Management** (Monthly)
  - User accounts reviewed
  - Access rights verified
  - Evidence file: `evidence/a9-user-access-YYYY-MM.json`

- [ ] **Privileged Access** (Monthly)
  - Admin access reviewed
  - Privilege escalation logged
  - Evidence file: `evidence/a9-privileged-access-YYYY-MM.json`

- [ ] **Access Control Matrix** (Quarterly)
  - Roles and permissions documented
  - Access matrix updated
  - Evidence file: `evidence/a9-access-matrix-YYYY-QX.json`

### A.12 - Operations Security

- [ ] **Logging Configuration** (Quarterly)
  - Log retention verified
  - Log integrity checked
  - Evidence file: `evidence/a12-logging-config-YYYY-QX.json`

- [ ] **Monitoring Activities** (Weekly)
  - Security events monitored
  - Anomalies detected
  - Evidence file: `evidence/a12-monitoring-YYYY-WW.json`

- [ ] **Vulnerability Management** (Monthly)
  - Vulnerabilities scanned
  - Patches applied
  - Evidence file: `evidence/a12-vulnerabilities-YYYY-MM.json`

### A.14 - System Acquisition, Development, and Maintenance

- [ ] **Code Review Process** (Continuous)
  - All code reviewed
  - Security reviews completed
  - Evidence: Git PR history

- [ ] **Testing Procedures** (Continuous)
  - Tests executed
  - Test results documented
  - Evidence: CI/CD test reports

- [ ] **Secure Development** (Quarterly)
  - Secure coding practices verified
  - Security training completed
  - Evidence file: `evidence/a14-secure-dev-YYYY-QX.json`

### A.18 - Compliance

- [ ] **Compliance Reviews** (Quarterly)
  - SOC2 controls reviewed
  - ISO 27001 controls reviewed
  - Evidence file: `evidence/a18-compliance-review-YYYY-QX.json`

- [ ] **Legal Requirements** (Annually)
  - Legal requirements identified
  - Compliance verified
  - Evidence file: `evidence/a18-legal-compliance-YYYY.json`

- [ ] **Audit Evidence** (Continuous)
  - Evidence collected
  - Evidence stored securely
  - Evidence: Evidence repository

## Automated Evidence Generation

### Daily Evidence

Run daily evidence collection:
```bash
python scripts/evidence/generate-evidence.py \
  --table-name terraform-spacelift-ai-reviewer-reviews-prod \
  --log-group-prefix /aws/lambda/terraform-spacelift-ai-reviewer
```

Generates:
- `evidence/cc2-daily-logs-YYYY-MM-DD.json`
- `evidence/cc4-monitoring-YYYY-MM-DD.json`

### Weekly Evidence

Run weekly evidence collection:
```bash
python scripts/evidence/generate-evidence.py --weekly
bash scripts/evidence/cloudwatch-queries.sh
```

Generates:
- `evidence/cc4-monitoring-report-YYYY-WW.json`
- `evidence/a12-monitoring-YYYY-WW.json`

### Monthly Evidence

Run monthly access review:
```bash
python scripts/evidence/access-review-report.py \
  --log-group-prefix /aws/lambda/terraform-spacelift-ai-reviewer \
  --user-pool-id <cognito_user_pool_id>
```

Generates:
- `evidence/access-reviews/access-review-YYYY-MM.json`
- `evidence/access-reviews/access-review-YYYY-MM-summary.csv`

## Evidence Storage

### Storage Location

- **Primary**: S3 bucket `terraform-spacelift-ai-reviewer-evidence-prod`
- **Backup**: DR region S3 bucket
- **Retention**: 7 years (compliance requirement)

### Evidence Organization

```
evidence/
├── soc2/
│   ├── cc2-communication/
│   ├── cc4-monitoring/
│   ├── cc6-access-control/
│   └── cc7-system-operations/
├── iso27001/
│   ├── a9-access-control/
│   ├── a12-operations/
│   ├── a14-development/
│   └── a18-compliance/
├── access-reviews/
├── audit-queries/
└── summaries/
```

### Evidence Security

- **Encryption**: AES-256 at rest
- **Access Control**: IAM policies
- **Versioning**: Enabled
- **Backup**: Cross-region replication

## Evidence Validation

### Automated Validation

Run evidence validation:
```bash
python scripts/evidence/validate-evidence.py
```

Checks:
- Evidence completeness
- Evidence format
- Required fields present
- Timestamps valid

### Manual Review

Monthly manual review:
- Evidence completeness
- Evidence quality
- Compliance alignment
- Improvement opportunities

## Evidence Reporting

### Monthly Summary

Generated automatically:
- Evidence collection status
- Missing evidence items
- Compliance gaps
- Recommendations

### Quarterly Audit

Prepared for auditors:
- Complete evidence package
- Evidence index
- Compliance mapping
- Control evidence matrix

## Compliance Gaps

### Gap Tracking

Track compliance gaps:
- Gap identified
- Root cause
- Remediation plan
- Target date
- Status

### Gap Remediation

Process:
1. Identify gap
2. Assess risk
3. Create remediation plan
4. Implement fix
5. Verify compliance
6. Update evidence

## Continuous Improvement

### Evidence Quality

Regularly review:
- Evidence completeness
- Evidence accuracy
- Evidence relevance
- Evidence timeliness

### Process Improvement

Identify opportunities:
- Automation improvements
- Process streamlining
- Tool enhancements
- Training needs

