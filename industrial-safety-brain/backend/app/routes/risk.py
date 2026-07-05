"""
risk.py -- REST endpoints for the Compound Risk Detection Engine.

Architecture: Route -> RiskEngine -> PlantStateService -> DataService -> JSON

POST /risk-analysis          - Full plant analysis with Gemini explanation
GET  /risk-analysis/{zone}   - Single zone analysis with Gemini explanation
"""

# pyrefly: ignore [missing-import]
from fastapi import APIRouter, HTTPException

from app.models.risk_models import PlantRiskAssessment, ZoneRiskAssessment
from app.services.plant_state_service import plant_state_service, VALID_ZONES
from app.services.risk_engine import risk_engine

router = APIRouter(tags=["Risk Analysis"])


@router.post("/risk-analysis", response_model=PlantRiskAssessment)
async def run_risk_analysis() -> PlantRiskAssessment:
    """Run compound risk analysis across the entire plant.

    Fetches the current plant state, analyzes every zone, and returns
    a comprehensive risk assessment with Gemini explanations.
    """
    try:
        from datetime import datetime

        plant_state = plant_state_service.get_plant_state()
        zone_assessments = []

        for zone_state in plant_state.zones:
            assessment = await risk_engine.analyze_zone_with_explanation(zone_state)
            zone_assessments.append(assessment)

        # Overall = worst-case across all zones
        if zone_assessments:
            worst = max(zone_assessments, key=lambda a: a.risk_score)
            overall_risk = worst.overall_risk
            overall_score = worst.risk_score
            avg_confidence = int(
                sum(a.confidence for a in zone_assessments) / len(zone_assessments)
            )
        else:
            overall_risk = "LOW"
            overall_score = 0
            avg_confidence = 0

        return PlantRiskAssessment(
            overall_risk=overall_risk,
            overall_risk_score=overall_score,
            overall_confidence=avg_confidence,
            zone_assessments=zone_assessments,
            total_compound_risks=sum(
                len(a.detected_compound_risks) for a in zone_assessments
            ),
            total_recommendations=sum(
                len(a.recommended_actions) for a in zone_assessments
            ),
            analyzed_at=datetime.utcnow().isoformat(),
        )

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Risk analysis failed: {e}")


@router.get("/risk-analysis/{zone}", response_model=ZoneRiskAssessment)
async def get_zone_risk_analysis(zone: str) -> ZoneRiskAssessment:
    """Run compound risk analysis for a single zone."""
    if zone not in VALID_ZONES:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown zone: {zone}. Valid zones: {VALID_ZONES}",
        )

    try:
        zone_state = plant_state_service.get_zone_state(zone)
        return await risk_engine.analyze_zone_with_explanation(zone_state)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Risk analysis failed: {e}")
