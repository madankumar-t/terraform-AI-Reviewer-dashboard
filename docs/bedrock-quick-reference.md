# Bedrock AI Engine Quick Reference

## Model Selection

| Model | ID | Use Case | Cost | Quality |
|-------|-----|----------|------|---------|
| Claude 3.5 Sonnet | `anthropic.claude-3-5-sonnet-20241022-v2:0` | Primary | Medium | High |
| Claude 3 Opus | `anthropic.claude-3-opus-20240229-v1:0` | Fallback (High Quality) | High | Very High |
| Llama 3 70B | `meta.llama3-70b-instruct-v1:0` | Fallback (Cost-Effective) | Low | Good |

## Prompt Types

1. **PR Review** (`pr_review`)
   - Version: v2.1
   - Purpose: Comprehensive code review
   - Output: Security, cost, reliability analysis

2. **Failure Analysis** (`failure_analysis`)
   - Version: v1.3
   - Purpose: Analyze failed runs
   - Output: Root cause, recommendations

3. **Fix Effectiveness** (`fix_effectiveness`)
   - Version: v1.0
   - Purpose: Compare fixes
   - Output: Effectiveness score, risk reduction

## Risk Scoring

**Formula**:
```
overall_risk = (
    security_score * 0.50 +
    cost_score * 0.25 +
    reliability_score * 0.25
)
```

**Risk Levels**:
- High: >= 0.7
- Medium: 0.4 - 0.7
- Low: < 0.4

## Confidence Scoring

**Factors**:
- Model quality (base)
- Finding specificity (+0.03 for line number, +0.02 for file path)
- Severity adjustment (high: 0, medium: -0.02, low: -0.05)

**Base Confidence**:
- Claude 3 Opus: 0.98
- Claude 3.5 Sonnet: 0.95
- Llama 3 70B: 0.85

## Retry Logic

- Max retries: 3
- Backoff: Exponential (1s, 2s, 4s)
- Retry on: ThrottlingException, ServiceUnavailableException

## Fallback Chain

1. Try Claude 3.5 Sonnet
2. Try Claude 3 Opus
3. Try Llama 3 70B
4. Return fallback result

## JSON Schema Validation

**Required Fields**:
- `security_analysis` (object)
- `cost_analysis` (object)
- `reliability_analysis` (object)
- `overall_risk_score` (float, 0.0-1.0)
- `fix_suggestions` (array)

## Usage Example

```python
from bedrock_service import BedrockService

bedrock = BedrockService(region='us-east-1')

# PR Review
result = bedrock.review_terraform(
    terraform_code=code,
    spacelift_context=context,
    prompt_type='pr_review'
)

# Failure Analysis
analysis = bedrock.analyze_failure(
    terraform_code=code,
    error_details=error,
    previous_review=prev_review
)

# Fix Effectiveness
effectiveness = bedrock.compare_fix_effectiveness(
    original_code=original,
    fixed_code=fixed,
    original_findings=orig_findings,
    fixed_findings=fixed_findings
)
```

## Error Handling

- Invalid JSON: Try next model
- Schema validation failure: Try next model
- All models fail: Return fallback result
- Timeout: Retry with exponential backoff

## Monitoring

**Key Metrics**:
- Model invocation count
- Success/failure rates
- Average latency
- Cost per review
- Confidence scores

**Alerts**:
- High failure rate (> 5%)
- Slow responses (> 10s)
- Low confidence scores (< 0.7)

