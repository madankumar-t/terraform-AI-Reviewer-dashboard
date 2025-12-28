# Backend Services Summary

## Complete Backend Architecture

### API Gateway Routes

| Route | Method | Handler | Purpose |
|-------|--------|---------|---------|
| `/api/reviews` | GET | api_handler | List reviews |
| `/api/reviews/{reviewId}` | GET | api_handler | Get review |
| `/api/reviews` | POST | api_handler | Create review |
| `/api/reviews/{reviewId}` | PUT | api_handler | Update review |
| `/api/reviews/pr` | POST | pr_review_handler | Create PR review |
| `/api/analytics` | GET | api_handler | Get analytics |
| `/api/analytics/historical` | GET | historical_analysis_handler | Historical analysis |
| `/webhook/spacelift` | POST | webhook_handler | Spacelift webhook |
| `/webhook/github` | POST | github_webhook_handler | GitHub webhook |

### Lambda Functions

1. **api_handler** - Main REST API
2. **ai_reviewer** - AI code analysis
3. **pr_review_handler** - PR review processing
4. **webhook_handler** - Spacelift webhooks
5. **github_webhook_handler** - GitHub webhooks
6. **historical_analysis_handler** - Historical analysis
7. **trend_aggregation_handler** - Scheduled trend aggregation

### Webhook Verification

- **GitHub**: HMAC SHA256 signature verification
- **Spacelift**: HMAC SHA256 signature verification
- **Security Events**: Invalid signatures logged

### DynamoDB Versioning

- Immutable version history
- Sequential version numbers
- Previous version tracking
- Complete audit trail

### Structured Logging

- JSON structured logs
- Trace ID correlation
- Audit trail logging
- Security event logging
- Performance metrics

### SOC2 Compliance

- CC2: Communication and Information ✅
- CC4: Monitoring Activities ✅
- CC6: Logical and Physical Access ✅

## Quick Start

1. Deploy infrastructure: `terraform apply`
2. Configure secrets in Secrets Manager
3. Set webhook URLs in GitHub/Spacelift
4. Test endpoints using API reference

## Documentation

- [Backend Services](./backend-services.md) - Complete service documentation
- [Backend API Reference](./backend-api-reference.md) - API endpoint reference
- [SOC2 Logging Compliance](./soc2-logging-compliance.md) - Compliance guide

