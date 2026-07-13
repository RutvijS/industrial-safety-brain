"""
response_aggregator.py -- Merges all agent outputs.

Combines results from all agents into a single AggregatedResponse.
Optional Gemini summary provides a cohesive narrative.
"""

from typing import Any, Dict, List, Optional

from app.models.agent_models import AgentResult


class ResponseAggregator:
    """Merges agent results into a unified response."""

    async def aggregate(
        self,
        results: List[Dict[str, Any]],
        include_summary: bool = True,
    ) -> Dict[str, Any]:
        """Merge all agent outputs and optionally generate Gemini summary.

        Args:
            results: List of agent output dicts from format_output().
            include_summary: Whether to call Gemini for overall summary.

        Returns:
            Dict with all merged data + optional summary.
        """
        merged: Dict[str, Any] = {}
        agent_results: List[AgentResult] = []

        for r in results:
            agent_results.append(AgentResult(**r))
            # Store each agent's data under its name
            merged[r["agent_name"]] = r.get("data", {})

        # Generate summary
        summary = None
        if include_summary:
            summary = await self._generate_summary(agent_results)

        return {
            "results": [r.model_dump() for r in agent_results],
            "overall_summary": summary,
            "agents_completed": sum(1 for r in agent_results if r.status == "completed"),
            "agents_failed": sum(1 for r in agent_results if r.status == "failed"),
        }

    async def _generate_summary(self, results: List[AgentResult]) -> Optional[str]:
        """Generate a Gemini summary of all agent outputs."""
        try:
            from app.services.gemini_service import gemini_service

            # Build context from all completed agents
            parts = ["Summarize this multi-agent industrial safety analysis:\n"]

            for r in results:
                if r.status != "completed":
                    continue

                parts.append(f"\n--- {r.agent_type} ---")

                if r.agent_name == "risk_agent":
                    d = r.data
                    parts.append(f"Risk Level: {d.get('risk_level', 'N/A')}")
                    parts.append(f"Risk Score: {d.get('risk_score', 0)}/100")
                    risks = d.get("compound_risks", [])
                    if risks:
                        parts.append(f"Compound Risks: {', '.join(r2.get('name','') for r2 in risks)}")

                elif r.agent_name == "incident_agent":
                    d = r.data
                    parts.append(f"Similar Incidents: {len(d.get('similar_incidents', []))}")
                    parts.append(f"Lessons Learned: {len(d.get('lessons_learned', []))}")

                elif r.agent_name == "compliance_agent":
                    d = r.data
                    parts.append(f"Compliance Gaps: {d.get('total_gaps', 0)}")
                    actions = d.get("required_actions", [])
                    if actions:
                        parts.append("Actions: " + "; ".join(a.get("action","") for a in actions[:3]))

                elif r.agent_name == "emergency_response_agent":
                    d = r.data
                    parts.append(f"Response Priority: {d.get('priority', 'N/A')}")
                    steps = d.get("evacuation_steps", [])
                    parts.append(f"Evacuation Steps: {len(steps)}")

                elif r.agent_name == "knowledge_graph_agent":
                    d = r.data
                    parts.append(f"Graph Available: {d.get('available', False)}")
                    parts.append(f"Connected Nodes: {d.get('total_nodes', 0)}")

            parts.append("\nProvide a concise 3-4 sentence executive summary.")
            parts.append("Focus on the most critical findings and recommended actions.")

            prompt = "\n".join(parts)
            return await gemini_service.generate_response(prompt)

        except Exception as e:
            return f"Summary unavailable: {str(e)}"


# Singleton
response_aggregator = ResponseAggregator()
