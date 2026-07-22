"""
risk.py -- REST endpoints for the Compound Risk Detection Engine.

Architecture: Route -> RiskEngine -> PlantStateService -> DataService -> JSON
              Route -> LLMSummaryService -> ONE Gemini call

POST /risk-analysis          - Full plant analysis with LLM summary (1 Gemini call)
GET  /risk-analysis/{zone}   - Single zone analysis with LLM summary (1 Gemini call)
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

    Fetches the current plant state, analyzes every zone deterministically,
    then calls LLMSummaryService ONCE for a unified explanation.
    """
    try:
        from datetime import datetime
        from app.services.llm_summary_service import llm_summary_service

        plant_state = plant_state_service.get_plant_state()
        zone_assessments = []

        for zone_state in plant_state.zones:
            # Deterministic analysis — NO Gemini calls
            assessment = risk_engine.analyze_zone(zone_state)
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

        # ONE Gemini call for all zones via LLMSummaryService
        risk_data = {
            "zone_assessments": [
                {
                    "zone": a.zone,
                    "zone_name": a.zone_name,
                    "overall_risk": a.overall_risk,
                    "risk_score": a.risk_score,
                    "hazard_level": a.hazard_level,
                    "confidence": a.confidence,
                    "detected_compound_risks": [
                        {"name": r.name, "severity": r.severity, "description": r.description}
                        for r in a.detected_compound_risks
                    ],
                    "risk_factors": [
                        {"name": f.name, "raw_value": f.raw_value, "status": f.status}
                        for f in a.risk_factors
                    ],
                    "recommended_actions": [
                        {"priority": r.priority, "action": r.action}
                        for r in a.recommended_actions
                    ],
                }
                for a in zone_assessments
            ],
        }
        llm_summary = await llm_summary_service.summarize(risk_data=risk_data)

        # Attach summary to each zone as gemini_explanation
        for a in zone_assessments:
            a.gemini_explanation = llm_summary

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
            llm_summary=llm_summary,
            analyzed_at=datetime.utcnow().isoformat(),
        )

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Risk analysis failed: {e}")


@router.get("/risk-analysis/{zone}", response_model=ZoneRiskAssessment)
async def get_zone_risk_analysis(zone: str) -> ZoneRiskAssessment:
    """Run compound risk analysis for a single zone.

    Deterministic analysis + ONE Gemini call via LLMSummaryService.
    """
    if zone not in VALID_ZONES:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown zone: {zone}. Valid zones: {VALID_ZONES}",
        )

    try:
        from app.services.llm_summary_service import llm_summary_service

        zone_state = plant_state_service.get_zone_state(zone)
        # Deterministic analysis — NO Gemini call
        assessment = risk_engine.analyze_zone(zone_state)

        # ONE Gemini call via LLMSummaryService
        risk_data = {
            "zone": assessment.zone,
            "zone_name": assessment.zone_name,
            "overall_risk": assessment.overall_risk,
            "risk_score": assessment.risk_score,
            "hazard_level": assessment.hazard_level,
            "confidence": assessment.confidence,
            "detected_compound_risks": [
                {"name": r.name, "severity": r.severity, "description": r.description}
                for r in assessment.detected_compound_risks
            ],
            "risk_factors": [
                {"name": f.name, "raw_value": f.raw_value, "status": f.status}
                for f in assessment.risk_factors
            ],
        }
        explanation = await llm_summary_service.summarize(risk_data=risk_data)
        assessment.gemini_explanation = explanation

        return assessment

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Risk analysis failed: {e}")
