"""
AWS Bedrock AI Service for Terraform Code Review

This module provides AI-powered code analysis using AWS Bedrock models.
Supports multiple models with fallback logic and deterministic JSON output.
"""

import json
import re
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from decimal import Decimal
import boto3
from botocore.exceptions import ClientError

from models import (
    AIReviewResult, SecurityAnalysis, CostAnalysis, ReliabilityAnalysis,
    Finding, FixSuggestion, RiskLevel
)
from risk_scoring import RiskScoringAlgorithm, ConfidenceScoringAlgorithm


class BedrockService:
    """
    AWS Bedrock service for AI-powered Terraform code review.
    
    Model Selection Rationale:
    - Claude 3.5 Sonnet: Best for structured JSON output, security analysis
    - Claude 3 Opus: Fallback for complex analysis, highest quality
    - Llama 3 70B: Cost-effective alternative, good for simple reviews
    """
    
    # Model priorities (best to fallback)
    MODELS = [
        {
            'id': 'anthropic.claude-3-5-sonnet-20241022-v2:0',
            'name': 'Claude 3.5 Sonnet',
            'max_tokens': 4096,
            'temperature': 0.1,  # Low temperature for deterministic output
            'use_case': 'primary'
        },
        {
            'id': 'anthropic.claude-3-opus-20240229-v1:0',
            'name': 'Claude 3 Opus',
            'max_tokens': 4096,
            'temperature': 0.1,
            'use_case': 'fallback_high_quality'
        },
        {
            'id': 'meta.llama3-70b-instruct-v1:0',
            'name': 'Llama 3 70B',
            'max_tokens': 2048,
            'temperature': 0.1,
            'use_case': 'fallback_cost_effective'
        }
    ]
    
    # Prompt versions for versioning and rollback
    PROMPT_VERSIONS = {
        'pr_review': 'v2.1',
        'failure_analysis': 'v1.3',
        'fix_effectiveness': 'v1.0'
    }
    
    def __init__(self, region: str = 'us-east-1'):
        """Initialize Bedrock client"""
        self.bedrock_runtime = boto3.client('bedrock-runtime', region_name=region)
        self.region = region
        
    def review_terraform(
        self,
        terraform_code: str,
        spacelift_context: Dict[str, Any] = None,
        prompt_type: str = 'pr_review'
    ) -> AIReviewResult:
        """
        Perform comprehensive AI review of Terraform code.
        
        Args:
            terraform_code: Terraform code to review
            spacelift_context: Optional Spacelift run context
            prompt_type: Type of prompt to use ('pr_review', 'failure_analysis', 'fix_effectiveness')
            
        Returns:
            AIReviewResult with analysis
        """
        spacelift_context = spacelift_context or {}
        
        # Get appropriate prompt template
        prompt = self._get_prompt_template(prompt_type, terraform_code, spacelift_context)
        
        # Try models in priority order
        for model_config in self.MODELS:
            try:
                result = self._invoke_model(model_config, prompt)
                parsed_result = self._parse_and_validate_json(result, prompt_type)
                
                # Build structured result
                return self._build_review_result(parsed_result, terraform_code, spacelift_context)
                
            except Exception as e:
                print(f"Model {model_config['name']} failed: {str(e)}")
                continue
        
        # All models failed, return fallback result
        return self._create_fallback_result()
    
    def analyze_failure(
        self,
        terraform_code: str,
        error_details: Dict[str, Any],
        previous_review: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze a failed Spacelift run.
        
        Args:
            terraform_code: Terraform code that failed
            error_details: Error information from Spacelift
            previous_review: Previous successful review (if any)
            
        Returns:
            Failure analysis with recommendations
        """
        prompt = self._get_failure_analysis_prompt(terraform_code, error_details, previous_review)
        
        for model_config in self.MODELS:
            try:
                result = self._invoke_model(model_config, prompt)
                parsed_result = self._parse_and_validate_json(result, 'failure_analysis')
                return parsed_result
            except Exception as e:
                print(f"Model {model_config['name']} failed: {str(e)}")
                continue
        
        return self._create_fallback_failure_analysis()
    
    def compare_fix_effectiveness(
        self,
        original_code: str,
        fixed_code: str,
        original_findings: List[Dict[str, Any]],
        fixed_findings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Compare fix effectiveness between original and fixed code.
        
        Args:
            original_code: Original Terraform code
            fixed_code: Fixed Terraform code
            original_findings: Findings from original review
            fixed_findings: Findings from fixed code review
            
        Returns:
            Fix effectiveness analysis
        """
        prompt = self._get_fix_effectiveness_prompt(
            original_code, fixed_code, original_findings, fixed_findings
        )
        
        for model_config in self.MODELS:
            try:
                result = self._invoke_model(model_config, prompt)
                parsed_result = self._parse_and_validate_json(result, 'fix_effectiveness')
                return parsed_result
            except Exception as e:
                print(f"Model {model_config['name']} failed: {str(e)}")
                continue
        
        return self._create_fallback_fix_analysis()
    
    def _invoke_model(self, model_config: Dict[str, Any], prompt: str) -> str:
        """Invoke Bedrock model with retry logic"""
        max_retries = 3
        backoff = 1
        
        for attempt in range(max_retries):
            try:
                if 'claude' in model_config['id'].lower():
                    return self._invoke_claude(model_config, prompt)
                elif 'llama' in model_config['id'].lower():
                    return self._invoke_llama(model_config, prompt)
                else:
                    raise ValueError(f"Unsupported model: {model_config['id']}")
                    
            except ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code == 'ThrottlingException' and attempt < max_retries - 1:
                    import time
                    time.sleep(backoff * (2 ** attempt))
                    continue
                raise
            except Exception as e:
                if attempt < max_retries - 1:
                    import time
                    time.sleep(backoff * (2 ** attempt))
                    continue
                raise
        
        raise Exception("All retry attempts failed")
    
    def _invoke_claude(self, model_config: Dict[str, Any], prompt: str) -> str:
        """Invoke Claude model via Bedrock"""
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": model_config['max_tokens'],
            "temperature": model_config['temperature'],
            "system": self._get_system_prompt(),
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        response = self.bedrock_runtime.invoke_model(
            modelId=model_config['id'],
            body=json.dumps(body),
            contentType='application/json',
            accept='application/json'
        )
        
        response_body = json.loads(response['body'].read())
        return response_body['content'][0]['text']
    
    def _invoke_llama(self, model_config: Dict[str, Any], prompt: str) -> str:
        """Invoke Llama model via Bedrock"""
        body = {
            "prompt": f"{self._get_system_prompt()}\n\n{prompt}",
            "max_gen_len": model_config['max_tokens'],
            "temperature": model_config['temperature']
        }
        
        response = self.bedrock_runtime.invoke_model(
            modelId=model_config['id'],
            body=json.dumps(body),
            contentType='application/json',
            accept='application/json'
        )
        
        response_body = json.loads(response['body'].read())
        return response_body['generation']
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for model"""
        return """You are an expert AWS and Terraform security, cost, and reliability analyst. 
Your responses must be valid JSON only, following the exact schema provided.
Be thorough, specific, and accurate in your analysis.
Always include line numbers when possible.
Provide actionable recommendations."""
    
    def _get_prompt_template(
        self,
        prompt_type: str,
        terraform_code: str,
        spacelift_context: Dict[str, Any]
    ) -> str:
        """Get prompt template based on type and version"""
        version = self.PROMPT_VERSIONS.get(prompt_type, 'v1.0')
        
        if prompt_type == 'pr_review':
            return self._get_pr_review_prompt(terraform_code, spacelift_context, version)
        elif prompt_type == 'failure_analysis':
            return self._get_failure_analysis_prompt(terraform_code, {}, None, version)
        elif prompt_type == 'fix_effectiveness':
            return self._get_fix_effectiveness_prompt('', '', [], [], version)
        else:
            raise ValueError(f"Unknown prompt type: {prompt_type}")
    
    def _get_pr_review_prompt(
        self,
        terraform_code: str,
        spacelift_context: Dict[str, Any],
        version: str
    ) -> str:
        """Get PR review prompt template"""
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
"""
        
        return f"""Analyze the following Terraform code for security, cost, and reliability issues.

{context_info}

Terraform Code:
```hcl
{terraform_code}
```

Provide a comprehensive analysis in the following EXACT JSON format (no markdown, no code blocks, just JSON):
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
    "model_used": "claude-3-5-sonnet",
    "review_timestamp": "{datetime.utcnow().isoformat()}",
    "code_length": {len(terraform_code)},
    "prompt_version": "{version}"
  }}
}}

Focus on:
1. Security: Exposed credentials, missing encryption, overly permissive IAM policies, public S3 buckets, etc.
2. Cost: Over-provisioned resources, missing auto-scaling, expensive instance types, unused resources
3. Reliability: Single points of failure, missing backups, no health checks, tight coupling

Be thorough and specific. Include line numbers when possible. Return ONLY valid JSON."""
    
    def _get_failure_analysis_prompt(
        self,
        terraform_code: str,
        error_details: Dict[str, Any],
        previous_review: Optional[Dict[str, Any]] = None,
        version: str = 'v1.3'
    ) -> str:
        """Get failure analysis prompt template"""
        previous_context = ""
        if previous_review:
            previous_context = f"""
Previous Review Context:
- Previous Risk Score: {previous_review.get('overall_risk_score', 'N/A')}
- Previous Findings: {len(previous_review.get('security_analysis', {}).get('findings', []))}
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
- Stack Trace: {error_details.get('stack_trace', 'N/A')[:500]}

{previous_context}

Provide analysis in the following EXACT JSON format:
{{
  "root_cause": "Primary cause of failure",
  "contributing_factors": ["Factor 1", "Factor 2"],
  "severity": "high|medium|low",
  "recommendations": [
    {{
      "priority": "high|medium|low",
      "action": "Specific action to take",
      "explanation": "Why this helps"
    }}
  ],
  "related_findings": [
    {{
      "finding_id": "finding-id",
      "category": "security|cost|reliability",
      "title": "Related finding",
      "description": "How this relates to the failure"
    }}
  ],
  "prevention_strategies": ["Strategy 1", "Strategy 2"],
  "confidence_score": 0.9,
  "analysis_metadata": {{
    "model_used": "claude-3-5-sonnet",
    "analysis_timestamp": "{datetime.utcnow().isoformat()}",
    "prompt_version": "{version}"
  }}
}}

Return ONLY valid JSON."""
    
    def _get_fix_effectiveness_prompt(
        self,
        original_code: str,
        fixed_code: str,
        original_findings: List[Dict[str, Any]],
        fixed_findings: List[Dict[str, Any]],
        version: str = 'v1.0'
    ) -> str:
        """Get fix effectiveness comparison prompt template"""
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
{json.dumps(original_findings[:5], indent=2)}

Fixed Findings ({len(fixed_findings)}):
{json.dumps(fixed_findings[:5], indent=2)}

Provide analysis in the following EXACT JSON format:
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
      "explanation": "Why this fix was effective"
    }}
  ],
  "remaining_issues": [
    {{
      "finding_id": "finding-id",
      "severity": "medium",
      "reason_not_fixed": "Fix not applied or incomplete"
    }}
  ],
  "recommendations": ["Additional recommendation 1"],
  "confidence_score": 0.9,
  "analysis_metadata": {{
    "model_used": "claude-3-5-sonnet",
    "analysis_timestamp": "{datetime.utcnow().isoformat()}",
    "prompt_version": "{version}"
  }}
}}

