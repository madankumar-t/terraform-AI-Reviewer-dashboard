import json
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
from models import (
    AIReviewResult, SecurityAnalysis, CostAnalysis, ReliabilityAnalysis,
    Finding, FixSuggestion, RiskLevel
)
from secrets_manager import SecretsManager

class AIService:
    def __init__(self, secrets_manager: SecretsManager):
        self.secrets_manager = secrets_manager
        self.openai_key = secrets_manager.get_openai_key()
        self.anthropic_key = secrets_manager.get_anthropic_key()
    
    def _call_openai(self, prompt: str, model: str = "gpt-4-turbo-preview") -> str:
        """Call OpenAI API"""
        try:
            import openai
            client = openai.OpenAI(api_key=self.openai_key)
            
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are an expert AWS and Terraform security, cost, and reliability analyst. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            return response.choices[0].message.content
        except Exception as e:
            print(f"OpenAI API error: {str(e)}")
            raise
    
    def _call_anthropic(self, prompt: str, model: str = "claude-3-5-sonnet-20241022") -> str:
        """Call Anthropic API"""
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.anthropic_key)
            
            response = client.messages.create(
                model=model,
                max_tokens=4096,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                system="You are an expert AWS and Terraform security, cost, and reliability analyst. Always respond with valid JSON only."
            )
            
            return response.content[0].text
        except Exception as e:
            print(f"Anthropic API error: {str(e)}")
            raise
    
    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Extract JSON from AI response"""
        # Try to find JSON in the response
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return json.loads(text)
    
    def review_terraform(self, terraform_code: str, spacelift_context: Dict[str, Any] = {}) -> AIReviewResult:
        """Perform comprehensive AI review of Terraform code"""
        
        # Build context-aware prompt
        context_info = ""
        if spacelift_context:
            context_info = f"""
Spacelift Run Context:
- Run ID: {spacelift_context.get('run_id', 'N/A')}
- Stack: {spacelift_context.get('stack_id', 'N/A')}
- Previous Run Status: {spacelift_context.get('previous_status', 'N/A')}
- Changed Files: {', '.join(spacelift_context.get('changed_files', []))}
"""
        
        prompt = f"""
Analyze the following Terraform code for security, cost, and reliability issues.

{context_info}

Terraform Code:
```hcl
{terraform_code}
```

Provide a comprehensive analysis in the following JSON format:
{{
  "security_analysis": {{
    "total_findings": 0,
    "high_severity": 0,
    "medium_severity": 0,
    "low_severity": 0,
    "findings": [
      {{
        "finding_id": "unique-id",
        "category": "security",
        "severity": "high|medium|low",
        "title": "Brief title",
        "description": "Detailed description",
        "line_number": 10,
        "file_path": "main.tf",
        "recommendation": "How to fix",
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
        "finding_id": "unique-id",
        "category": "cost",
        "severity": "high|medium|low",
        "title": "Cost optimization opportunity",
        "description": "Description",
        "recommendation": "Recommendation",
        "estimated_cost_impact": 100.0,
        "confidence_score": 0.9
      }}
    ]
  }},
  "reliability_analysis": {{
    "reliability_score": 0.85,
    "single_points_of_failure": [
      {{
        "finding_id": "unique-id",
        "category": "reliability",
        "severity": "high|medium|low",
        "title": "SPOF identified",
        "description": "Description",
        "recommendation": "Recommendation",
        "confidence_score": 0.9
      }}
    ],
    "recommendations": ["Recommendation 1", "Recommendation 2"]
  }},
  "overall_risk_score": 0.5,
  "fix_suggestions": [
    {{
      "fix_id": "unique-id",
      "finding_id": "finding-id",
      "original_code": "original code snippet",
      "suggested_code": "suggested code snippet",
      "explanation": "Why this fix works",
      "effectiveness_score": 0.9
    }}
  ],
  "review_metadata": {{
    "model_used": "gpt-4",
    "review_timestamp": "2024-01-01T00:00:00Z",
    "code_length": 1000
  }}
}}

