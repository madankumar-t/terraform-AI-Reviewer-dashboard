# DynamoDB Schema Design Summary

## Quick Reference

### Table Name
`terraform-spacelift-ai-reviewer-reviews-{environment}`

### Primary Key
- **PK**: `REVIEW#{review_id}` | `STACK#{stack_id}` | `FINDING#{finding_id}` | `ISSUE#{issue_hash}`
- **SK**: `VERSION#{version}` | `STATS` | `REVIEW#{review_id}` | `STACK#{stack_id}`

### Global Secondary Indexes

| Index | Partition Key | Sort Key | Purpose |
|-------|--------------|---------|---------|
| GSI1 | Stack ID | Created Timestamp | Stack history queries |
| GSI2 | Risk Date | Risk Score | Risk trend analysis |
| GSI3 | Issue Category+Hash | Timestamp/Frequency | Repeated issue tracking |
| GSI4 | Status | Created Timestamp | Status-based queries |

## Key Design Decisions

### 1. Single-Table Design
- All entities in one table
- Entity type discrimination via PK/SK patterns
- Efficient queries via GSIs
- Reduced operational overhead

### 2. Versioning Strategy
- Immutable version history
- Sequential version numbers
- Previous version tracking
- Complete audit trail

### 3. Hot Partition Avoidance
- Date-based sharding for time-series data
- Random sharding for high-volume writes
- GSI projection optimization
- Read distribution strategies

### 4. Compliance Features
- Immutability enforcement
- Complete audit trail
- Access logging
- Encryption at rest and in transit
- Data retention policies

## Access Patterns Supported

✅ Get latest review by ID  
✅ Get all versions of a review  
✅ Get stack history (chronological)  
✅ Get reviews by date range  
✅ Get high-risk reviews  
✅ Analyze risk trends  
✅ Find repeated issues  
✅ Get pending/failed reviews  
✅ Compare review versions  
✅ Get audit trail  
✅ Get stack statistics  

## Example Use Cases

### Use Case 1: Initial Run Review
- Create Version 1 with status "pending"
- Process AI review → status "completed"
- Store findings and risk scores
- Update stack statistics

### Use Case 2: Failed Run
- Create Version 1 with status "failed"
- Store error details
- Track for retry logic
- Alert monitoring systems

### Use Case 3: Fix Applied
- Create new version (Version 3)
- Mark FixApplied = true
- Store fix details
- Compare risk scores (before/after)
- Update issue frequency tracking

## Performance Characteristics

### Read Performance
- Single-item reads: < 10ms
- Query operations: < 50ms
- GSI queries: < 100ms
- Batch operations: < 200ms

### Write Performance
- Single-item writes: < 20ms
- Batch writes: < 100ms
- GSI write amplification: ~4x (4 GSIs)

### Scalability
- Supports millions of reviews
- Auto-scaling with on-demand mode
- No hot partition issues with proper sharding
- Efficient GSI queries

## Compliance Guarantees

### Immutability
✅ Version-based writes only  
✅ No update operations  
✅ Conditional writes prevent overwrites  
✅ Point-in-time recovery enabled  

### Audit Trail
✅ Complete version history  
✅ Timestamps on all records  
✅ User attribution (CreatedBy)  
✅ Change tracking  

### Data Protection
✅ Encryption at rest (KMS)  
✅ Encryption in transit (TLS)  
✅ Access logging (CloudTrail)  
✅ VPC endpoints for private access  

### Retention
✅ Point-in-time recovery (35 days)  
✅ Automated backups  
✅ TTL for archival (optional)  
✅ Glacier for long-term retention  

## Best Practices Implemented

1. **Item Size**: Keep under 400 KB (store large code in S3)
2. **Query Optimization**: Use specific partition keys, limit results
3. **Write Optimization**: Batch writes, minimize GSI projections
4. **Monitoring**: Track capacity, hot partitions, GSI lag
5. **Error Handling**: Retry logic with exponential backoff

## Migration Considerations

### From Current Schema
- Map existing PK/SK to new patterns
- Migrate GSI keys
- Update application code
- Test query patterns

### Future Enhancements
- Add more GSIs if needed
- Implement caching layer
- Add DynamoDB Streams for real-time processing
- Consider DAX for read caching

## References

- [Complete Schema Design](./dynamodb-schema.md)
- [Query Patterns](./dynamodb-queries.md)
- [AWS DynamoDB Best Practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html)

