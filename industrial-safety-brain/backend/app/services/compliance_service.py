"""
compliance_service.py -- Compliance Intelligence Service.

Consumes Risk Assessment + Plant State + RAG regulations.
Produces a ComplianceReport with score, findings, corrective actions.

IMPORTANT: Never calculates risk. Only interprets regulations.
"""

from datetime import datetime
from typing import List

from app.models.compliance_models import (
    ComplianceReport,
    CorrectiveAction,
    RegulationFinding,
)
from app.services.plant_state_service import (
    plant_state_service,
    VALID_ZONES,
    ZONE_METADATA,
)
from app.services.risk_engine import risk_engine


# ── Regulation Rules ───────────────────────────────────────
# These map risk factors to applicable regulations.
# In production, these would be loaded from a database.

REGULATION_RULES = [
    {
        "regulation": "OISD-GDN-116",
        "section": "Gas Detection & Monitoring",
        "factor": "gas_level",
        "threshold_warning": 30,
        "threshold_critical": 50,
        "description": "Continuous gas monitoring required in hazardous zones",
        "action": "Deploy additional gas monitors and verify LEL alarm thresholds",
    },
    {
        "regulation": "Factory Act Section 7A",
        "section": "General Safety",
        "factor": "overall_risk",
        "threshold_warning": "HIGH",
        "threshold_critical": "CRITICAL",
        "description": "Employer must ensure safety of workers in hazardous areas",
        "action": "Conduct immediate safety audit and implement risk controls",
    },
    {
        "regulation": "DGMS Technical Circular",
        "section": "Temperature Control",
        "factor": "temperature",
        "threshold_warning": 80,
        "threshold_critical": 120,
        "description": "Temperature monitoring and heat stress prevention mandatory",
        "action": "Inspect cooling systems and enforce heat rest schedules",
    },
    {
        "regulation": "OISD-STD-144",
        "section": "Pressure Vessel Safety",
        "factor": "pressure",
        "threshold_warning": 5.0,
        "threshold_critical": 8.0,
        "description": "Pressure vessels must have certified relief valves",
        "action": "Verify pressure relief valve certification and inspect containment",
    },
    {
        "regulation": "Factory Act Section 36",
        "section": "Permit to Work",
        "factor": "active_permits",
        "threshold_warning": 3,
        "threshold_critical": 5,
        "description": "Work permits must be properly managed and reviewed",
        "action": "Review all active permits for conflicts and expiration",
    },
    {
        "regulation": "OISD-STD-154",
        "section": "Maintenance Safety",
        "factor": "active_maintenance",
        "threshold_warning": 2,
        "threshold_critical": 4,
        "description": "Maintenance work must follow safe work procedures",
        "action": "Verify maintenance procedures and worker safety compliance",
    },
    {
        "regulation": "DGMS Regulation 15",
        "section": "Vibration Monitoring",
        "factor": "vibration",
        "threshold_warning": 10,
        "threshold_critical": 20,
        "description": "Equipment vibration must be monitored for structural integrity",
        "action": "Inspect rotating equipment and check foundation bolts",
    },
    {
        "regulation": "Factory Act Section 41B",
        "section": "Hazardous Process Safety",
        "factor": "compound_risks",
        "threshold_warning": 1,
        "threshold_critical": 2,
        "description": "Compound hazards require escalated safety management",
        "action": "Activate compound risk protocol and notify safety committee",
    },
]