Focus on:
1. Security: Exposed credentials, missing encryption, overly permissive IAM policies, public S3 buckets, etc.
2. Cost: Over-provisioned resources, missing auto-scaling, expensive instance types, unused resources
3. Reliability: Single points of failure, missing backups, no health checks, tight coupling

Be thorough and specific. Include line numbers when possible.
"""
        
        # Call AI service (prefer Anthropic, fallback to OpenAI)
        try:
            if self.anthropic_key:
                response_text = self._call_anthropic(prompt)
            elif self.openai_key:
                response_text = self._call_openai(prompt)
            else:
                raise ValueError("No AI API keys configured")
        except Exception as e:
            print(f"AI service error: {str(e)}")
            # Return minimal result on error
            return self._create_fallback_result()
        
        # Parse response
        try:
            result_data = self._extract_json(response_text)
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {str(e)}")
            print(f"Response was: {response_text[:500]}")
            return self._create_fallback_result()
        
        # Build structured result
        security_data = result_data.get('security_analysis', {})
        cost_data = result_data.get('cost_analysis', {})
        reliability_data = result_data.get('reliability_analysis', {})
        
        security_analysis = SecurityAnalysis(
            total_findings=security_data.get('total_findings', 0),
            high_severity=security_data.get('high_severity', 0),
            medium_severity=security_data.get('medium_severity', 0),
            low_severity=security_data.get('low_severity', 0),
            findings=[
                Finding(**f) for f in security_data.get('findings', [])
            ]
        )
        
        cost_analysis = CostAnalysis(
            estimated_monthly_cost=cost_data.get('estimated_monthly_cost', 0.0),
            estimated_annual_cost=cost_data.get('estimated_annual_cost', 0.0),
            resource_count=cost_data.get('resource_count', 0),
            cost_optimizations=[
                Finding(**f) for f in cost_data.get('cost_optimizations', [])
            ]
        )
        
        reliability_analysis = ReliabilityAnalysis(
            reliability_score=reliability_data.get('reliability_score', 0.5),
            single_points_of_failure=[
                Finding(**f) for f in reliability_data.get('single_points_of_failure', [])
            ],
            recommendations=reliability_data.get('recommendations', [])
        )
        
        fix_suggestions = [
            FixSuggestion(**f) for f in result_data.get('fix_suggestions', [])
        ]
        
        # Calculate overall risk score if not provided
        overall_risk = result_data.get('overall_risk_score')
        if overall_risk is None:
            # Calculate based on findings
            total_issues = (
                security_analysis.high_severity * 3 +
                security_analysis.medium_severity * 2 +
                security_analysis.low_severity +
                len(cost_analysis.cost_optimizations) +
                len(reliability_analysis.single_points_of_failure)
            )
            overall_risk = min(1.0, total_issues / 20.0)  # Normalize to 0-1
        
        review_metadata = result_data.get('review_metadata', {})
        review_metadata['code_length'] = len(terraform_code)
        review_metadata['review_timestamp'] = datetime.utcnow().isoformat()
        
        return AIReviewResult(
            review_id="",  # Will be set by caller
            security_analysis=security_analysis,
            cost_analysis=cost_analysis,
            reliability_analysis=reliability_analysis,
            overall_risk_score=overall_risk,
            fix_suggestions=fix_suggestions,
            review_metadata=review_metadata
        )
    
    def _create_fallback_result(self) -> AIReviewResult:
        """Create a fallback result when AI service fails"""
        return AIReviewResult(
            review_id="",
            security_analysis=SecurityAnalysis(
                total_findings=0,
                high_severity=0,
                medium_severity=0,
                low_severity=0,
                findings=[]
            ),
            cost_analysis=CostAnalysis(
                estimated_monthly_cost=0.0,
                estimated_annual_cost=0.0,
                resource_count=0,
                cost_optimizations=[]
            ),
            reliability_analysis=ReliabilityAnalysis(
                reliability_score=0.5,
                single_points_of_failure=[],
                recommendations=["Unable to complete analysis - AI service unavailable"]
            ),
            overall_risk_score=0.5,
            fix_suggestions=[],
            review_metadata={
                "error": "AI service unavailable",
                "review_timestamp": datetime.utcnow().isoformat()
            }
        )

