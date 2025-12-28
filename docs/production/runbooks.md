# Production Runbooks

## Overview

This document contains step-by-step procedures for common operational tasks and incident response.

## Table of Contents

1. [Common Operations](#common-operations)
2. [Incident Response](#incident-response)
3. [Maintenance Procedures](#maintenance-procedures)
4. [Troubleshooting](#troubleshooting)

## Common Operations

### Runbook 1: Deploy New Lambda Function Version

**Purpose**: Deploy updated Lambda function code

**Prerequisites**:
- Terraform access
- Code changes committed
- Tests passing

**Steps**:
1. Update Lambda code in repository
2. Run Terraform plan:
   ```bash
   cd terraform
   terraform plan -target=aws_lambda_function.<function_name>
   ```
3. Review changes
4. Apply:
   ```bash
   terraform apply -target=aws_lambda_function.<function_name>
   ```
5. Verify deployment:
   ```bash
   aws lambda get-function --function-name <function_name>
   ```
6. Test function:
   ```bash
   aws lambda invoke --function-name <function_name> output.json
   ```
7. Monitor CloudWatch logs for errors

**Rollback**:
```bash
aws lambda update-function-configuration \
  --function-name <function_name> \
  --revision-id <previous_revision_id>
```

### Runbook 2: Scale DynamoDB Capacity

**Purpose**: Increase DynamoDB read/write capacity

**Prerequisites**:
- DynamoDB table in PROVISIONED mode
- Appropriate IAM permissions

**Steps**:
1. Check current capacity:
   ```bash
   aws dynamodb describe-table --table-name <table_name>
   ```
2. Update capacity via Terraform:
   ```hcl
   read_capacity  = <new_value>
   write_capacity = <new_value>
   ```
3. Apply:
   ```bash
   terraform apply -target=aws_dynamodb_table.reviews
   ```
4. Monitor CloudWatch metrics for throttling

**Alternative (On-Demand)**:
- Switch to PAY_PER_REQUEST mode
- No capacity planning needed

### Runbook 3: Rotate Secrets Manually

**Purpose**: Manually rotate a secret

**Prerequisites**:
- Secrets Manager access
- New secret value ready

**Steps**:
1. Get current secret:
   ```bash
   aws secretsmanager get-secret-value --secret-id <secret_name>
   ```
2. Create new version:
   ```bash
   aws secretsmanager put-secret-value \
     --secret-id <secret_name> \
     --secret-string "<new_value>"
   ```
3. Update secret stage:
   ```bash
   aws secretsmanager update-secret-version-stage \
     --secret-id <secret_name> \
     --version-stage AWSCURRENT \
     --move-to-version-id <new_version_id>
   ```
4. Verify Lambda functions can access new secret
5. Delete old version (after verification):
   ```bash
   aws secretsmanager delete-secret \
     --secret-id <secret_name> \
     --recovery-window-in-days 7
   ```

### Runbook 4: Clear CloudFront Cache

**Purpose**: Invalidate CloudFront cache after frontend update

**Prerequisites**:
- CloudFront distribution ID
- Appropriate permissions

**Steps**:
1. Create invalidation:
   ```bash
   aws cloudfront create-invalidation \
     --distribution-id <distribution_id> \
     --paths "/*"
   ```
2. Monitor invalidation status:
   ```bash
   aws cloudfront get-invalidation \
     --distribution-id <distribution_id> \
     --id <invalidation_id>
   ```
3. Verify cache cleared (check response headers)

### Runbook 5: Restore from Backup

**Purpose**: Restore DynamoDB table from backup

**Prerequisites**:
- Backup available
- Appropriate permissions

**Steps**:
1. List available backups:
   ```bash
   aws dynamodb list-backups --table-name <table_name>
   ```
2. Restore from backup:
   ```bash
   aws dynamodb restore-table-from-backup \
     --target-table-name <new_table_name> \
     --backup-arn <backup_arn>
   ```
3. Verify restored data
4. Update application to use new table
5. Delete old table after verification

## Incident Response

### Runbook 6: High Error Rate

**Symptoms**:
- CloudWatch alarm triggered
- Error rate > 5%
- User complaints

**Steps**:
1. **Identify**: Check which service is failing
   ```bash
   aws cloudwatch get-metric-statistics \
     --namespace AWS/Lambda \
     --metric-name Errors \
     --start-time <time> \
     --end-time <time> \
     --period 300 \
     --statistics Sum
   ```

2. **Investigate**: Review CloudWatch logs
   ```bash
   aws logs filter-log-events \
     --log-group-name /aws/lambda/<function_name> \
     --filter-pattern "ERROR"
   ```

3. **Mitigate**:
   - If Lambda timeout: Increase timeout
   - If DynamoDB throttling: Scale capacity
   - If Bedrock error: Check service status
   - If code error: Deploy fix

4. **Verify**: Monitor error rate decreases
5. **Document**: Update incident log

**Escalation**: If error rate > 10% for > 15 minutes

### Runbook 7: API Gateway 5xx Errors

**Symptoms**:
- 5xx error alarm triggered
- API requests failing
- High error rate

**Steps**:
1. **Check API Gateway logs**:
   ```bash
   aws logs filter-log-events \
     --log-group-name /aws/apigateway/<api_name> \
     --filter-pattern "5xx"
   ```

2. **Identify root cause**:
   - Lambda function errors
   - Integration timeouts
   - Throttling

3. **Fix**:
   - Deploy Lambda fix
   - Increase timeout
   - Scale resources

4. **Verify**: Test API endpoints
5. **Monitor**: Watch error rate

### Runbook 8: Lambda Function Timeout

**Symptoms**:
- Lambda timeout errors
- Requests timing out
- User complaints

**Steps**:
1. **Check function duration**:
   ```bash
   aws cloudwatch get-metric-statistics \
     --namespace AWS/Lambda \
     --metric-name Duration \
     --dimensions Name=FunctionName,Value=<function_name> \
     --start-time <time> \
     --end-time <time> \
     --period 300 \
     --statistics Average,Maximum
   ```

2. **Review logs** for bottlenecks:
   ```bash
   aws logs filter-log-events \
     --log-group-name /aws/lambda/<function_name> \
     --filter-pattern "duration"
   ```

3. **Options**:
   - Increase timeout (quick fix)
   - Optimize code (long-term)
   - Increase memory (may help)

4. **Deploy fix**:
   ```bash
   terraform apply -target=aws_lambda_function.<function_name>
   ```

5. **Verify**: Monitor duration metrics

### Runbook 9: DynamoDB Throttling

**Symptoms**:
- Throttling errors in logs
- Slow responses
- User complaints

**Steps**:
1. **Check throttling metrics**:
   ```bash
   aws cloudwatch get-metric-statistics \
     --namespace AWS/DynamoDB \
     --metric-name UserErrors \
     --dimensions Name=TableName,Value=<table_name> \
     --start-time <time> \
     --end-time <time> \
     --period 300 \
     --statistics Sum
   ```

2. **Check capacity utilization**:
   ```bash
   aws dynamodb describe-table --table-name <table_name>
   ```

3. **Scale up**:
   - If PROVISIONED: Increase capacity
   - If ON_DEMAND: Check for hot partitions

4. **Optimize**:
   - Review query patterns
   - Add GSIs if needed
   - Implement caching

5. **Monitor**: Watch throttling decrease

### Runbook 10: Security Incident

**Symptoms**:
- Unauthorized access attempts
- Security alarm triggered
- Unusual activity

**Steps**:
1. **IMMEDIATE**: Block suspicious IPs
   ```bash
   # Update WAF IP set
   aws wafv2 update-ip-set \
     --scope REGIONAL \
     --id <ip_set_id> \
     --addresses <ip_addresses>
   ```

2. **Investigate**:
   - Review CloudTrail logs
   - Check access logs
   - Identify compromised accounts

3. **Contain**:
   - Revoke compromised credentials
   - Rotate secrets
   - Update IAM policies

4. **Notify**: Security team, management
5. **Document**: Security incident report
6. **Remediate**: Fix vulnerabilities

**Escalation**: Always escalate security incidents

## Maintenance Procedures

### Runbook 11: Scheduled Maintenance

**Purpose**: Perform scheduled maintenance tasks

**Frequency**: Monthly

**Steps**:
1. **Pre-maintenance**:
   - Notify users
   - Create maintenance window
   - Prepare rollback plan

2. **Maintenance tasks**:
   - Update dependencies
   - Apply security patches
   - Rotate secrets
   - Review and clean logs

3. **Post-maintenance**:
   - Verify all services operational
   - Monitor for issues
   - Update documentation

### Runbook 12: Log Cleanup

**Purpose**: Clean up old CloudWatch logs

**Frequency**: Monthly

**Steps**:
1. **Identify old log groups**:
   ```bash
   aws logs describe-log-groups \
     --log-group-name-prefix /aws/lambda/
   ```

2. **Delete old logs** (if retention expired):
   ```bash
   aws logs delete-log-group \
     --log-group-name <log_group_name>
   ```

3. **Verify**: Check log retention policies

### Runbook 13: Cost Review

**Purpose**: Review and optimize costs

**Frequency**: Monthly

**Steps**:
1. **Generate cost report**:
   ```bash
   aws ce get-cost-and-usage \
     --time-period Start=<start>,End=<end> \
     --granularity MONTHLY \
     --metrics BlendedCost
   ```

2. **Identify cost drivers**:
   - High Lambda invocations
   - DynamoDB capacity
   - CloudFront data transfer
   - NAT Gateway costs

3. **Optimize**:
   - Right-size resources
   - Enable auto-scaling
   - Use reserved capacity
   - Optimize queries

4. **Document**: Cost optimization report

## Troubleshooting

### Runbook 14: Debug Lambda Function

**Steps**:
1. **Check function status**:
   ```bash
   aws lambda get-function --function-name <function_name>
   ```

2. **Review logs**:
   ```bash
   aws logs tail /aws/lambda/<function_name> --follow
   ```

3. **Test locally** (if possible):
   ```bash
   sam local invoke <function_name>
   ```

4. **Check environment variables**:
   ```bash
   aws lambda get-function-configuration --function-name <function_name>
   ```

5. **Test with sample event**:
   ```bash
   aws lambda invoke \
     --function-name <function_name> \
     --payload file://test-event.json \
     output.json
   ```

### Runbook 15: Debug API Gateway

**Steps**:
1. **Check API status**:
   ```bash
   aws apigatewayv2 get-api --api-id <api_id>
   ```

2. **Review access logs**:
   ```bash
   aws logs filter-log-events \
     --log-group-name /aws/apigateway/<api_name> \
     --start-time <time>
   ```

3. **Test endpoint**:
   ```bash
   curl -X GET <api_endpoint>/api/reviews \
     -H "Authorization: Bearer <token>"
   ```

4. **Check integration**:
   - Verify Lambda integration
   - Check authorizer configuration
   - Review route settings

### Runbook 16: Debug DynamoDB

**Steps**:
1. **Check table status**:
   ```bash
   aws dynamodb describe-table --table-name <table_name>
   ```

2. **Query table**:
   ```bash
   aws dynamodb query \
     --table-name <table_name> \
     --key-condition-expression "PK = :pk" \
     --expression-attribute-values '{":pk":{"S":"<value>"}}'
   ```

3. **Check metrics**:
   ```bash
   aws cloudwatch get-metric-statistics \
     --namespace AWS/DynamoDB \
     --metric-name ConsumedReadCapacityUnits \
     --dimensions Name=TableName,Value=<table_name>
   ```

4. **Review throttling**:
   - Check capacity settings
   - Review query patterns
   - Identify hot partitions

## Emergency Contacts

- **On-Call Engineer**: [Contact Info]
- **Senior Engineer**: [Contact Info]
- **Security Team**: [Contact Info]
- **AWS Support**: [Support Plan Details]

## Quick Reference

### Common Commands

```bash
# Lambda
aws lambda list-functions
aws lambda get-function --function-name <name>
aws lambda invoke --function-name <name> output.json

# DynamoDB
aws dynamodb list-tables
aws dynamodb describe-table --table-name <name>
aws dynamodb scan --table-name <name>

# API Gateway
aws apigatewayv2 get-apis
aws apigatewayv2 get-api --api-id <id>

# CloudWatch
aws cloudwatch get-metric-statistics --namespace <ns> --metric-name <metric>
aws logs tail <log-group> --follow

# Secrets
aws secretsmanager list-secrets
aws secretsmanager get-secret-value --secret-id <id>
```

### Useful Links

- CloudWatch Dashboard: [URL]
- API Gateway Console: [URL]
- DynamoDB Console: [URL]
- Lambda Console: [URL]

