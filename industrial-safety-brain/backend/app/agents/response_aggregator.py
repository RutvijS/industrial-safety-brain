"""
response_aggregator.py -- Merges all agent outputs.

Combines results from all agents into a single AggregatedResponse.
Summary is generated via LLMSummaryService (ONE Gemini call).
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
        """Merge all agent outputs and optionally generate LLM summary.

        Args:
            results: List of agent output dicts from format_output().
            include_summary: Whether to generate an LLM summary.

        Returns:
            Dict with all merged data + optional summary.
        """
        merged: Dict[str, Any] = {}
        agent_results: List[AgentResult] = []

        for r in results:
            agent_results.append(AgentResult(**r))
            # Store each agent's data under its name
            merged[r["agent_name"]] = r.get("data", {})

        # Generate summary via LLMSummaryService (ONE Gemini call)
        summary = None
        if include_summary:
            summary = await self._generate_summary(results)

        return {
            "results": [r.model_dump() for r in agent_results],
            "overall_summary": summary,
            "agents_completed": sum(1 for r in agent_results if r.status == "completed"),
            "agents_failed": sum(1 for r in agent_results if r.status == "failed"),
        }

    async def _generate_summary(self, results: List[Dict[str, Any]]) -> Optional[str]:
        """Generate a unified summary via LLMSummaryService."""
        try:
            from app.services.llm_summary_service import llm_summary_service
            return await llm_summary_service.summarize_agent_results(results)
        except Exception as e:
            return f"Summary unavailable: {str(e)}"


# Singleton
response_aggregator = ResponseAggregator()
