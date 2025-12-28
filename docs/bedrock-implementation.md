# AWS Bedrock AI Evaluation Engine Implementation

## Overview

This document describes the complete AWS Bedrock implementation for the Terraform + Spacelift AI Reviewer system, including model selection, prompt templates, deterministic JSON enforcement, risk scoring, and confidence scoring.

## Model Selection Rationale

### Primary Model: Claude 3.5 Sonnet

**Model ID**: `anthropic.claude-3-5-sonnet-20241022-v2:0`

**Rationale**:
- **Best JSON Output**: Excellent at following structured output requirements
- **Security Analysis**: Strong performance on security-related tasks
- **Cost-Effective**: Good balance of quality and cost
- **Token Limit**: 4096 tokens (sufficient for most reviews)
- **Temperature**: 0.1 (deterministic output)

**Use Cases**:
- Primary model for all review types
- Best for structured JSON output
- Recommended for production

### Fallback Model 1: Claude 3 Opus

**Model ID**: `anthropic.claude-3-opus-20240229-v1:0`

**Rationale**:
- **Highest Quality**: Best overall performance
- **Complex Analysis**: Excellent for complex codebases
- **Fallback**: Used when Sonnet fails
- **Cost**: Higher cost, but better quality

**Use Cases**:
- Fallback for complex reviews
- High-stakes analysis
- When Sonnet produces low confidence

### Fallback Model 2: Llama 3 70B

**Model ID**: `meta.llama3-70b-instruct-v1:0`

**Rationale**:
- **Cost-Effective**: Lower cost than Claude models
- **Good Performance**: Solid performance for standard reviews
- **Availability**: Good availability during high load
- **Token Limit**: 2048 tokens (sufficient for most cases)

**Use Cases**:
- Cost-sensitive scenarios
- High-volume processing
- Final fallback option

## Prompt Templates

### 1. PR Review Prompt (v2.1)

**Purpose**: Comprehensive Terraform code review

**Key Features**:
- Context-aware (Spacelift run information)
- Structured JSON output
- Security, cost, and reliability focus
- Line number and file path tracking

**Template Structure**:
```
You are an expert AWS and Terraform analyst.

Analyze the following Terraform code.

[Spacelift Context if available]

Terraform Code:
```hcl
{code}
```

Provide analysis in EXACT JSON format:
{
  "security_analysis": {...},
  "cost_analysis": {...},
  "reliability_analysis": {...},
  "overall_risk_score": 0.5,
  "fix_suggestions": [...]
}
```

**Version History**:
- v2.1: Current (enhanced context awareness)
- v2.0: Previous (basic context)
- v1.0: Original (minimal context)

### 2. Failure Analysis Prompt (v1.3)

**Purpose**: Analyze failed Spacelift runs

**Key Features**:
- Root cause analysis
- Correlation with previous reviews
- Actionable recommendations
- Prevention strategies

**Template Structure**:
```
Analyze the following Terraform code failure.

[Error Details]
[Previous Review Context if available]

Provide analysis in EXACT JSON format:
{
  "root_cause": "...",
  "contributing_factors": [...],
  "recommendations": [...],
  "related_findings": [...]
}
```

**Version History**:
- v1.3: Current (enhanced correlation)
- v1.0: Original (basic analysis)

### 3. Fix Effectiveness Prompt (v1.0)

**Purpose**: Compare original vs fixed code

**Key Features**:
- Effectiveness scoring
- Findings resolution tracking
- Risk reduction calculation
- Remaining issues identification

**Template Structure**:
```
Compare the effectiveness of fixes.

[Original Code]
[Fixed Code]
[Original Findings]
[Fixed Findings]

Provide analysis in EXACT JSON format:
{
  "fix_effectiveness_score": 0.85,
  "findings_resolved": {...},
  "risk_reduction": {...}
}
```

## Deterministic JSON Schema Enforcement

### Schema Validation

**Three-Level Validation**:

1. **JSON Parsing**: Extract and parse JSON from response
2. **Schema Validation**: Validate against expected structure
3. **Type Checking**: Ensure correct data types

**Implementation**:
```python
def _parse_and_validate_json(self, text: str, prompt_type: str) -> Dict[str, Any]:
    # Extract JSON (handle markdown code blocks)
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    json_text = json_match.group() if json_match else text
    
    # Parse JSON
    parsed = json.loads(json_text)
    
    # Validate schema
    self._validate_schema(parsed, prompt_type)
    
    return parsed
```

### Required Schema Fields

**PR Review Schema**:
- `security_analysis` (object)
  - `total_findings` (integer)
  - `high_severity` (integer)
  - `findings` (array)
- `cost_analysis` (object)
  - `estimated_monthly_cost` (float)
  - `cost_optimizations` (array)
- `reliability_analysis` (object)
  - `reliability_score` (float, 0.0-1.0)
  - `single_points_of_failure` (array)
- `overall_risk_score` (float, 0.0-1.0)
- `fix_suggestions` (array)

### Error Handling

**Invalid JSON**:
- Log error with response snippet
- Try next model in fallback chain
- Return fallback result if all models fail

**Schema Validation Failure**:
- Identify missing/invalid fields
- Log validation errors
- Attempt to fix common issues
- Fallback to next model

## Risk Scoring Algorithm

### Algorithm Overview

**Weighted Combination**:
- Security: 50% weight
- Cost: 25% weight
- Reliability: 25% weight

**Formula**:
```
overall_risk = (
    security_score * 0.50 +
    cost_score * 0.25 +
    reliability_score * 0.25
)
```

### Security Score Calculation

**Method**:
1. Weight findings by severity:
   - High: 1.0
   - Medium: 0.5
   - Low: 0.2