class ComplianceService:
    """Evaluates regulatory compliance from existing risk data."""

    async def analyze(self, zone: str) -> ComplianceReport:
        """Run compliance analysis for a zone.

        1. Get plant state + risk assessment
        2. Check each regulation against actual values
        3. Score compliance
        4. Generate corrective actions
        """
        if zone not in VALID_ZONES:
            raise ValueError(f"Unknown zone: {zone}")

        zone_state = plant_state_service.get_zone_state(zone)
        assessment = risk_engine.analyze_zone(zone_state)
        meta = ZONE_METADATA.get(zone, {})

        # Build context values for checking
        context = {
            "gas_level": zone_state.current_sensor_status.avg_gas_level,
            "temperature": zone_state.current_sensor_status.avg_temperature,
            "pressure": zone_state.current_sensor_status.avg_pressure,
            "vibration": zone_state.current_sensor_status.avg_vibration,
            "active_permits": len(zone_state.active_permits),
            "active_maintenance": len(zone_state.active_maintenance),
            "compound_risks": len(assessment.detected_compound_risks),
            "overall_risk": assessment.overall_risk,
        }

        violated: List[RegulationFinding] = []
        compliant: List[RegulationFinding] = []
        actions: List[CorrectiveAction] = []

        for rule in REGULATION_RULES:
            factor = rule["factor"]
            value = context.get(factor)

            if value is None:
                continue

            # Check compliance
            finding = self._check_regulation(rule, value, assessment)
            if finding.status == "Non-Compliant":
                violated.append(finding)
                actions.append(CorrectiveAction(
                    priority="Immediate" if finding.severity == "Critical" else "High",
                    action=rule["action"],
                    regulation=rule["regulation"],
                    deadline_hours=4 if finding.severity == "Critical" else 24,
                    responsible="Safety Officer",
                ))
            elif finding.status == "Warning":
                violated.append(finding)
                actions.append(CorrectiveAction(
                    priority="Medium",
                    action=rule["action"],
                    regulation=rule["regulation"],
                    deadline_hours=48,
                    responsible="Shift Supervisor",
                ))
            else:
                compliant.append(finding)

        # Try RAG retrieval for additional regulatory evidence
        rag_findings = await self._retrieve_rag_regulations(assessment)
        for rf in rag_findings:
            if rf not in [v.regulation for v in violated]:
                compliant.append(RegulationFinding(
                    regulation=rf,
                    status="Reviewed",
                    severity="Low",
                    description="Retrieved from document index",
                    source="RAG",
                ))

        # Calculate score
        total = len(violated) + len(compliant)
        score = round((len(compliant) / max(total, 1)) * 100)
        critical_count = sum(1 for v in violated if v.severity == "Critical")

        if critical_count > 0:
            overall_status = "Non-Compliant"
        elif len(violated) > 0:
            overall_status = "Warning"
        else:
            overall_status = "Compliant"

        # Generate audit summary
        summary = await self._generate_summary(
            zone, meta, assessment, violated, compliant, actions, score
        )

        return ComplianceReport(
            zone=zone,
            zone_name=meta.get("zone_name", zone),
            overall_status=overall_status,
            compliance_score=score,
            risk_level=assessment.overall_risk,
            risk_score=assessment.risk_score,
            total_findings=len(violated),
            critical_findings=critical_count,
            violated_regulations=violated,
            compliant_regulations=compliant,
            corrective_actions=actions,
            audit_summary=summary,
            analyzed_at=datetime.utcnow().isoformat(),
        )

    def _check_regulation(self, rule: dict, value, assessment) -> RegulationFinding:
        """Check a single regulation against the actual value."""
        factor = rule["factor"]

        # String comparison (risk level)
        if factor == "overall_risk":
            risk_levels = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}
            val_num = risk_levels.get(value, 0)
            warn_num = risk_levels.get(rule["threshold_warning"], 1)
            crit_num = risk_levels.get(rule["threshold_critical"], 2)

            if val_num >= crit_num:
                return RegulationFinding(
                    regulation=rule["regulation"],
                    section=rule["section"],
                    status="Non-Compliant",
                    severity="Critical",
                    description=f"{rule['description']}. Current: {value}",
                    evidence=f"Risk level {value} exceeds critical threshold",
                )
            elif val_num >= warn_num:
                return RegulationFinding(
                    regulation=rule["regulation"],
                    section=rule["section"],
                    status="Warning",
                    severity="High",
                    description=f"{rule['description']}. Current: {value}",
                    evidence=f"Risk level {value} exceeds warning threshold",
                )
        else:
            # Numeric comparison
            if value >= rule["threshold_critical"]:
                return RegulationFinding(
                    regulation=rule["regulation"],
                    section=rule["section"],
                    status="Non-Compliant",
                    severity="Critical",
                    description=f"{rule['description']}. Current: {value}",
                    evidence=f"{factor} = {value} exceeds critical threshold ({rule['threshold_critical']})",
                )
            elif value >= rule["threshold_warning"]:
                return RegulationFinding(
                    regulation=rule["regulation"],
                    section=rule["section"],
                    status="Warning",
                    severity="High",
                    description=f"{rule['description']}. Current: {value}",
                    evidence=f"{factor} = {value} exceeds warning threshold ({rule['threshold_warning']})",
                )

        return RegulationFinding(
            regulation=rule["regulation"],
            section=rule["section"],
            status="Compliant",
            severity="Low",
            description=rule["description"],
            evidence=f"{factor} = {value} within acceptable limits",
        )

    async def _retrieve_rag_regulations(self, assessment) -> List[str]:
        """Retrieve regulation names from RAG."""
        try:
            from app.rag.retriever import retriever
            from app.rag.vector_store import vector_store

            if vector_store.get_document_count() == 0:
                return []

            query = f"Safety regulations for {assessment.zone_name} {assessment.overall_risk} risk"
            docs = retriever.retrieve(query=query, top_k=3)
            return [d.title or d.source_filename for d in docs]
        except Exception:
            return []

    async def _generate_summary(
        self, zone, meta, assessment, violated, compliant, actions, score
    ) -> str:
        """Generate deterministic audit summary.

        LLM-powered summaries are now handled by LLMSummaryService.
        This returns a structured fallback summary only.
        """
        return (
            f"Compliance audit for {meta.get('zone_name', zone)}: "
            f"Score {score}/100. {len(violated)} violations found. "
            f"{len(actions)} corrective actions required."
        )


# Singleton
compliance_service = ComplianceService()