Return ONLY valid JSON."""
    
    def _parse_and_validate_json(self, text: str, prompt_type: str) -> Dict[str, Any]:
        """Parse and validate JSON response with strict schema validation"""
        # Extract JSON from response (handle markdown code blocks)
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            json_text = json_match.group()
        else:
            json_text = text
        
        try:
            parsed = json.loads(json_text)
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {str(e)}")
            print(f"Response text: {text[:500]}")
            raise ValueError(f"Invalid JSON response: {str(e)}")
        
        # Validate against schema
        self._validate_schema(parsed, prompt_type)
        
        return parsed
    
    def _validate_schema(self, data: Dict[str, Any], prompt_type: str) -> None:
        """Validate JSON against expected schema"""
        if prompt_type == 'pr_review':
            self._validate_pr_review_schema(data)
        elif prompt_type == 'failure_analysis':
            self._validate_failure_analysis_schema(data)
        elif prompt_type == 'fix_effectiveness':
            self._validate_fix_effectiveness_schema(data)
        else:
            raise ValueError(f"Unknown prompt type for validation: {prompt_type}")
    
    def _validate_pr_review_schema(self, data: Dict[str, Any]) -> None:
        """Validate PR review schema"""
        required_keys = [
            'security_analysis', 'cost_analysis', 'reliability_analysis',
            'overall_risk_score', 'fix_suggestions', 'review_metadata'
        ]
        
        for key in required_keys:
            if key not in data:
                raise ValueError(f"Missing required key: {key}")
        
        # Validate security_analysis
        sec = data['security_analysis']
        assert 'total_findings' in sec
        assert 'findings' in sec and isinstance(sec['findings'], list)
        
        # Validate cost_analysis
        cost = data['cost_analysis']
        assert 'estimated_monthly_cost' in cost
        assert isinstance(cost['estimated_monthly_cost'], (int, float))
        
        # Validate reliability_analysis
        rel = data['reliability_analysis']
        assert 'reliability_score' in rel
        assert 0.0 <= rel['reliability_score'] <= 1.0
        
        # Validate overall_risk_score
        assert 0.0 <= data['overall_risk_score'] <= 1.0
    
    def _validate_failure_analysis_schema(self, data: Dict[str, Any]) -> None:
        """Validate failure analysis schema"""
        required_keys = ['root_cause', 'recommendations', 'confidence_score']
        for key in required_keys:
            if key not in data:
                raise ValueError(f"Missing required key: {key}")
    
    def _validate_fix_effectiveness_schema(self, data: Dict[str, Any]) -> None:
        """Validate fix effectiveness schema"""
        required_keys = ['fix_effectiveness_score', 'findings_resolved', 'risk_reduction']
        for key in required_keys:
            if key not in data:
                raise ValueError(f"Missing required key: {key}")
    
    def _build_review_result(
        self,
        parsed_data: Dict[str, Any],
        terraform_code: str,
        spacelift_context: Dict[str, Any]
    ) -> AIReviewResult:
        """Build structured AIReviewResult from parsed JSON"""
        security_data = parsed_data.get('security_analysis', {})
        cost_data = parsed_data.get('cost_analysis', {})
        reliability_data = parsed_data.get('reliability_analysis', {})
        
        # Build security analysis
        security_analysis = SecurityAnalysis(
            total_findings=security_data.get('total_findings', 0),
            high_severity=security_data.get('high_severity', 0),
            medium_severity=security_data.get('medium_severity', 0),
            low_severity=security_data.get('low_severity', 0),
            findings=[
                Finding(**f) for f in security_data.get('findings', [])
            ]
        )
        
        # Build cost analysis
        cost_analysis = CostAnalysis(
            estimated_monthly_cost=cost_data.get('estimated_monthly_cost', 0.0),
            estimated_annual_cost=cost_data.get('estimated_annual_cost', 0.0),
            resource_count=cost_data.get('resource_count', 0),
            cost_optimizations=[
                Finding(**f) for f in cost_data.get('cost_optimizations', [])
            ]
        )
        
        # Build reliability analysis
        reliability_analysis = ReliabilityAnalysis(
            reliability_score=reliability_data.get('reliability_score', 0.5),
            single_points_of_failure=[
                Finding(**f) for f in reliability_data.get('single_points_of_failure', [])
            ],
            recommendations=reliability_data.get('recommendations', [])
        )
        
        # Calculate overall risk score if not provided or invalid
        overall_risk = parsed_data.get('overall_risk_score')
        if overall_risk is None or not (0.0 <= overall_risk <= 1.0):
            overall_risk = RiskScoringAlgorithm.calculate_overall_risk(
                security_analysis, cost_analysis, reliability_analysis
            )
        
        # Calculate and update confidence scores
        model_used = review_metadata.get('model_used', 'claude-3-5-sonnet')
        for finding in security_analysis.findings:
            finding.confidence_score = ConfidenceScoringAlgorithm.calculate_finding_confidence(
                finding,
                model_used,
                has_line_number=finding.line_number is not None,
                has_file_path=finding.file_path is not None
            )
        
        # Build fix suggestions
        fix_suggestions = [
            FixSuggestion(**f) for f in parsed_data.get('fix_suggestions', [])
        ]
        
        # Build metadata
        review_metadata = parsed_data.get('review_metadata', {})
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
        """Create fallback result when all models fail"""
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
    
    def _create_fallback_failure_analysis(self) -> Dict[str, Any]:
        """Create fallback failure analysis"""
        return {
            "root_cause": "Unable to analyze - AI service unavailable",
            "contributing_factors": [],
            "severity": "unknown",
            "recommendations": [
                {
                    "priority": "high",
                    "action": "Retry analysis or check AI service status",
                    "explanation": "AI service was unavailable during analysis"
                }
            ],
            "related_findings": [],
            "prevention_strategies": [],
            "confidence_score": 0.0,
            "analysis_metadata": {
                "error": "AI service unavailable",
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
        }
    
    def _create_fallback_fix_analysis(self) -> Dict[str, Any]:
        """Create fallback fix effectiveness analysis"""
        return {
            "fix_effectiveness_score": 0.0,
            "findings_resolved": {"total": 0, "security": 0, "cost": 0, "reliability": 0},
            "findings_remaining": {"total": 0, "security": 0, "cost": 0, "reliability": 0},
            "risk_reduction": {"before": 0.0, "after": 0.0, "reduction_percentage": 0.0},
            "fix_analysis": [],
            "remaining_issues": [],
            "recommendations": [],
            "confidence_score": 0.0,
            "analysis_metadata": {
                "error": "AI service unavailable",
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
        }

