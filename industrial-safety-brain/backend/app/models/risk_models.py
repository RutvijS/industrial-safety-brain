"""
risk_models.py -- Pydantic models for the Compound Risk Detection Engine.

These models represent the structured output of the risk analysis.
The engine produces deterministic assessments; Gemini only explains them.
"""

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field
from typing import Dict, List, Optional


class RiskFactor(BaseModel):
    """Individual risk factor with its computed score."""

    name: str = Field(description="Factor name (e.g. gas_level, temperature)")
    raw_value: float = Field(description="Raw measured or derived value")
    normalized_score: float = Field(description="Normalized 0-100 score for this factor")
    weight: float = Field(description="Weight applied to this factor")
    weighted_score: float = Field(description="normalized_score * weight / 100")
    status: str = Field(description="Normal / Warning / Critical")


class RiskEvidence(BaseModel):
    """Supporting evidence for a detected risk."""

    source: str = Field(description="Data source (sensor, permit, maintenance, incident, shift)")
    detail: str = Field(description="Human-readable description")
    value: str = Field(description="The actual value or identifier")


class DetectedRisk(BaseModel):
    """A compound risk detected from multiple correlated factors."""

    name: str = Field(description="Rule name (e.g. Gas Leak + Hot Work)")
    severity: str = Field(description="Critical / High / Medium / Low")
    description: str = Field(description="Why this combination is dangerous")
    evidence: List[RiskEvidence] = Field(default_factory=list)
    score_boost: int = Field(default=0, description="Additional score points from this compound risk")


class Recommendation(BaseModel):
    """Recommended action to mitigate a detected risk."""

    priority: str = Field(description="IMMEDIATE / HIGH / MEDIUM / LOW")
    action: str = Field(description="What should be done")
    reasoning: str = Field(description="Why this action is needed")


class ZoneRiskAssessment(BaseModel):
    """Complete risk assessment for a single zone."""

    zone: str
    zone_name: str
    overall_risk: str = Field(description="CRITICAL / HIGH / MEDIUM / LOW")
    risk_score: int = Field(description="0-100 composite risk score")
    confidence: int = Field(description="0-99 confidence percentage")
    hazard_level: str = Field(description="Very High / High / Moderate / Low / Very Low")
    risk_factors: List[RiskFactor] = Field(default_factory=list)
    detected_compound_risks: List[DetectedRisk] = Field(default_factory=list)
    recommended_actions: List[Recommendation] = Field(default_factory=list)
    reasoning: List[str] = Field(default_factory=list)
    supporting_evidence: List[RiskEvidence] = Field(default_factory=list)
    gemini_explanation: Optional[str] = Field(
        default=None,
        description="Natural language explanation from Gemini (does not affect score)",
    )
    analyzed_at: str = Field(description="ISO-8601 timestamp")


class PlantRiskAssessment(BaseModel):
    """Risk assessment across the entire plant."""

    overall_risk: str = Field(description="Worst-case risk across all zones")
    overall_risk_score: int = Field(description="Max risk score across all zones")
    overall_confidence: int = Field(description="Average confidence")
    zone_assessments: List[ZoneRiskAssessment] = Field(default_factory=list)
    total_compound_risks: int = 0
    total_recommendations: int = 0
    llm_summary: Optional[str] = Field(
        default=None,
        description="Unified executive summary from LLMSummaryService (single Gemini call)",
    )
    analyzed_at: str = Field(description="ISO-8601 timestamp")
