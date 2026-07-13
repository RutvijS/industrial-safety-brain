"""
risk_agent.py -- Risk Assessment Agent.

Wraps the existing Risk Engine. Never duplicates risk logic.

Input:  Plant State (zone_state)
Output: Risk Assessment
"""

from typing import Any, Dict

from app.agents.base_agent import BaseAgent


class RiskAgent(BaseAgent):
    """Wraps RiskEngine to produce zone risk assessment."""

    name = "risk_agent"
    display_name = "Risk Agent"
    icon = "🔥"

    def validate(self, context: Dict[str, Any]) -> bool:
        return "zone_state" in context

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        from app.services.risk_engine import risk_engine

        zone_state = context["zone_state"]
        assessment = risk_engine.analyze_zone(zone_state)

        # Store in context for downstream agents
        context["risk_assessment"] = assessment

        return {
            "zone": assessment.zone,
            "zone_name": assessment.zone_name,
            "risk_score": assessment.risk_score,
            "risk_level": assessment.overall_risk,
            "hazard_level": assessment.hazard_level,
            "confidence": assessment.confidence,
            "compound_risks": [
                {"name": r.name, "severity": r.severity, "description": r.description}
                for r in assessment.detected_compound_risks
            ],
            "risk_factors": [
                {
                    "name": f.name,
                    "raw_value": f.raw_value,
                    "normalized_score": f.normalized_score,
                    "status": f.status,
                }
                for f in assessment.risk_factors
            ],
            "recommendations": [
                {"priority": r.priority, "action": r.action, "reasoning": r.reasoning}
                for r in assessment.recommended_actions
            ],
            "reasoning": assessment.reasoning,
        }
