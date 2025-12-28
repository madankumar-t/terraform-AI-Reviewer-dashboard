-- DynamoDB Audit Queries
-- These queries can be adapted for DynamoDB Query/Scan operations
-- or used with DynamoDB Streams and exported to a queryable format

-- ============================================
-- SOC2 CC2: Communication and Information
-- ============================================

-- Query 1: All reviews created in date range
-- Purpose: Verify information capture and storage
SELECT review_id, created_at, status, version
FROM reviews
WHERE created_at BETWEEN :start_date AND :end_date
ORDER BY created_at DESC;

-- Query 2: Review version history
-- Purpose: Verify complete audit trail
SELECT review_id, version, previous_version_id, created_at, updated_at
FROM reviews
WHERE review_id = :review_id
ORDER BY version ASC;

-- Query 3: Reviews by status
-- Purpose: Monitor system operations
SELECT status, COUNT(*) as count
FROM reviews
WHERE created_at >= :start_date
GROUP BY status;

-- ============================================
-- SOC2 CC4: Monitoring Activities
-- ============================================

-- Query 4: High-risk reviews
-- Purpose: Identify reviews requiring attention
SELECT review_id, overall_risk_score, created_at, status
FROM reviews
WHERE ai_review_result.overall_risk_score > 0.67
  AND created_at >= :start_date
ORDER BY overall_risk_score DESC;

-- Query 5: Failed reviews
-- Purpose: Monitor system failures
SELECT review_id, status, created_at, error_message
FROM reviews
WHERE status = 'failed'
  AND created_at >= :start_date
ORDER BY created_at DESC;

-- ============================================
-- SOC2 CC6: Logical and Physical Access
-- ============================================

-- Query 6: Reviews by user (from audit logs)
-- Note: User information stored in review metadata or CloudTrail
SELECT review_id, created_at, review_metadata.user_id, review_metadata.user_email
FROM reviews
WHERE review_metadata.user_id = :user_id
  AND created_at >= :start_date
ORDER BY created_at DESC;

-- Query 7: Recent review modifications
-- Purpose: Track data access and modifications
SELECT review_id, version, updated_at, previous_version_id
FROM reviews
WHERE updated_at >= :start_date
ORDER BY updated_at DESC;

-- ============================================
-- ISO 27001 A.12.4: Logging and Monitoring
-- ============================================

-- Query 8: Security findings summary
-- Purpose: Monitor security posture
SELECT 
  review_id,
  ai_review_result.security_analysis.total_findings,
  ai_review_result.security_analysis.high_severity,
  ai_review_result.security_analysis.medium_severity,
  ai_review_result.security_analysis.low_severity,
  created_at
FROM reviews
WHERE ai_review_result.security_analysis IS NOT NULL
  AND created_at >= :start_date
ORDER BY ai_review_result.security_analysis.total_findings DESC;

-- Query 9: Cost analysis trends
-- Purpose: Monitor resource usage
SELECT 
  review_id,
  ai_review_result.cost_analysis.estimated_monthly_cost,
  ai_review_result.cost_analysis.resource_count,
  created_at
FROM reviews
WHERE ai_review_result.cost_analysis IS NOT NULL
  AND created_at >= :start_date
ORDER BY created_at DESC;

-- ============================================
-- ISO 27001 A.9.2: User Access Management
-- ============================================

-- Query 10: Review creation frequency by user
-- Purpose: Detect unusual access patterns
SELECT 
  review_metadata.user_id,
  COUNT(*) as review_count,
  MIN(created_at) as first_review,
  MAX(created_at) as last_review
FROM reviews
WHERE review_metadata.user_id IS NOT NULL
  AND created_at >= :start_date
GROUP BY review_metadata.user_id
ORDER BY review_count DESC;

-- ============================================
-- Compliance: Complete Audit Trail
-- ============================================

-- Query 11: Complete review lifecycle
-- Purpose: Full audit trail for compliance
SELECT 
  review_id,
  version,
  status,
  created_at,
  updated_at,
  previous_version_id,
  review_metadata.user_id,
  review_metadata.user_email,
  ai_review_result.overall_risk_score
FROM reviews
WHERE review_id = :review_id
ORDER BY version ASC;

-- Query 12: Reviews with no AI analysis
-- Purpose: Identify incomplete reviews
SELECT review_id, created_at, status
FROM reviews
WHERE ai_review_result IS NULL
  AND created_at >= :start_date
ORDER BY created_at DESC;

-- ============================================
-- Data Retention and Compliance
-- ============================================

-- Query 13: Reviews older than retention period
-- Purpose: Data retention compliance
SELECT review_id, created_at, status
FROM reviews
WHERE created_at < :retention_cutoff_date
ORDER BY created_at ASC;

-- Query 14: Version count per review
-- Purpose: Monitor versioning compliance
SELECT 
  review_id,
  COUNT(*) as version_count,
  MAX(version) as latest_version,
  MIN(created_at) as first_created,
  MAX(updated_at) as last_updated
FROM reviews
GROUP BY review_id
HAVING COUNT(*) > 1
ORDER BY version_count DESC;

-- ============================================
-- Performance and Capacity Monitoring
-- ============================================

-- Query 15: Review processing time analysis
-- Purpose: Monitor system performance
SELECT 
  review_id,
  created_at,
  updated_at,
  TIMESTAMPDIFF(SECOND, created_at, updated_at) as processing_seconds,
  status
FROM reviews
WHERE status = 'completed'
  AND created_at >= :start_date
ORDER BY processing_seconds DESC;

-- ============================================
-- Spacelift Integration Monitoring
-- ============================================

-- Query 16: Reviews by Spacelift run
-- Purpose: Track Spacelift integration
SELECT 
  spacelift_run_id,
  COUNT(*) as review_count,
  COUNT(DISTINCT status) as status_count,
  MIN(created_at) as first_review,
  MAX(created_at) as last_review
FROM reviews
WHERE spacelift_run_id IS NOT NULL
  AND created_at >= :start_date
GROUP BY spacelift_run_id
ORDER BY review_count DESC;

-- ============================================
-- Risk Trend Analysis
-- ============================================

-- Query 17: Risk score trends over time
-- Purpose: Monitor risk trends for compliance
SELECT 
  DATE(created_at) as review_date,
  AVG(ai_review_result.overall_risk_score) as avg_risk_score,
  COUNT(*) as review_count,
  SUM(CASE WHEN ai_review_result.overall_risk_score > 0.67 THEN 1 ELSE 0 END) as high_risk_count
FROM reviews
WHERE ai_review_result.overall_risk_score IS NOT NULL
  AND created_at >= :start_date
GROUP BY DATE(created_at)
ORDER BY review_date DESC;

