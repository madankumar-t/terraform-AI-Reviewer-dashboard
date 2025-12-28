# DynamoDB Schema Visual Diagram

## Table Structure Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│         terraform-spacelift-ai-reviewer-reviews-{environment}                │
│                                                                              │
│  Primary Key: PK (String) | SK (String)                                     │
│                                                                              │
│  Global Secondary Indexes:                                                  │
│  - GSI1: Stack History (GSI1PK | GSI1SK)                                   │
│  - GSI2: Risk Trends (GSI2PK | GSI2SK)                                       │
│  - GSI3: Repeated Issues (GSI3PK | GSI3SK)                                  │
│  - GSI4: Status & Time (GSI4PK | GSI4SK)                                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Entity Relationships

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           REVIEW ENTITY                                      │
│                                                                              │
│  PK: REVIEW#{review_id}                                                     │
│  SK: VERSION#{version_number}                                               │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Version 1 (Initial)                                                  │  │
│  │  - Status: pending → completed                                       │  │
│  │  - Risk Score: 0.72                                                   │  │
│  │  - Findings: 3                                                       │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                            │                                                 │
│                            │ PreviousVersionId                              │
│                            ▼                                                 │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Version 2 (Update)                                                   │  │
│  │  - Status: completed                                                 │  │
│  │  - Risk Score: 0.72                                                  │  │
│  │  - Findings: 3                                                       │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                            │                                                 │
│                            │ PreviousVersionId                              │
│                            ▼                                                 │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Version 3 (Fix Applied)                                             │  │
│  │  - Status: completed                                                 │  │
│  │  - Risk Score: 0.35 (reduced!)                                       │  │
│  │  - Findings: 1                                                       │  │
│  │  - FixApplied: true                                                 │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                            │
                            │ Links to
                            ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          FINDING ENTITY                                      │
│                                                                              │
│  PK: FINDING#{finding_id}                                                  │
│  SK: REVIEW#{review_id}                                                    │
│                                                                              │
│  - Category: security/cost/reliability                                      │
│  - Severity: high/medium/low                                                │
│  - IssueHash: for repeated issue tracking                                  │
└─────────────────────────────────────────────────────────────────────────────┘
                            │
                            │ Groups by
                            ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      ISSUE FREQUENCY ENTITY                                 │
│                                                                              │
│  PK: ISSUE#{issue_hash}                                                     │
│  SK: STACK#{stack_id}                                                       │
│                                                                              │
│  - OccurrenceCount: 15                                                      │
│  - FirstSeen: 2024-01-01                                                   │
│  - LastSeen: 2024-01-15                                                    │
│  - FixApplied: false                                                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

## GSI Access Patterns

