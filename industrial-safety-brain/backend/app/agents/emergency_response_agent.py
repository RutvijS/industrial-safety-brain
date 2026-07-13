"""
emergency_response_agent.py -- Emergency Response Agent.

Generates emergency response plans from existing risk data.
Uses existing project data -- no external APIs.

Input:  Risk Assessment
Output: Evacuation steps, response priority, contacts, incident draft
"""

from typing import Any, Dict, List

from app.agents.base_agent import BaseAgent


# Emergency contacts (would come from a config in production)
EMERGENCY_CONTACTS = [
    {"role": "Fire Officer", "name": "Control Room", "phone": "100"},
    {"role": "Safety Officer", "name": "HSE Department", "phone": "101"},
    {"role": "Medical", "name": "Plant Medical Center", "phone": "102"},
    {"role": "Plant Manager", "name": "Command Center", "phone": "103"},
    {"role": "CISF", "name": "Security", "phone": "104"},
]


class EmergencyResponseAgent(BaseAgent):
    """Generates emergency response plans from risk assessments."""

    name = "emergency_response_agent"
    display_name = "Emergency Response Agent"
    icon = "🚨"

    def validate(self, context: Dict[str, Any]) -> bool:
        return "risk_assessment" in context

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        assessment = context["risk_assessment"]
        zone_state = context.get("zone_state")

        risk_level = assessment.overall_risk
        risk_score = assessment.risk_score

        # Determine response priority
        priority = self._determine_priority(risk_level, risk_score)

        # Generate evacuation steps
        evacuation_steps = self._generate_evacuation(
            assessment, zone_state, priority
        )

        # Generate incident report draft
        report_draft = self._generate_report_draft(assessment, zone_state)

        # Filter contacts by priority
        contacts = EMERGENCY_CONTACTS
        if priority == "Low":
            contacts = contacts[:2]
        elif priority == "Medium":
            contacts = contacts[:3]

        return {
            "priority": priority,
            "risk_level": risk_level,
            "risk_score": risk_score,
            "evacuation_steps": evacuation_steps,
            "emergency_contacts": contacts,
            "report_draft": report_draft,
            "zone": assessment.zone,
            "zone_name": assessment.zone_name,
            "worker_count": zone_state.overall_context.worker_count if zone_state else 0,
        }

    def _determine_priority(self, risk_level: str, risk_score: int) -> str:
        """Map risk level to response priority."""
        if risk_level == "CRITICAL" or risk_score >= 80:
            return "Critical"
        elif risk_level == "HIGH" or risk_score >= 60:
            return "High"
        elif risk_level == "MEDIUM" or risk_score >= 40:
            return "Medium"
        return "Low"

    def _generate_evacuation(
        self, assessment, zone_state, priority: str
    ) -> List[Dict]:
        """Generate evacuation steps based on risk assessment."""
        steps = []

        if priority in ("Critical", "High"):
            steps.append({
                "step": 1,
                "action": f"Sound evacuation alarm for {assessment.zone} ({assessment.zone_name})",
                "responsible": "Control Room Operator",
                "time_limit": "Immediate",
            })
            steps.append({
                "step": 2,
                "action": "Notify Fire Officer and Safety Officer",
                "responsible": "Shift Supervisor",
                "time_limit": "Within 1 minute",
            })

        if zone_state:
            worker_count = zone_state.overall_context.worker_count
            steps.append({
                "step": len(steps) + 1,
                "action": f"Account for all {worker_count} workers in the zone",
                "responsible": "Shift Supervisor",
                "time_limit": "Within 3 minutes",
            })

        # Risk-specific steps
        for factor in assessment.risk_factors:
            if factor.status == "Critical":
                if "gas" in factor.name:
                    steps.append({
                        "step": len(steps) + 1,
                        "action": "Deploy SCBA equipment and isolate gas source",
                        "responsible": "Emergency Response Team",
                        "time_limit": "Within 2 minutes",
                    })
                elif "temperature" in factor.name:
                    steps.append({
                        "step": len(steps) + 1,
                        "action": "Activate fire suppression systems and cool down equipment",
                        "responsible": "Fire Team",
                        "time_limit": "Within 3 minutes",
                    })
                elif "pressure" in factor.name:
                    steps.append({
                        "step": len(steps) + 1,
                        "action": "Vent pressure and establish exclusion zone (50m radius)",
                        "responsible": "Process Engineer",
                        "time_limit": "Within 2 minutes",
                    })

        steps.append({
            "step": len(steps) + 1,
            "action": "Assemble at designated muster point and conduct headcount",
            "responsible": "All Personnel",
            "time_limit": "Within 5 minutes",
        })

        steps.append({
            "step": len(steps) + 1,
            "action": "Submit incident report and notify management",
            "responsible": "Safety Officer",
            "time_limit": "Within 30 minutes",
        })

        return steps

    def _generate_report_draft(self, assessment, zone_state) -> Dict:
        """Generate an incident report draft."""
        compound_risks = [r.name for r in assessment.detected_compound_risks]
        critical_factors = [
            f.name for f in assessment.risk_factors if f.status == "Critical"
        ]

        return {
            "title": f"Safety Alert - {assessment.zone} ({assessment.zone_name})",
            "risk_level": assessment.overall_risk,
            "risk_score": assessment.risk_score,
            "zone": assessment.zone,
            "zone_name": assessment.zone_name,
            "detected_hazards": compound_risks,
            "critical_factors": critical_factors,
            "worker_count": zone_state.overall_context.worker_count if zone_state else 0,
            "active_permits": len(zone_state.active_permits) if zone_state else 0,
            "description": (
                f"Risk assessment for {assessment.zone_name} indicates "
                f"{assessment.overall_risk} risk (score: {assessment.risk_score}/100). "
                f"{len(compound_risks)} compound risks detected. "
                f"{len(critical_factors)} critical factors identified."
            ),
        }