2. Normalize by total findings (max 10 = 1.0)
3. Apply exponential curve for high-severity findings

**Formula**:
```
weighted_score = (
    high_severity * 1.0 +
    medium_severity * 0.5 +
    low_severity * 0.2
)
normalized = min(1.0, weighted_score / 10.0)
if high_severity > 0:
    normalized = min(1.0, normalized * 1.5)
```

### Cost Score Calculation

**Method**:
1. Base score from monthly cost ($10k/month = 1.0)
2. Add optimization opportunity score
3. Combine for final score

**Formula**:
```
cost_base = min(1.0, monthly_cost / 10000.0)
optimization_score = min(0.5, optimization_count * 0.1)
cost_score = min(1.0, cost_base + optimization_score)
```

### Reliability Score Calculation

**Method**:
1. Inverse of reliability score (lower reliability = higher risk)
2. Add single point of failure adjustment
3. Normalize to 0-1 range

**Formula**:
```
base_risk = 1.0 - reliability_score
spof_adjustment = min(0.3, spof_count * 0.1)
reliability_score = min(1.0, base_risk + spof_adjustment)
```

### Risk Level Categories

- **High**: risk_score >= 0.7
- **Medium**: 0.4 <= risk_score < 0.7
- **Low**: risk_score < 0.4

## Confidence Scoring

### Finding-Level Confidence

**Factors**:
1. Model quality (base confidence)
2. Finding specificity (line numbers, file paths)
3. Severity adjustment

**Model Base Confidence**:
- Claude 3 Opus: 0.98
- Claude 3.5 Sonnet: 0.95
- Llama 3 70B: 0.85
- Default: 0.80

**Specificity Bonuses**:
- Line number: +0.03
- File path: +0.02

**Severity Adjustments**:
- High: No adjustment
- Medium: -0.02
- Low: -0.05

**Formula**:
```
confidence = base_confidence + specificity_bonus + severity_adjustment
```

### Review-Level Confidence

**Method**:
1. Calculate confidence for each finding
2. Weight by severity
3. Average weighted confidences

**Formula**:
```
weighted_sum = sum(confidence * severity_weight for each finding)
total_weight = sum(severity_weight for each finding)
overall_confidence = weighted_sum / total_weight
```

### Consistency Adjustment

**Purpose**: Adjust confidence when multiple models agree

**Method**:
- Compare findings across models
- Calculate agreement percentage
- Apply consistency bonus/penalty

**Formula**:
```
consistency_bonus = (consistency_score - 0.5) * 0.1
adjusted_confidence = base_confidence + consistency_bonus
```

## Retry & Fallback Logic

### Retry Strategy

**Exponential Backoff**:
- Initial delay: 1 second
- Max retries: 3
- Backoff multiplier: 2

**Retry Conditions**:
- ThrottlingException
- ServiceUnavailableException
- Transient errors

**Implementation**:
```python
for attempt in range(max_retries):
    try:
        return invoke_model(...)
    except ThrottlingException:
        if attempt < max_retries - 1:
            time.sleep(backoff * (2 ** attempt))
            continue
        raise
```

### Fallback Chain

**Model Priority**:
1. Claude 3.5 Sonnet (primary)
2. Claude 3 Opus (high quality fallback)
3. Llama 3 70B (cost-effective fallback)

**Fallback Triggers**:
- Model invocation failure
- Invalid JSON response
- Schema validation failure
- Timeout

**Final Fallback**:
- Return minimal result with error indicator
- Log failure for investigation
- Allow manual review

## Prompt Versioning

### Version Management

**Current Versions**:
- PR Review: v2.1
- Failure Analysis: v1.3
- Fix Effectiveness: v1.0

**Version Storage**:
- In prompt template files
- In review metadata
- For A/B testing

### Rollback Capability

**Use Cases**:
- New version produces worse results
- Need to compare versions
- A/B testing

**Implementation**:
```python
# Rollback to previous version
PromptVersionManager.rollback_version('pr_review', 'v2.0')
```

### A/B Testing

**Strategy**:
- Deploy new version to subset of reviews
- Compare results
- Gradually roll out if successful

**Metrics**:
- Finding accuracy
- Risk score correlation
- User feedback

## Performance Characteristics

### Latency

- Claude 3.5 Sonnet: ~3-5 seconds
- Claude 3 Opus: ~5-8 seconds
- Llama 3 70B: ~2-4 seconds

### Throughput

- On-demand scaling
- No pre-provisioning needed
- Handles burst traffic

### Cost Optimization

- Use Sonnet for most reviews (cost-effective)
- Use Opus only when needed (higher quality)
- Use Llama for high-volume (lowest cost)

## Error Handling

### Model Errors

**Handling**:
- Log error details
- Try next model
- Return fallback result

### JSON Errors

**Handling**:
- Extract JSON from markdown
- Validate structure
- Fix common issues
- Fallback if unfixable

### Timeout Errors

**Handling**:
- Set appropriate timeouts
- Retry with shorter timeout
- Fallback to faster model

## Monitoring

### Metrics

- Model invocation count
- Success/failure rates
- Average latency
- Cost per review
- Confidence scores

### Alerts

- High failure rate
- Slow responses
- Cost anomalies
- Low confidence scores

## Best Practices

1. **Always validate JSON**: Never trust model output
2. **Use fallback chain**: Don't fail on first error
3. **Log everything**: For debugging and improvement
4. **Version prompts**: Enable rollback capability
5. **Monitor costs**: Track usage per model
6. **Test new versions**: A/B test before full rollout

## References

- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [Claude 3.5 Sonnet Guide](https://docs.anthropic.com/claude/docs)
- [Prompt Engineering Best Practices](https://docs.anthropic.com/claude/docs/prompt-engineering)

