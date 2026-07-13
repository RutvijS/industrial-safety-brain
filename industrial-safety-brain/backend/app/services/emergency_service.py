"""
emergency_service.py -- Emergency Response Orchestrator.

Generates comprehensive emergency response plans from existing risk data.
Never calculates risk -- only creates action plans.

Input:  Risk Assessment + Plant State
Output: EmergencyPlan with evacuation, isolation, PPE, medical, timeline
"""

from datetime import datetime
from typing import List

from app.models.compliance_models import (
    ChecklistItem,
    EmergencyAction,
    EmergencyContact,
    EmergencyPlan,
    PPERequirement,
    ResponseChecklist,
)
from app.services.plant_state_service import (
    plant_state_service,
    VALID_ZONES,
    ZONE_METADATA,
)
from app.services.risk_engine import risk_engine


# ── Emergency Contacts ────────────────────────────────────

CONTACTS = [
    EmergencyContact(role="Fire Officer", name="Control Room", phone="100", priority=1),
    EmergencyContact(role="Safety Officer", name="HSE Department", phone="101", priority=1),
    EmergencyContact(role="Medical Officer", name="Plant Medical Center", phone="102", priority=1),
    EmergencyContact(role="Plant Manager", name="Command Center", phone="103", priority=2),
    EmergencyContact(role="CISF Security", name="Main Gate", phone="104", priority=2),
    EmergencyContact(role="Ambulance", name="Emergency Medical", phone="108", priority=1),
    EmergencyContact(role="Fire Brigade", name="Municipal Fire", phone="101", priority=2),
    EmergencyContact(role="PESO Inspector", name="Regulatory", phone="105", priority=3),
]


# ── PPE Mapping ───────────────────────────────────────────

PPE_RULES = {
    "gas_level": [
        PPERequirement(item="Self-Contained Breathing Apparatus (SCBA)", reason="Toxic gas detected", mandatory=True),
        PPERequirement(item="Gas Detection Badge", reason="Continuous gas monitoring", mandatory=True),
    ],
    "temperature": [
        PPERequirement(item="Heat-Resistant Suit", reason="High temperature exposure", mandatory=True),
        PPERequirement(item="Face Shield with IR Protection", reason="Radiant heat protection", mandatory=True),
    ],
    "pressure": [
        PPERequirement(item="Blast-Resistant Shield", reason="High pressure hazard", mandatory=True),
        PPERequirement(item="Safety Goggles (Sealed)", reason="Pressure release protection", mandatory=True),
    ],
    "vibration": [
        PPERequirement(item="Anti-Vibration Gloves", reason="Equipment vibration hazard", mandatory=False),
    ],
}

BASE_PPE = [
    PPERequirement(item="Hard Hat (Class E)", reason="Head protection in industrial zone", mandatory=True),
    PPERequirement(item="Safety Boots (Steel Toe)", reason="Foot protection", mandatory=True),
    PPERequirement(item="High-Visibility Vest", reason="Visibility during emergency", mandatory=True),
    PPERequirement(item="Safety Gloves", reason="Hand protection", mandatory=True),
]


