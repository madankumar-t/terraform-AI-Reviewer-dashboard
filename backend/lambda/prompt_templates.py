"""
Prompt Template Management

Centralized prompt templates with versioning support.
Allows for prompt A/B testing and rollback capabilities.
"""

from typing import Dict, Any
from datetime import datetime
import json


class PromptTemplates:
    """Manage prompt templates with versioning"""
    
    # Current prompt versions
    VERSIONS = {
        'pr_review': 'v2.1',
        'failure_analysis': 'v1.3',
        'fix_effectiveness': 'v1.0'
    }
    
    @staticmethod
    def get_pr_review_prompt(
        terraform_code: str,
        spacelift_context: Dict[str, Any] = None,
        version: str = 'v2.1'
    ) -> str:
        """Get PR review prompt for specified version"""
        spacelift_context = spacelift_context or {}
        
        if version == 'v2.1':
            return PromptTemplates._pr_review_v2_1(terraform_code, spacelift_context)
        elif version == 'v2.0':
            return PromptTemplates._pr_review_v2_0(terraform_code, spacelift_context)
        elif version == 'v1.0':
            return PromptTemplates._pr_review_v1_0(terraform_code, spacelift_context)
        else:
            raise ValueError(f"Unknown PR review prompt version: {version}")
    
    @staticmethod
    def _pr_review_v2_1(terraform_code: str, spacelift_context: Dict[str, Any]) -> str:
        """PR review prompt v2.1 - Enhanced with context awareness"""
        context_info = ""
        if spacelift_context:
            context_info = f"""
Spacelift Run Context:
- Run ID: {spacelift_context.get('run_id', 'N/A')}
- Stack: {spacelift_context.get('stack_id', 'N/A')}
- Previous Run Status: {spacelift_context.get('previous_status', 'N/A')}
- Changed Files: {', '.join(spacelift_context.get('changed_files', []))}
- Commit SHA: {spacelift_context.get('commit_sha', 'N/A')}
- Branch: {spacelift_context.get('branch', 'N/A')}
- Previous Risk Score: {spacelift_context.get('previous_risk_score', 'N/A')}
"""
        
        return f"""You are an expert AWS and Terraform security, cost, and reliability analyst.

Analyze the following Terraform code comprehensively.

{context_info}

Terraform Code:
```hcl
{terraform_code}
```

Provide your analysis in the following EXACT JSON format (no markdown, no code blocks, just pure JSON):
{{
  "security_analysis": {{
    "total_findings": 0,
    "high_severity": 0,
    "medium_severity": 0,
    "low_severity": 0,
    "findings": [
      {{
        "finding_id": "sec-001",
        "category": "security",
        "severity": "high|medium|low",
        "title": "Brief descriptive title",
        "description": "Detailed description of the issue, including why it's a problem",
        "line_number": 10,
        "file_path": "main.tf",
        "recommendation": "Specific, actionable recommendation with code examples if applicable",
        "confidence_score": 0.95
      }}
    ]
  }},
  "cost_analysis": {{
    "estimated_monthly_cost": 0.0,
    "estimated_annual_cost": 0.0,
    "resource_count": 0,
    "cost_optimizations": [
      {{
        "finding_id": "cost-001",
        "category": "cost",
        "severity": "high|medium|low",
        "title": "Cost optimization opportunity",
        "description": "Description of cost issue",
        "recommendation": "Recommendation to reduce costs",
        "estimated_cost_impact": 100.0,
        "confidence_score": 0.9
      }}
    ]
  }},
  "reliability_analysis": {{
    "reliability_score": 0.85,
    "single_points_of_failure": [
      {{
        "finding_id": "rel-001",
        "category": "reliability",
        "severity": "high|medium|low",
        "title": "Single point of failure identified",
        "description": "Description of reliability issue",
        "recommendation": "Recommendation to improve reliability",
        "confidence_score": 0.9
      }}
    ],
    "recommendations": ["General reliability recommendation 1", "Recommendation 2"]
  }},
  "overall_risk_score": 0.5,
  "fix_suggestions": [
    {{
      "fix_id": "fix-001",
      "finding_id": "sec-001",
      "original_code": "resource \"aws_s3_bucket\" \"example\" {{\n  bucket = \"my-bucket\"\n}}",
      "suggested_code": "resource \"aws_s3_bucket\" \"example\" {{\n  bucket = \"my-bucket\"\n}}\n\nresource \"aws_s3_bucket_public_access_block\" \"example\" {{\n  bucket = aws_s3_bucket.example.id\n  block_public_acls = true\n  block_public_policy = true\n  ignore_public_acls = true\n  restrict_public_buckets = true\n}}",
      "explanation": "Detailed explanation of why this fix works and what it addresses",
      "effectiveness_score": 0.95
    }}
  ],
  "review_metadata": {{
    "model_used": "claude-3-5-sonnet",
    "review_timestamp": "{datetime.utcnow().isoformat()}",
    "code_length": {len(terraform_code)},
    "prompt_version": "v2.1"
  }}
}}

Analysis Guidelines:
1. Security: Focus on exposed credentials, missing encryption, overly permissive IAM policies, public resources, missing security groups, etc.
2. Cost: Identify over-provisioned resources, missing auto-scaling, expensive instance types, unused resources, missing reserved instances, etc.
3. Reliability: Find single points of failure, missing backups, no health checks, tight coupling, missing disaster recovery, etc.

Be thorough, specific, and actionable. Include line numbers when possible. Return ONLY valid JSON, no additional text."""
    
    @staticmethod
    def _pr_review_v2_0(terraform_code: str, spacelift_context: Dict[str, Any]) -> str:
        """PR review prompt v2.0 - Previous version for rollback"""
        # Similar to v2.1 but without previous_risk_score in context
        context_info = ""
        if spacelift_context:
            context_info = f"""
Spacelift Run Context:
- Run ID: {spacelift_context.get('run_id', 'N/A')}
- Stack: {spacelift_context.get('stack_id', 'N/A')}
- Previous Run Status: {spacelift_context.get('previous_status', 'N/A')}
- Changed Files: {', '.join(spacelift_context.get('changed_files', []))}
"""
        # ... (similar structure to v2.1)
        return PromptTemplates._pr_review_v2_1(terraform_code, spacelift_context)
    
    @staticmethod
    def _pr_review_v1_0(terraform_code: str, spacelift_context: Dict[str, Any]) -> str:
        """PR review prompt v1.0 - Original version"""
        return f"""Analyze this Terraform code for security, cost, and reliability issues.

```hcl
{terraform_code}
```

Return JSON with security_analysis, cost_analysis, reliability_analysis, overall_risk_score, and fix_suggestions."""
    
    @staticmethod
    def get_failure_analysis_prompt(
        terraform_code: str,
        error_details: Dict[str, Any],
        previous_review: Dict[str, Any] = None,
        version: str = 'v1.3'
    ) -> str:
        """Get failure analysis prompt for specified version"""
        if version == 'v1.3':
            return PromptTemplates._failure_analysis_v1_3(terraform_code, error_details, previous_review)
        elif version == 'v1.0':
            return PromptTemplates._failure_analysis_v1_0(terraform_code, error_details, previous_review)
        else:
            raise ValueError(f"Unknown failure analysis prompt version: {version}")
    
    @staticmethod
    def _failure_analysis_v1_3(
        terraform_code: str,
        error_details: Dict[str, Any],
        previous_review: Dict[str, Any] = None
    ) -> str:
        """Failure analysis prompt v1.3 - Enhanced with correlation"""
        previous_context = ""
        if previous_review:
            prev_risk = previous_review.get('ai_review_result', {}).get('overall_risk_score', 'N/A')
            prev_findings = previous_review.get('ai_review_result', {}).get('security_analysis', {}).get('total_findings', 'N/A')
            previous_context = f"""
Previous Review Context:
- Previous Risk Score: {prev_risk}
- Previous Security Findings: {prev_findings}
- Previous Status: {previous_review.get('status', 'N/A')}
"""
        
        return f"""Analyze the following Terraform code failure and provide root cause analysis.

Terraform Code:
```hcl
{terraform_code}
```

Error Details:
- Error Type: {error_details.get('error_type', 'Unknown')}
- Error Message: {error_details.get('error_message', 'N/A')}
- Error Code: {error_details.get('error_code', 'N/A')}
- Stack Trace: {error_details.get('stack_trace', 'N/A')[:1000]}

{previous_context}

Provide your analysis in the following EXACT JSON format:
{{
  "root_cause": "Primary cause of the failure",
  "contributing_factors": ["Factor 1", "Factor 2", "Factor 3"],
  "severity": "high|medium|low",
  "recommendations": [
    {{
      "priority": "high|medium|low",
      "action": "Specific, actionable step to resolve",
      "explanation": "Why this action will help"
    }}
  ],
  "related_findings": [
    {{
      "finding_id": "finding-id",
      "category": "security|cost|reliability",
      "title": "Related finding title",
      "description": "How this finding relates to the failure"
    }}
  ],
  "prevention_strategies": ["Strategy 1", "Strategy 2"],
  "confidence_score": 0.9,
  "analysis_metadata": {{
    "model_used": "claude-3-5-sonnet",
    "analysis_timestamp": "{datetime.utcnow().isoformat()}",
    "prompt_version": "v1.3"
  }}
}}

Focus on:
- Root cause analysis (not just symptoms)
- Correlation with previous reviews if available
- Actionable recommendations
- Prevention strategies

Return ONLY valid JSON."""
    
    @staticmethod
    def _failure_analysis_v1_0(
        terraform_code: str,
        error_details: Dict[str, Any],
        previous_review: Dict[str, Any] = None
    ) -> str:
        """Failure analysis prompt v1.0 - Original version"""
        return f"""Analyze this Terraform failure:

Code:
{terraform_code}

Error: {error_details.get('error_message', 'N/A')}

Return JSON with root_cause, recommendations, and severity."""
    
    @staticmethod
    def get_fix_effectiveness_prompt(
        original_code: str,
        fixed_code: str,
        original_findings: List[Dict[str, Any]],
        fixed_findings: List[Dict[str, Any]],
        version: str = 'v1.0'
    ) -> str:
        """Get fix effectiveness prompt for specified version"""
        if version == 'v1.0':
            return PromptTemplates._fix_effectiveness_v1_0(
                original_code, fixed_code, original_findings, fixed_findings
            )
        else:
            raise ValueError(f"Unknown fix effectiveness prompt version: {version}")
    
    @staticmethod
    def _fix_effectiveness_v1_0(
        original_code: str,
        fixed_code: str,
        original_findings: List[Dict[str, Any]],
        fixed_findings: List[Dict[str, Any]]
    ) -> str:
        """Fix effectiveness prompt v1.0"""
        return f"""Compare the effectiveness of fixes applied to Terraform code.

Original Code:
```hcl
{original_code}
```

Fixed Code:
```hcl
{fixed_code}
```

Original Findings ({len(original_findings)}):
{json.dumps(original_findings[:10], indent=2)}

Fixed Findings ({len(fixed_findings)}):
{json.dumps(fixed_findings[:10], indent=2)}

Provide your analysis in the following EXACT JSON format:
{{
  "fix_effectiveness_score": 0.85,
  "findings_resolved": {{
    "total": 3,
    "security": 2,
    "cost": 1,
    "reliability": 0
  }},
  "findings_remaining": {{
    "total": 1,
    "security": 0,
    "cost": 1,
    "reliability": 0
  }},
  "risk_reduction": {{
    "before": 0.72,
    "after": 0.35,
    "reduction_percentage": 51.4
  }},
  "fix_analysis": [
    {{
      "finding_id": "finding-id",
      "fix_applied": true,
      "effectiveness": 0.95,
      "explanation": "Why this fix was effective or not"
    }}
  ],
  "remaining_issues": [
    {{
      "finding_id": "finding-id",
      "severity": "medium",
      "reason_not_fixed": "Fix not applied or incomplete"
    }}
  ],
  "recommendations": ["Additional recommendation 1", "Recommendation 2"],
  "confidence_score": 0.9,
  "analysis_metadata": {{
    "model_used": "claude-3-5-sonnet",
    "analysis_timestamp": "{datetime.utcnow().isoformat()}",
    "prompt_version": "v1.0"
  }}
}}

Analyze:
- Which findings were resolved
- Effectiveness of each fix
- Remaining issues and why they weren't fixed
- Overall risk reduction

Return ONLY valid JSON."""


class PromptVersionManager:
    """Manage prompt versions and A/B testing"""
    
    @staticmethod
    def get_current_version(prompt_type: str) -> str:
        """Get current version for prompt type"""
        return PromptTemplates.VERSIONS.get(prompt_type, 'v1.0')
    
    @staticmethod
    def list_versions(prompt_type: str) -> List[str]:
        """List available versions for prompt type"""
        if prompt_type == 'pr_review':
            return ['v2.1', 'v2.0', 'v1.0']
        elif prompt_type == 'failure_analysis':
            return ['v1.3', 'v1.0']
        elif prompt_type == 'fix_effectiveness':
            return ['v1.0']
        else:
            return []
    
    @staticmethod
    def rollback_version(prompt_type: str, target_version: str) -> bool:
        """Rollback to previous version (for testing)"""
        available = PromptVersionManager.list_versions(prompt_type)
        if target_version in available:
            PromptTemplates.VERSIONS[prompt_type] = target_version
            return True
        return False

