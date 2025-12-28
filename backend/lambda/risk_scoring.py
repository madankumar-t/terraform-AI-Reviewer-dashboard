"""
Risk Scoring Algorithm

Deterministic risk scoring based on security, cost, and reliability findings.
"""

from typing import Dict, Any, List
from models import SecurityAnalysis, CostAnalysis, ReliabilityAnalysis, Finding


class RiskScoringAlgorithm:
    """
    Deterministic risk scoring algorithm.
    
    Algorithm:
    - Security: 50% weight (most critical)
    - Cost: 25% weight
    - Reliability: 25% weight
    
    Each category score is normalized 0-1 based on findings and severity.
    """
    
    # Severity weights
    SEVERITY_WEIGHTS = {
        'high': 1.0,
        'medium': 0.5,
        'low': 0.2
    }
    
    # Category weights for overall risk
    CATEGORY_WEIGHTS = {
        'security': 0.50,
        'cost': 0.25,
        'reliability': 0.25
    }
    
    @staticmethod
    def calculate_overall_risk(
        security: SecurityAnalysis,
        cost: CostAnalysis,
        reliability: ReliabilityAnalysis
    ) -> float:
        """
        Calculate overall risk score (0.0 to 1.0).
        
        Args:
            security: Security analysis results
            cost: Cost analysis results
            reliability: Reliability analysis results
            
        Returns:
            Overall risk score between 0.0 and 1.0
        """
        security_score = RiskScoringAlgorithm._calculate_security_score(security)
        cost_score = RiskScoringAlgorithm._calculate_cost_score(cost)
        reliability_score = RiskScoringAlgorithm._calculate_reliability_score(reliability)
        
        # Weighted combination
        overall_risk = (
            security_score * RiskScoringAlgorithm.CATEGORY_WEIGHTS['security'] +
            cost_score * RiskScoringAlgorithm.CATEGORY_WEIGHTS['cost'] +
            reliability_score * RiskScoringAlgorithm.CATEGORY_WEIGHTS['reliability']
        )
        
        return min(1.0, max(0.0, overall_risk))
    
    @staticmethod
    def _calculate_security_score(security: SecurityAnalysis) -> float:
        """Calculate security risk score (0.0 to 1.0)"""
        if security.total_findings == 0:
            return 0.0
        
        # Weighted severity calculation
        weighted_score = (
            security.high_severity * RiskScoringAlgorithm.SEVERITY_WEIGHTS['high'] +
            security.medium_severity * RiskScoringAlgorithm.SEVERITY_WEIGHTS['medium'] +
            security.low_severity * RiskScoringAlgorithm.SEVERITY_WEIGHTS['low']
        )
        
        # Normalize by total findings (max 10 findings = 1.0)
        normalized = min(1.0, weighted_score / 10.0)
        
        # Apply exponential curve for high-severity findings
        if security.high_severity > 0:
            normalized = min(1.0, normalized * 1.5)
        
        return normalized
    
    @staticmethod
    def _calculate_cost_score(cost: CostAnalysis) -> float:
        """Calculate cost risk score (0.0 to 1.0)"""
        # Base score from monthly cost
        # Normalize: $10k/month = 1.0
        cost_base = min(1.0, cost.estimated_monthly_cost / 10000.0)
        
        # Adjust based on optimization opportunities
        optimization_count = len(cost.cost_optimizations)
        optimization_score = min(0.5, optimization_count * 0.1)
        
        # Combine: high cost + optimization opportunities = higher risk
        return min(1.0, cost_base + optimization_score)
    
    @staticmethod
    def _calculate_reliability_score(reliability: ReliabilityAnalysis) -> float:
        """Calculate reliability risk score (0.0 to 1.0)"""
        # Inverse: lower reliability = higher risk
        base_risk = 1.0 - reliability.reliability_score
        
        # Adjust for single points of failure
        spof_count = len(reliability.single_points_of_failure)
        spof_adjustment = min(0.3, spof_count * 0.1)
        
        return min(1.0, base_risk + spof_adjustment)
    
    @staticmethod
    def calculate_finding_risk(finding: Finding) -> float:
        """Calculate individual finding risk score"""
        severity_weight = RiskScoringAlgorithm.SEVERITY_WEIGHTS.get(
            finding.severity.value if hasattr(finding.severity, 'value') else finding.severity,
            0.5
        )
        
        # Adjust by confidence
        confidence_adjustment = finding.confidence_score
        
        return severity_weight * confidence_adjustment
    
    @staticmethod
    def calculate_category_risk(findings: List[Finding], category: str) -> float:
        """Calculate risk score for a specific category"""
        if not findings:
            return 0.0
        
        category_findings = [f for f in findings if f.category == category]
        if not category_findings:
            return 0.0
        
        total_risk = sum(
            RiskScoringAlgorithm.calculate_finding_risk(f)
            for f in category_findings
        )
        
        # Normalize by count
        return min(1.0, total_risk / max(1, len(category_findings)))
    
    @staticmethod
    def get_risk_level(risk_score: float) -> str:
        """Get risk level category from score"""
        if risk_score >= 0.7:
            return 'high'
        elif risk_score >= 0.4:
            return 'medium'
        else:
            return 'low'