class EmergencyService:
    """Generates comprehensive emergency response plans."""

    async def generate_plan(self, zone: str) -> EmergencyPlan:
        """Generate emergency response plan for a zone."""
        if zone not in VALID_ZONES:
            raise ValueError(f"Unknown zone: {zone}")

        zone_state = plant_state_service.get_zone_state(zone)
        assessment = risk_engine.analyze_zone(zone_state)
        meta = ZONE_METADATA.get(zone, {})

        risk_level = assessment.overall_risk
        risk_score = assessment.risk_score
        priority = self._determine_priority(risk_level, risk_score)

        # Determine incident type from critical factors
        incident_type = self._determine_incident_type(assessment)

        # Generate all plan components
        immediate = self._immediate_actions(assessment, zone_state, priority)
        evacuation = self._evacuation_plan(assessment, zone_state, priority)
        isolation = self._isolation_procedure(assessment, zone_state)
        ppe = self._required_ppe(assessment)
        medical = self._medical_response(assessment, zone_state, priority)
        recovery = self._recovery_checklist(assessment)
        timeline = self._incident_timeline(assessment, zone_state, priority)

        # Filter contacts by priority
        contacts = list(CONTACTS)
        if priority == "Low":
            contacts = [c for c in contacts if c.priority <= 1]

        return EmergencyPlan(
            zone=zone,
            zone_name=meta.get("zone_name", zone),
            risk_level=risk_level,
            risk_score=risk_score,
            priority=priority,
            incident_type=incident_type,
            immediate_actions=immediate,
            evacuation_plan=evacuation,
            isolation_procedure=isolation,
            emergency_contacts=contacts,
            required_ppe=ppe,
            medical_response=medical,
            recovery_checklist=recovery,
            incident_timeline=timeline,
            worker_count=zone_state.overall_context.worker_count,
            generated_at=datetime.utcnow().isoformat(),
        )

    def _determine_priority(self, risk_level: str, risk_score: int) -> str:
        if risk_level == "CRITICAL" or risk_score >= 80:
            return "Critical"
        elif risk_level == "HIGH" or risk_score >= 60:
            return "High"
        elif risk_level == "MEDIUM" or risk_score >= 40:
            return "Medium"
        return "Low"

    def _determine_incident_type(self, assessment) -> str:
        critical = [f for f in assessment.risk_factors if f.status == "Critical"]
        if not critical:
            return "General Safety Alert"
        primary = critical[0].name
        mapping = {
            "gas_level": "Gas Leak / Toxic Exposure",
            "temperature": "Thermal Hazard / Fire Risk",
            "pressure": "Pressure Vessel Incident",
            "vibration": "Structural / Mechanical Failure",
            "humidity": "Environmental Hazard",
        }
        return mapping.get(primary, "Multi-Factor Hazard")

    def _immediate_actions(self, assessment, zone_state, priority) -> List[EmergencyAction]:
        step = 0
        actions = []

        if priority in ("Critical", "High"):
            step += 1
            actions.append(EmergencyAction(
                step=step, action=f"Sound emergency alarm for {assessment.zone}",
                responsible="Control Room Operator", time_limit="Immediate", category="Alert",
            ))
            step += 1
            actions.append(EmergencyAction(
                step=step, action="Activate emergency response team",
                responsible="Safety Officer", time_limit="Within 1 min", category="Mobilize",
            ))

        step += 1
        actions.append(EmergencyAction(
            step=step, action="Assess situation and confirm hazard type",
            responsible="Shift Supervisor", time_limit="Within 2 min", category="Assessment",
        ))

        for f in assessment.risk_factors:
            if f.status == "Critical":
                step += 1
                if "gas" in f.name:
                    actions.append(EmergencyAction(
                        step=step, action="Shut off gas supply valves and ventilate area",
                        responsible="Process Operator", time_limit="Within 3 min", category="Containment",
                    ))
                elif "temperature" in f.name:
                    actions.append(EmergencyAction(
                        step=step, action="Activate fire suppression and cooling systems",
                        responsible="Fire Team", time_limit="Within 3 min", category="Suppression",
                    ))
                elif "pressure" in f.name:
                    actions.append(EmergencyAction(
                        step=step, action="Activate pressure relief valves and establish exclusion zone",
                        responsible="Process Engineer", time_limit="Within 2 min", category="Containment",
                    ))

        step += 1
        actions.append(EmergencyAction(
            step=step, action="Report situation to Plant Manager and regulatory authorities",
            responsible="Safety Officer", time_limit="Within 15 min", category="Notification",
        ))

        return actions

    def _evacuation_plan(self, assessment, zone_state, priority) -> List[EmergencyAction]:
        steps = []
        worker_count = zone_state.overall_context.worker_count

        steps.append(EmergencyAction(
            step=1, action=f"Initiate evacuation of {assessment.zone} ({worker_count} workers)",
            responsible="Shift Supervisor", time_limit="Immediate", category="Evacuation",
        ))
        steps.append(EmergencyAction(
            step=2, action="Guide personnel to nearest emergency exit via designated routes",
            responsible="Floor Marshals", time_limit="Within 3 min", category="Evacuation",
        ))
        steps.append(EmergencyAction(
            step=3, action="Conduct headcount at muster point",
            responsible="Shift Supervisor", time_limit="Within 5 min", category="Accountability",
        ))
        steps.append(EmergencyAction(
            step=4, action="Report missing personnel to Emergency Commander",
            responsible="Shift Supervisor", time_limit="Within 7 min", category="Accountability",
        ))

        if priority in ("Critical", "High"):
            steps.append(EmergencyAction(
                step=5, action="Establish 100m exclusion perimeter around affected zone",
                responsible="Security Team", time_limit="Within 5 min", category="Perimeter",
            ))

        return steps

    def _isolation_procedure(self, assessment, zone_state) -> List[EmergencyAction]:
        steps = [
            EmergencyAction(step=1, action="Isolate electrical supply to affected equipment",
                            responsible="Electrical Team", time_limit="Within 5 min", category="Isolation"),
            EmergencyAction(step=2, action="Close process isolation valves",
                            responsible="Process Operator", time_limit="Within 5 min", category="Isolation"),
            EmergencyAction(step=3, action="Depressurize affected systems",
                            responsible="Process Engineer", time_limit="Within 10 min", category="Isolation"),
            EmergencyAction(step=4, action="Verify zero-energy state with LOTO procedures",
                            responsible="Maintenance Team", time_limit="Within 15 min", category="Verification"),
        ]
        return steps

    def _required_ppe(self, assessment) -> List[PPERequirement]:
        ppe = list(BASE_PPE)
        for f in assessment.risk_factors:
            if f.status in ("Critical", "Warning"):
                extra = PPE_RULES.get(f.name, [])
                ppe.extend(extra)
        return ppe

    def _medical_response(self, assessment, zone_state, priority) -> List[EmergencyAction]:
        steps = [
            EmergencyAction(step=1, action="Alert plant medical center and prepare for casualties",
                            responsible="Medical Officer", time_limit="Immediate", category="Medical"),
            EmergencyAction(step=2, action="Set up triage area at muster point",
                            responsible="First Aid Team", time_limit="Within 5 min", category="Medical"),
            EmergencyAction(step=3, action="Administer first aid to affected personnel",
                            responsible="First Aid Team", time_limit="Ongoing", category="Medical"),
        ]
        if priority in ("Critical", "High"):
            steps.append(EmergencyAction(
                step=4, action="Request external ambulance services for severe cases",
                responsible="Medical Officer", time_limit="Within 10 min", category="Medical",
            ))
        return steps

    def _recovery_checklist(self, assessment) -> List[ResponseChecklist]:
        return [
            ResponseChecklist(category="Area Clearance", items=[
                ChecklistItem(item="Confirm hazard has been neutralized", priority="Critical"),
                ChecklistItem(item="Environmental monitoring shows safe levels", priority="Critical"),
                ChecklistItem(item="Structural integrity assessment completed", priority="High"),
            ]),
            ResponseChecklist(category="Equipment", items=[
                ChecklistItem(item="Inspect all affected equipment", priority="High"),
                ChecklistItem(item="Replace damaged components", priority="Medium"),
                ChecklistItem(item="Functional testing completed", priority="High"),
            ]),
            ResponseChecklist(category="Documentation", items=[
                ChecklistItem(item="Incident report filed", priority="Critical"),
                ChecklistItem(item="Regulatory notifications sent", priority="Critical"),
                ChecklistItem(item="Root cause analysis initiated", priority="High"),
                ChecklistItem(item="Lessons learned documented", priority="Medium"),
            ]),
            ResponseChecklist(category="Return to Operations", items=[
                ChecklistItem(item="Management approval for restart", priority="Critical"),
                ChecklistItem(item="Workers briefed on incident", priority="High"),
                ChecklistItem(item="Safety systems verified operational", priority="Critical"),
            ]),
        ]

    def _incident_timeline(self, assessment, zone_state, priority) -> List[dict]:
        now = datetime.utcnow().strftime("%H:%M")
        timeline = [
            {"time": f"T+0 ({now})", "event": "Hazard detected by monitoring systems"},
            {"time": "T+1 min", "event": "Emergency alarm activated"},
            {"time": "T+2 min", "event": "Emergency response team mobilized"},
            {"time": "T+3 min", "event": "Evacuation initiated"},
            {"time": "T+5 min", "event": "Headcount completed at muster point"},
            {"time": "T+5 min", "event": "Isolation procedures initiated"},
            {"time": "T+10 min", "event": "Area secured and perimeter established"},
            {"time": "T+15 min", "event": "Situation report to management"},
            {"time": "T+30 min", "event": "Initial incident assessment complete"},
            {"time": "T+60 min", "event": "Regulatory notification dispatched"},
        ]
        return timeline


# Singleton
emergency_service = EmergencyService()