### GSI1: Stack History

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  GSI1PK: STACK#prod-stack-001                                               │
│  GSI1SK: CREATED#2024-01-15T10:30:00Z                                       │
│                                                                              │
│  Query: Get all reviews for stack, chronological order                      │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Review 1: CREATED#2024-01-15T10:30:00Z                              │  │
│  │  Review 2: CREATED#2024-01-15T11:00:00Z                              │  │
│  │  Review 3: CREATED#2024-01-16T10:30:00Z                              │  │
│  │  ...                                                                  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### GSI2: Risk Trends

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  GSI2PK: RISK#2024-01-15                                                   │
│  GSI2SK: 0.72 (Risk Score as String)                                       │
│                                                                              │
│  Query: Get high-risk reviews for a date                                  │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Review A: 0.95 (High Risk)                                          │  │
│  │  Review B: 0.72 (High Risk)                                           │  │
│  │  Review C: 0.45 (Medium Risk)                                         │  │
│  │  Review D: 0.20 (Low Risk)                                            │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  Trend Analysis:                                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Date       | Avg Risk | Count                                       │  │
│  │  2024-01-15 | 0.58     | 10                                          │  │
│  │  2024-01-16 | 0.45     | 12                                          │  │
│  │  2024-01-17 | 0.35     | 15  (Improving!)                            │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### GSI3: Repeated Issues

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  GSI3PK: ISSUE#CATEGORY#security#HASH#abc123                               │
│  GSI3SK: CREATED#2024-01-15T10:30:00Z                                      │
│                                                                              │
│  Query: Find all occurrences of specific issue                             │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Issue: "Public S3 Bucket"                                            │  │
│  │  Hash: abc123                                                          │  │
│  │                                                                        │  │
│  │  Occurrences:                                                          │  │
│  │  - Review 1: 2024-01-01                                               │  │
│  │  - Review 2: 2024-01-05                                               │  │
│  │  - Review 3: 2024-01-10                                               │  │
│  │  - Review 4: 2024-01-15                                               │  │
│  │  ...                                                                   │  │
│  │                                                                        │  │
│  │  Frequency: 15 occurrences across 3 stacks                            │  │
│  │  Fix Applied: false                                                   │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### GSI4: Status & Time

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  GSI4PK: STATUS#completed                                                   │
│  GSI4SK: CREATED#2024-01-15T10:31:00Z                                       │
│                                                                              │
│  Query: Get reviews by status                                              │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  STATUS#pending                                                       │  │
│  │  - Review 1: CREATED#2024-01-15T10:30:00Z                             │  │
│  │  - Review 2: CREATED#2024-01-15T11:00:00Z                             │  │
│  │                                                                        │  │
│  │  STATUS#completed                                                      │  │
│  │  - Review 3: CREATED#2024-01-15T10:31:00Z                             │  │
│  │  - Review 4: CREATED#2024-01-15T11:01:00Z                             │  │
│  │                                                                        │  │
│  │  STATUS#failed                                                         │  │
│  │  - Review 5: CREATED#2024-01-15T11:02:00Z                             │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Data Flow: Review Lifecycle

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        REVIEW LIFECYCLE                                     │
│                                                                              │
│  1. CREATE (Version 1)                                                      │
│     ┌──────────────────────────────────────────────────────────────────┐   │
│     │  PK: REVIEW#abc123                                                │   │
│     │  SK: VERSION#1                                                    │   │
│     │  Status: pending                                                  │   │
│     │  PreviousVersionId: null                                         │   │
│     └──────────────────────────────────────────────────────────────────┘   │
│                            │                                                 │
│                            │ AI Review Process                              │
│                            ▼                                                 │
│  2. UPDATE (Version 2)                                                      │
│     ┌──────────────────────────────────────────────────────────────────┐   │
│     │  PK: REVIEW#abc123                                                │   │
│     │  SK: VERSION#2                                                    │   │
│     │  Status: completed                                                │   │
│     │  PreviousVersionId: REVIEW#abc123#VERSION#1                      │   │
│     │  RiskScore: 0.72                                                  │   │
│     │  Findings: 3                                                      │   │
│     └──────────────────────────────────────────────────────────────────┘   │
│                            │                                                 │
│                            │ Fix Applied                                     │
│                            ▼                                                 │
│  3. FIX APPLIED (Version 3)                                                 │
│     ┌──────────────────────────────────────────────────────────────────┐   │
│     │  PK: REVIEW#abc123                                                │   │
│     │  SK: VERSION#3                                                    │   │
│     │  Status: completed                                                │   │
│     │  PreviousVersionId: REVIEW#abc123#VERSION#2                      │   │
│     │  RiskScore: 0.35 (reduced!)                                       │   │
│     │  Findings: 1                                                      │   │
│     │  FixApplied: true                                                 │   │
│     │  FixDetails: {...}                                                │   │
│     └──────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  All versions preserved for audit trail                                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Partition Key Distribution

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PARTITION KEY STRATEGY                                   │
│                                                                              │
│  REVIEW#{review_id}                                                         │
│  ├── VERSION#1  (Initial)                                                  │
│  ├── VERSION#2  (Update)                                                   │
│  └── VERSION#3  (Fix Applied)                                              │
│                                                                              │
│  STACK#{stack_id}                                                           │
│  ├── STATS  (Aggregated statistics)                                        │
│  └── METADATA  (Stack metadata)                                             │
│                                                                              │
│  FINDING#{finding_id}                                                       │
│  ├── REVIEW#{review_id_1}  (Finding in Review 1)                          │
│  ├── REVIEW#{review_id_2}  (Finding in Review 2)                          │
│  └── REVIEW#{review_id_3}  (Finding in Review 3)                          │
│                                                                              │
│  ISSUE#{issue_hash}                                                         │
│  ├── STACK#{stack_id_1}  (Issue in Stack 1)                              │
│  ├── STACK#{stack_id_2}  (Issue in Stack 2)                               │
│  └── STACK#{stack_id_3}  (Issue in Stack 3)                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Hot Partition Avoidance Strategy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              HOT PARTITION AVOIDANCE                                        │
│                                                                              │
│  Problem: High-volume stack creates hot partition                            │
│                                                                              │
│  Solution 1: Date-based Sharding                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  GSI1PK: STACK#prod-stack-001#DATE#2024-01-15                         │  │
│  │  GSI1PK: STACK#prod-stack-001#DATE#2024-01-16                         │  │
│  │  GSI1PK: STACK#prod-stack-001#DATE#2024-01-17                         │  │
│  │  (Distributes writes across partitions)                              │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  Solution 2: Random Sharding                                                │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  GSI1PK: STACK#prod-stack-001#SHARD#0                                 │  │
│  │  GSI1PK: STACK#prod-stack-001#SHARD#1                                 │  │
│  │  GSI1PK: STACK#prod-stack-001#SHARD#2                                 │  │
│  │  ... (10 shards)                                                      │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  Solution 3: GSI Projection Optimization                                    │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Only project essential attributes to GSI                             │  │
│  │  - Reduces write amplification                                        │  │
│  │  - Reduces storage costs                                              │  │
│  │  - Improves write performance                                         │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Compliance & Audit Trail

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    AUDIT TRAIL STRUCTURE                                    │
│                                                                              │
│  Review: REVIEW#abc123                                                      │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Version 1                                                            │  │
│  │  - Created: 2024-01-15T10:30:00Z                                     │  │
│  │  - CreatedBy: system@spacelift                                       │  │
│  │  - Status: pending → completed                                       │  │
│  │  - RiskScore: 0.72                                                   │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                            │                                                 │
│                            │ PreviousVersionId                              │
│                            ▼                                                 │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Version 2                                                            │  │
│  │  - Created: 2024-01-15T10:31:00Z                                     │  │
│  │  - CreatedBy: system@spacelift                                       │  │
│  │  - Status: completed                                                 │  │
│  │  - RiskScore: 0.72                                                   │  │
│  │  - Changes: None (status update only)                                 │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                            │                                                 │
│                            │ PreviousVersionId                              │
│                            ▼                                                 │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Version 3                                                            │  │
│  │  - Created: 2024-01-16T10:30:00Z                                     │  │
│  │  - CreatedBy: user@example.com                                       │  │
│  │  - Status: completed                                                 │  │
│  │  - RiskScore: 0.35 (reduced from 0.72)                               │  │
│  │  - Changes: Fix applied, 2 findings resolved                         │  │
│  │  - FixDetails: {...}                                                 │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  Complete immutable history for compliance                                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Query Performance Characteristics

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    QUERY PERFORMANCE                                         │
│                                                                              │
│  Operation Type          | Latency    | Use Case                            │
│  ────────────────────────────────────────────────────────────────────────   │
│  GetItem (by PK/SK)     | < 10ms     | Get specific version                │
│  Query (by PK)           | < 50ms     | Get all versions                   │
│  Query (GSI1)            | < 100ms    | Stack history                       │
│  Query (GSI2)            | < 100ms    | Risk trends                        │
│  Query (GSI3)            | < 100ms    | Repeated issues                     │
│  Query (GSI4)            | < 100ms    | Status queries                      │
│  BatchGetItem            | < 200ms    | Multiple reviews                    │
│  BatchWriteItem          | < 200ms    | Bulk operations                    │
│  ────────────────────────────────────────────────────────────────────────   │
│                                                                              │
│  Scalability:                                                            │
│  - Supports millions of reviews                                            │
│  - Auto-scaling with on-demand mode                                        │
│  - No hot partition issues with proper sharding                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

