from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class ReviewStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class Finding(BaseModel):
    finding_id: str
    category: str  # security, cost, reliability
    severity: RiskLevel
    title: str
    description: str
    line_number: Optional[int] = None
    file_path: Optional[str] = None
    recommendation: str
    estimated_cost_impact: Optional[float] = None
    confidence_score: float = Field(ge=0.0, le=1.0)

class FixSuggestion(BaseModel):
    fix_id: str
    finding_id: str
    original_code: str
    suggested_code: str
    explanation: str
    effectiveness_score: Optional[float] = Field(None, ge=0.0, le=1.0)

class SecurityAnalysis(BaseModel):
    total_findings: int
    high_severity: int
    medium_severity: int
    low_severity: int
    findings: List[Finding]

class CostAnalysis(BaseModel):
    estimated_monthly_cost: float
    estimated_annual_cost: float
    cost_optimizations: List[Finding]
    resource_count: int

class ReliabilityAnalysis(BaseModel):
    reliability_score: float = Field(ge=0.0, le=1.0)
    single_points_of_failure: List[Finding]
    recommendations: List[str]

class AIReviewResult(BaseModel):
    review_id: str
    security_analysis: SecurityAnalysis
    cost_analysis: CostAnalysis
    reliability_analysis: ReliabilityAnalysis
    overall_risk_score: float = Field(ge=0.0, le=1.0)
    fix_suggestions: List[FixSuggestion]
    review_metadata: Dict[str, Any]

class Review(BaseModel):
    review_id: str
    terraform_code: str
    spacelift_run_id: Optional[str] = None
    spacelift_context: Dict[str, Any] = {}
    status: ReviewStatus
    ai_review_result: Optional[AIReviewResult] = None
    created_at: str
    updated_at: str
    version: int = 1
    previous_version_id: Optional[str] = None

class ReviewCreateRequest(BaseModel):
    terraform_code: str
    spacelift_run_id: Optional[str] = None
    spacelift_context: Optional[Dict[str, Any]] = None

class ReviewUpdateRequest(BaseModel):
    status: Optional[ReviewStatus] = None
    ai_review_result: Optional[AIReviewResult] = None
    version: Optional[int] = None

class AnalyticsResponse(BaseModel):
    total_reviews: int
    reviews_by_status: Dict[str, int]
    reviews_by_risk: Dict[str, int]
    average_risk_score: float
    trend_data: List[Dict[str, Any]]
    top_findings: List[Dict[str, Any]]

