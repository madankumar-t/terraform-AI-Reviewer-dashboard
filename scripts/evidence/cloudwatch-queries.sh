#!/bin/bash
# CloudWatch Log Queries for Compliance Evidence
# These queries can be run via AWS CLI or CloudWatch Insights

set -e

# Configuration
START_DATE=$(date -u -d '30 days ago' +%Y-%m-%dT%H:%M:%S)
END_DATE=$(date -u +%Y-%m-%dT%H:%M:%S)
LOG_GROUP_PREFIX="/aws/lambda/terraform-spacelift-ai-reviewer"

# ============================================
# SOC2 CC2: Communication and Information
# ============================================

echo "=== SOC2 CC2: Communication and Information ==="

# Query 1: All log entries in date range
echo "Query 1: All log entries"
aws logs filter-log-events \
  --log-group-name "${LOG_GROUP_PREFIX}-api-handler-prod" \
  --start-time $(date -u -d "${START_DATE}" +%s)000 \
  --end-time $(date -u -d "${END_DATE}" +%s)000 \
  --max-items 1000 \
  --output json > evidence/cc2-all-logs.json

# Query 2: Error logs
echo "Query 2: Error logs"
aws logs filter-log-events \
  --log-group-name "${LOG_GROUP_PREFIX}-api-handler-prod" \
  --filter-pattern "ERROR" \
  --start-time $(date -u -d "${START_DATE}" +%s)000 \
  --end-time $(date -u -d "${END_DATE}" +%s)000 \
  --output json > evidence/cc2-error-logs.json

# ============================================
# SOC2 CC4: Monitoring Activities
# ============================================

echo "=== SOC2 CC4: Monitoring Activities ==="

# Query 3: Security events
echo "Query 3: Security events"
aws logs filter-log-events \
  --log-group-name "${LOG_GROUP_PREFIX}-jwt-authorizer-prod" \
  --filter-pattern "security_event" \
  --start-time $(date -u -d "${START_DATE}" +%s)000 \
  --end-time $(date -u -d "${END_DATE}" +%s)000 \
  --output json > evidence/cc4-security-events.json

# Query 4: Audit events
echo "Query 4: Audit events"
aws logs filter-log-events \
  --log-group-name "${LOG_GROUP_PREFIX}-api-handler-prod" \
  --filter-pattern "audit_event" \
  --start-time $(date -u -d "${START_DATE}" +%s)000 \
  --end-time $(date -u -d "${END_DATE}" +%s)000 \
  --output json > evidence/cc4-audit-events.json

# ============================================
# SOC2 CC6: Logical and Physical Access
# ============================================

echo "=== SOC2 CC6: Logical and Physical Access ==="

# Query 5: Authorization failures
echo "Query 5: Authorization failures"
aws logs filter-log-events \
  --log-group-name "${LOG_GROUP_PREFIX}-jwt-authorizer-prod" \
  --filter-pattern "authorization_failed OR authorization_insufficient_permissions" \
  --start-time $(date -u -d "${START_DATE}" +%s)000 \
  --end-time $(date -u -d "${END_DATE}" +%s)000 \
  --output json > evidence/cc6-auth-failures.json

# Query 6: Successful authorizations
echo "Query 6: Successful authorizations"
aws logs filter-log-events \
  --log-group-name "${LOG_GROUP_PREFIX}-jwt-authorizer-prod" \
  --filter-pattern "authorization_granted" \
  --start-time $(date -u -d "${START_DATE}" +%s)000 \
  --end-time $(date -u -d "${END_DATE}" +%s)000 \
  --output json > evidence/cc6-auth-success.json

# ============================================
# ISO 27001 A.12.4: Logging and Monitoring
# ============================================

echo "=== ISO 27001 A.12.4: Logging and Monitoring ==="

# Query 7: All Lambda invocations
echo "Query 7: Lambda invocations"
for func in api-handler ai-reviewer webhook-handler pr-review-handler; do
  aws logs filter-log-events \
    --log-group-name "${LOG_GROUP_PREFIX}-${func}-prod" \
    --start-time $(date -u -d "${START_DATE}" +%s)000 \
    --end-time $(date -u -d "${END_DATE}" +%s)000 \
    --max-items 1000 \
    --output json > "evidence/a12-4-${func}-invocations.json"
done

# Query 8: Performance metrics
echo "Query 8: Performance metrics"
aws logs filter-log-events \
  --log-group-name "${LOG_GROUP_PREFIX}-api-handler-prod" \
  --filter-pattern "performance" \
  --start-time $(date -u -d "${START_DATE}" +%s)000 \
  --end-time $(date -u -d "${END_DATE}" +%s)000 \
  --output json > evidence/a12-4-performance.json

# ============================================
# API Gateway Access Logs
# ============================================

echo "=== API Gateway Access Logs ==="

# Query 9: API Gateway access logs
echo "Query 9: API Gateway access"
aws logs filter-log-events \
  --log-group-name "/aws/apigateway/terraform-spacelift-ai-reviewer-prod" \
  --start-time $(date -u -d "${START_DATE}" +%s)000 \
  --end-time $(date -u -d "${END_DATE}" +%s)000 \
  --max-items 1000 \
  --output json > evidence/api-gateway-access.json

# ============================================
# VPC Flow Logs
# ============================================

echo "=== VPC Flow Logs ==="

# Query 10: VPC Flow Logs
echo "Query 10: VPC Flow Logs"
aws logs filter-log-events \
  --log-group-name "/aws/vpc/terraform-spacelift-ai-reviewer-prod-flow-logs" \
  --start-time $(date -u -d "${START_DATE}" +%s)000 \
  --end-time $(date -u -d "${END_DATE}" +%s)000 \
  --max-items 1000 \
  --output json > evidence/vpc-flow-logs.json

# ============================================
# CloudWatch Insights Queries
# ============================================

echo "=== CloudWatch Insights Queries ==="

# Query 11: Error rate by function
cat > evidence/insights-error-rate.query <<EOF
fields @timestamp, @message
| filter @message like /ERROR/
| stats count() as error_count by bin(5m)
| sort @timestamp desc
EOF

# Query 12: User activity
cat > evidence/insights-user-activity.query <<EOF
fields @timestamp, user_id, action
| filter user_id != ""
| stats count() as action_count by user_id, action
| sort action_count desc
EOF

# Query 13: Review creation timeline
cat > evidence/insights-review-timeline.query <<EOF
fields @timestamp, review_id, status
| filter review_id != ""
| stats count() as review_count by bin(1h)
| sort @timestamp desc
EOF

echo "Evidence collection complete. Files saved to evidence/ directory."

