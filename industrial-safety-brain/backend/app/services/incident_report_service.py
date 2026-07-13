"""
incident_report_service.py -- Auto-generated Incident Report Service.

Orchestrates Risk Engine + Compliance + Emergency to produce
a comprehensive, PDF-ready incident report.

Reports are stored in memory for GET /reports/{id} retrieval.
"""

import uuid
from datetime import datetime
from typing import Dict, Optional

from app.models.compliance_models import IncidentReport
from app.services.plant_state_service import (
    plant_state_service,
    VALID_ZONES,
    ZONE_METADATA,
)
from app.services.risk_engine import risk_engine


class IncidentReportService:
    """Auto-generates structured incident reports."""

    def __init__(self) -> None:
        self._reports: Dict[str, IncidentReport] = {}

    async def generate(self, zone: str) -> IncidentReport:
        """Generate a comprehensive incident report for a zone.

        Combines data from Risk Engine + Plant State.
        Produces a PDF-ready JSON structure.
        """
        if zone not in VALID_ZONES:
            raise ValueError(f"Unknown zone: {zone}")

        zone_state = plant_state_service.get_zone_state(zone)
        assessment = risk_engine.analyze_zone(zone_state)
        meta = ZONE_METADATA.get(zone, {})

        report_id = f"RPT-{uuid.uuid4().hex[:8].upper()}"

        # Equipment involved
        equipment = list({
            s.equipment for s in zone_state.sensors_snapshot
        })

        # Detected risks
        detected_risks = [
            {"name": r.name, "severity": r.severity, "description": r.description}
            for r in assessment.detected_compound_risks
        ]

        # Risk factors
        risk_factors = [
            {
                "name": f.name,
                "value": str(f.raw_value),
                "score": f.normalized_score,
                "status": f.status,
            }
            for f in assessment.risk_factors
        ]

        # Evidence from sensor data
        evidence = []
        critical_sensors = [
            s for s in zone_state.sensors_snapshot if s.status in ("Critical", "Warning")
        ]
        for s in critical_sensors[:5]:
            evidence.append({
                "type": "Sensor Reading",
                "source": s.sensor_id,
                "detail": (
                    f"Equipment {s.equipment}: "
                    f"Gas={s.gas_level}ppm, Temp={s.temperature}°C, "
                    f"Pressure={s.pressure}bar, Status={s.status}"
                ),
            })

        # Applicable regulations
        regulations = []
        for f in assessment.risk_factors:
            if f.status == "Critical":
                if "gas" in f.name:
                    regulations.append({"regulation": "OISD-GDN-116", "section": "Gas Detection"})
                elif "temperature" in f.name:
                    regulations.append({"regulation": "DGMS Technical Circular", "section": "Temperature Control"})
                elif "pressure" in f.name:
                    regulations.append({"regulation": "OISD-STD-144", "section": "Pressure Vessel Safety"})
        if assessment.overall_risk in ("CRITICAL", "HIGH"):
            regulations.append({"regulation": "Factory Act Section 7A", "section": "General Safety"})

        # Corrective actions from recommendations
        corrective_actions = [
            {"priority": r.priority, "action": r.action, "reasoning": r.reasoning}
            for r in assessment.recommended_actions
        ]

        # Evacuation required?
        evacuation = assessment.overall_risk == "CRITICAL" or assessment.risk_score >= 80

        # Executive summary
        summary = await self._generate_summary(
            zone, meta, assessment, detected_risks, regulations
        )

        report = IncidentReport(
            report_id=report_id,
            timestamp=datetime.utcnow().isoformat(),
            zone=zone,
            zone_name=meta.get("zone_name", zone),
            risk_level=assessment.overall_risk,
            risk_score=assessment.risk_score,
            equipment_involved=equipment,
            detected_risks=detected_risks,
            risk_factors=risk_factors,
            evidence=evidence,
            applicable_regulations=regulations,
            corrective_actions=corrective_actions,
            emergency_priority="Critical" if evacuation else (
                "High" if assessment.overall_risk == "HIGH" else "Medium"
            ),
            evacuation_required=evacuation,
            worker_count=zone_state.overall_context.worker_count,
            active_permits=len(zone_state.active_permits),
            executive_summary=summary,
            export_format="json",
        )

        # Store for retrieval
        self._reports[report_id] = report

        return report

    def get_report(self, report_id: str) -> Optional[IncidentReport]:
        """Retrieve a previously generated report."""
        return self._reports.get(report_id)

    def list_reports(self) -> list:
        """List all stored report IDs."""
        return [
            {"report_id": r.report_id, "zone": r.zone, "timestamp": r.timestamp, "risk_level": r.risk_level}
            for r in self._reports.values()
        ]

    async def _generate_summary(self, zone, meta, assessment, risks, regulations) -> str:
        """Generate executive summary with Gemini."""
        try:
            from app.services.gemini_service import gemini_service

            prompt = (
                f"Write a 4-sentence executive summary for an incident report.\n"
                f"Zone: {meta.get('zone_name', zone)}\n"
                f"Risk: {assessment.overall_risk} ({assessment.risk_score}/100)\n"
                f"Compound Risks: {len(risks)}\n"
                f"Regulations: {', '.join(r.get('regulation','') for r in regulations)}\n"
                f"Be factual and actionable. This is for plant management."
            )
            return await gemini_service.generate_response(prompt)
        except Exception:
            return (
                f"Incident report for {meta.get('zone_name', zone)}: "
                f"Risk level {assessment.overall_risk} ({assessment.risk_score}/100). "
                f"{len(risks)} compound risks detected. "
                f"Immediate corrective actions required per applicable regulations."
            )


# Singleton
incident_report_service = IncidentReportService()