class ConfidenceScoringAlgorithm:
    """
    Confidence scoring algorithm for AI findings.
    
    Factors:
    - Model quality
    - Finding specificity (line numbers, file paths)
    - Consistency across models
    - Historical accuracy
    """
    
    MODEL_CONFIDENCE_BASE = {
        'claude-3-5-sonnet': 0.95,
        'claude-3-opus': 0.98,
        'llama3-70b': 0.85,
        'default': 0.80
    }
    
    @staticmethod
    def calculate_finding_confidence(
        finding: Finding,
        model_used: str,
        has_line_number: bool = False,
        has_file_path: bool = False
    ) -> float:
        """
        Calculate confidence score for a finding.
        
        Args:
            finding: The finding to score
            model_used: Model that generated the finding
            has_line_number: Whether finding has line number
            has_file_path: Whether finding has file path
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        # Base confidence from model
        base_confidence = ConfidenceScoringAlgorithm.MODEL_CONFIDENCE_BASE.get(
            model_used.lower(),
            ConfidenceScoringAlgorithm.MODEL_CONFIDENCE_BASE['default']
        )
        
        # Specificity bonus
        specificity_bonus = 0.0
        if has_line_number:
            specificity_bonus += 0.03
        if has_file_path:
            specificity_bonus += 0.02
        
        # Severity adjustment (higher severity = more confidence needed)
        severity_adjustment = {
            'high': 0.0,  # No adjustment
            'medium': -0.02,  # Slight reduction
            'low': -0.05  # More reduction
        }.get(
            finding.severity.value if hasattr(finding.severity, 'value') else finding.severity,
            0.0
        )
        
        confidence = base_confidence + specificity_bonus + severity_adjustment
        
        return min(1.0, max(0.0, confidence))
    
    @staticmethod
    def calculate_overall_confidence(
        findings: List[Finding],
        model_used: str
    ) -> float:
        """Calculate overall confidence for a review"""
        if not findings:
            return 0.0
        
        confidences = [
            ConfidenceScoringAlgorithm.calculate_finding_confidence(
                f,
                model_used,
                has_line_number=f.line_number is not None,
                has_file_path=f.file_path is not None
            )
            for f in findings
        ]
        
        # Average confidence, weighted by severity
        weighted_sum = sum(
            conf * RiskScoringAlgorithm.SEVERITY_WEIGHTS.get(
                f.severity.value if hasattr(f.severity, 'value') else f.severity,
                0.5
            )
            for conf, f in zip(confidences, findings)
        )
        
        total_weight = sum(
            RiskScoringAlgorithm.SEVERITY_WEIGHTS.get(
                f.severity.value if hasattr(f.severity, 'value') else f.severity,
                0.5
            )
            for f in findings
        )
        
        return weighted_sum / max(1, total_weight)
    
    @staticmethod
    def adjust_confidence_by_consistency(
        base_confidence: float,
        consistency_score: float
    ) -> float:
        """
        Adjust confidence based on consistency across models.
        
        Args:
            base_confidence: Base confidence score
            consistency_score: Consistency score (0.0 to 1.0)
            
        Returns:
            Adjusted confidence score
        """
        # Consistency bonus: if multiple models agree, increase confidence
        consistency_bonus = (consistency_score - 0.5) * 0.1
        
        return min(1.0, max(0.0, base_confidence + consistency_bonus))

