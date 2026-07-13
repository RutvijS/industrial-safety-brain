"""
compliance.py -- REST endpoints for Compliance Intelligence,
Emergency Response, and Incident Reports.

POST /compliance-analysis      - Compliance report
POST /emergency-response       - Emergency plan
POST /generate-incident-report - Auto-generated report
GET  /reports/{report_id}      - Retrieve stored report
GET  /reports                  - List all reports
"""

# pyrefly: ignore [missing-import]
from fastapi import APIRouter, HTTPException
from typing import List

from app.models.compliance_models import (
    ComplianceReport,
    EmergencyPlan,
    IncidentReport,
    ZoneRequest,
)
from app.services.compliance_service import compliance_service
from app.services.emergency_service import emergency_service
from app.services.incident_report_service import incident_report_service
from app.services.plant_state_service import VALID_ZONES

router = APIRouter(tags=["Compliance & Emergency"])


@router.post("/compliance-analysis", response_model=ComplianceReport)
async def run_compliance_analysis(request: ZoneRequest) -> ComplianceReport:
    """Run compliance analysis for a zone."""
    if request.zone not in VALID_ZONES:
        raise HTTPException(status_code=404, detail=f"Unknown zone: {request.zone}")
    try:
        return await compliance_service.analyze(request.zone)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Compliance analysis failed: {e}")


@router.post("/emergency-response", response_model=EmergencyPlan)
async def generate_emergency_response(request: ZoneRequest) -> EmergencyPlan:
    """Generate emergency response plan for a zone."""
    if request.zone not in VALID_ZONES:
        raise HTTPException(status_code=404, detail=f"Unknown zone: {request.zone}")
    try:
        return await emergency_service.generate_plan(request.zone)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Emergency plan generation failed: {e}")


@router.post("/generate-incident-report", response_model=IncidentReport)
async def generate_incident_report(request: ZoneRequest) -> IncidentReport:
    """Auto-generate an incident report for a zone."""
    if request.zone not in VALID_ZONES:
        raise HTTPException(status_code=404, detail=f"Unknown zone: {request.zone}")
    try:
        return await incident_report_service.generate(request.zone)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {e}")


@router.get("/reports/{report_id}", response_model=IncidentReport)
async def get_report(report_id: str) -> IncidentReport:
    """Retrieve a previously generated incident report."""
    report = incident_report_service.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
    return report


@router.get("/reports", response_model=List[dict])
async def list_reports() -> List[dict]:
    """List all stored incident reports."""
    return incident_report_service.list_reports()
