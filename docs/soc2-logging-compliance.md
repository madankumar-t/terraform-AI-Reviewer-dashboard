# SOC2 Logging Compliance Guide

## Overview

This document describes how the backend services meet SOC2 logging requirements for audit and compliance.

## SOC2 Control Mapping

### CC2 - Communication and Information

**Requirement**: System captures and communicates information

**Implementation**:
- Structured JSON logging for all services
- Request/response logging
- Error logging with stack traces
- Performance metrics logging

**Evidence**:
- CloudWatch Logs with structured JSON
- API Gateway access logs
- Lambda execution logs

### CC4 - Monitoring Activities

**Requirement**: System monitors activities

**Implementation**:
- Performance metrics (duration, latency)
- Error rate monitoring
- Security event logging
- Audit trail logging

**Evidence**:
- CloudWatch Metrics
- Custom performance logs
- Security event logs

### CC6 - Logical and Physical Access

**Requirement**: System restricts and logs access

**Implementation**:
- Audit logs for all data access
- Security event logging for failed access
- User attribution in logs
- IP address logging

**Evidence**:
- Audit log entries
- Security event logs
- CloudTrail integration

## Logging Standards

### Structured Log Format

All logs use JSON format with required fields:

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "service": "api-handler",
  "environment": "prod",
  "message": "Request processed",
  "trace_id": "abc-123-def",
  "correlation_id": "xyz-789",
  "request": {
    "method": "GET",
    "path": "/api/reviews",
    "user_id": "user@example.com"
  },
  "response": {
    "status_code": 200,
    "duration_ms": 45.2
  }
}
```

### Required Fields

**All Logs**:
- `timestamp`: ISO 8601 UTC timestamp
- `level`: Log level (INFO, WARN, ERROR, DEBUG, AUDIT, SECURITY, PERF)
- `service`: Service name
- `environment`: Environment (dev, staging, prod)
- `message`: Human-readable message
- `trace_id`: Request correlation ID

**Audit Logs** (Additional):
- `audit_event.event_type`: Type of audit event
- `audit_event.user_id`: User/service performing action
- `audit_event.resource`: Resource being accessed
- `audit_event.action`: Action performed
- `audit_event.success`: Success/failure
- `audit_event.ip_address`: Source IP (if available)

**Security Logs** (Additional):
- `security_event.event_type`: Type of security event
- `security_event.severity`: high, medium, low
- `security_event.source_ip`: Source IP address

**Performance Logs** (Additional):
- `performance.operation`: Operation name
- `performance.duration_ms`: Duration in milliseconds

## Audit Events

### Review Creation

```json
{
  "level": "AUDIT",
  "audit_event": {
    "event_type": "review_created",
    "user_id": "user@example.com",
    "resource": "review/abc123",
    "action": "create",
    "success": true,
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

### Review Update

```json
{
  "level": "AUDIT",
  "audit_event": {
    "event_type": "review_updated",
    "user_id": "ai_reviewer",
    "resource": "review/abc123",
    "action": "update",
    "success": true,
    "changes": ["status", "ai_review_result"]
  }
}
```

### Review Completion

```json
{
  "level": "AUDIT",
  "audit_event": {
    "event_type": "review_completed",
    "user_id": "ai_reviewer",
    "resource": "review/abc123",
    "action": "complete",
    "success": true,
    "risk_score": 0.72
  }
}
```

### Review Failure

```json
{
  "level": "AUDIT",
  "audit_event": {
    "event_type": "review_failed",
    "user_id": "ai_reviewer",
    "resource": "review/abc123",
    "action": "fail",
    "success": false,
    "error": "AI service unavailable"
  }
}
```

## Security Events

### Invalid Webhook Signature

```json
{
  "level": "SECURITY",
  "security_event": {
    "event_type": "webhook_signature_invalid",
    "severity": "high",
    "timestamp": "2024-01-15T10:30:00Z"
  },
  "source_ip": "1.2.3.4"
}
```

### Unauthorized Access Attempt

```json
{
  "level": "SECURITY",
  "security_event": {
    "event_type": "unauthorized_access_attempt",
    "severity": "high",
    "timestamp": "2024-01-15T10:30:00Z"
  },
  "resource": "review/abc123",
  "action": "read",
  "source_ip": "1.2.3.4"
}
```

## Log Retention

### CloudWatch Logs
- **Retention**: 30 days (configurable)
- **Storage**: CloudWatch Logs
- **Access**: IAM-controlled

### CloudTrail
- **Retention**: 90 days (CloudTrail)
- **Long-term**: S3 (configurable)
- **Access**: IAM-controlled

### DynamoDB
- **Point-in-time Recovery**: 35 days
- **Backups**: Automated daily
- **Access**: CloudTrail logged

## Log Access Control

### IAM Policies

**Read Access**:
```json
{
  "Effect": "Allow",
  "Action": [
    "logs:DescribeLogGroups",
    "logs:DescribeLogStreams",
    "logs:GetLogEvents",
    "logs:FilterLogEvents"
  ],
  "Resource": "arn:aws:logs:*:*:log-group:/aws/lambda/terraform-*"
}
```

**Write Access** (Lambda only):
```json
{
  "Effect": "Allow",
  "Action": [
    "logs:CreateLogGroup",
    "logs:CreateLogStream",
    "logs:PutLogEvents"
  ],
  "Resource": "arn:aws:logs:*:*:*"
}
```

## Compliance Evidence Collection

### Automated Collection

1. **CloudWatch Logs Export**:
   - Daily export to S3
   - Encrypted at rest
   - Access logged

2. **CloudTrail Integration**:
   - All API calls logged
   - DynamoDB access logged
   - Lambda invocations logged

3. **Custom Metrics**:
   - Error rates
   - Performance metrics
   - Security events

### Manual Collection

1. **Audit Reports**:
   - Monthly audit summaries
   - Access review reports
   - Security incident reports

2. **Evidence Storage**:
   - S3 bucket with versioning
   - Encrypted at rest
   - Access logged

## Logging Best Practices

1. **Always include trace_id** for request correlation
2. **Log all data modifications** with audit events
3. **Log security events immediately** with high severity
4. **Use structured JSON** for machine parsing
5. **Include context** (user_id, resource, action)
6. **Log errors with stack traces** for debugging
7. **Log performance metrics** for optimization
8. **Never log sensitive data** (passwords, tokens)

## Monitoring and Alerting

### Critical Alerts

- Security events (high severity)
- High error rates (> 5%)
- Failed audit events
- Unauthorized access attempts

### Warning Alerts

- Performance degradation
- Increased error rates
- Unusual access patterns

## Compliance Checklist

- [x] Structured logging implemented
- [x] Audit trail for all data modifications
- [x] Security event logging
- [x] Performance metrics logging
- [x] Trace ID correlation
- [x] User attribution
- [x] IP address logging
- [x] Error logging with stack traces
- [x] Log retention configured
- [x] Access control on logs
- [x] Automated evidence collection

