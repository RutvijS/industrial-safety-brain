"""
compliance_agent.py -- Compliance Agent.

Uses existing RAG retriever for regulation documents.
Does NOT create a separate compliance engine.

Input:  Risk Assessment + Plant State
Output: Relevant regulations, compliance gaps, required actions
"""

from typing import Any, Dict, List

from app.agents.base_agent import BaseAgent


class ComplianceAgent(BaseAgent):
    """Identifies applicable regulations and compliance gaps."""

    name = "compliance_agent"
    display_name = "Compliance Agent"
    icon = "📋"

    def validate(self, context: Dict[str, Any]) -> bool:
        return "risk_assessment" in context

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        assessment = context["risk_assessment"]
        zone_state = context.get("zone_state")

        # Build compliance query from risk factors
        risk_factors_str = ", ".join(
            f"{f.name} ({f.status})" for f in assessment.risk_factors
            if f.status in ("Warning", "Critical")
        )
        compound_risks_str = ", ".join(
            r.name for r in assessment.detected_compound_risks
        )

        # Try RAG retrieval for regulations
        regulations = []
        try:
            from app.rag.retriever import retriever
            from app.rag.vector_store import vector_store

            if vector_store.get_document_count() > 0:
                query = (
                    f"Industrial safety compliance regulations for "
                    f"{assessment.zone_name}. "
                    f"Risk factors: {risk_factors_str}. "
                    f"Compound risks: {compound_risks_str}."
                )

                reg_docs = retriever.retrieve(
                    query=query,
                    top_k=5,
                    document_type=None,  # Search all types
                )

                regulations = [
                    {
                        "source": d.title or d.source_filename,
                        "type": d.document_type,
                        "relevance": d.relevance_score,
                        "excerpt": d.content[:200],
                    }
                    for d in reg_docs
                ]
        except Exception:
            pass  # RAG unavailable, continue with generated compliance

        # Generate compliance gaps from risk assessment
        compliance_gaps = self._identify_gaps(assessment)

        # Generate required actions
        required_actions = self._generate_actions(assessment, zone_state)

        return {
            "regulations": regulations,
            "compliance_gaps": compliance_gaps,
            "required_actions": required_actions,
            "risk_level": assessment.overall_risk,
            "total_gaps": len(compliance_gaps),
            "rag_available": len(regulations) > 0,
        }

    def _identify_gaps(self, assessment) -> List[Dict]:
        """Identify compliance gaps from risk factors."""
        gaps = []

        for factor in assessment.risk_factors:
            if factor.status == "Critical":
                gaps.append({
                    "area": factor.name.replace("_", " ").title(),
                    "severity": "Critical",
                    "description": (
                        f"{factor.name.replace('_', ' ').title()} is at critical level "
                        f"({factor.raw_value}). Immediate compliance action required."
                    ),
                })
            elif factor.status == "Warning":
                gaps.append({
                    "area": factor.name.replace("_", " ").title(),
                    "severity": "Warning",
                    "description": (
                        f"{factor.name.replace('_', ' ').title()} is above warning threshold "
                        f"({factor.raw_value}). Review compliance requirements."
                    ),
                })

        for risk in assessment.detected_compound_risks:
            gaps.append({
                "area": risk.name,
                "severity": risk.severity,
                "description": f"Compound risk detected: {risk.description}",
            })

        return gaps

    def _generate_actions(self, assessment, zone_state) -> List[Dict]:
        """Generate required compliance actions."""
        actions = []

        if assessment.overall_risk in ("CRITICAL", "HIGH"):
            actions.append({
                "priority": "Immediate",
                "action": "Conduct emergency safety audit of the zone",
                "regulation": "Factory Act Section 7A",
            })

        for factor in assessment.risk_factors:
            if factor.status == "Critical":
                if "gas" in factor.name:
                    actions.append({
                        "priority": "Immediate",
                        "action": "Deploy gas detection monitors and evacuate if LEL exceeded",
                        "regulation": "OISD-GDN-116",
                    })
                elif "temperature" in factor.name:
                    actions.append({
                        "priority": "High",
                        "action": "Inspect cooling systems and verify heat shielding",
                        "regulation": "DGMS Technical Circular",
                    })
                elif "pressure" in factor.name:
                    actions.append({
                        "priority": "High",
                        "action": "Check pressure relief valves and containment systems",
                        "regulation": "OISD-STD-144",
                    })

        if zone_state and len(zone_state.active_permits) > 2:
            actions.append({
                "priority": "Medium",
                "action": "Review overlapping permits for conflict resolution",
                "regulation": "Factory Act Section 36",
            })

        return actions
