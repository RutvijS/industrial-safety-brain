"""
agent_manager.py -- Agentic AI Orchestrator.

Coordinates all agents:
1. Receives user request
2. Determines which agents to run
3. Executes them sequentially (each feeds the next)
4. Merges responses via ResponseAggregator
5. Returns unified result

If one agent fails, the pipeline continues with partial results.
"""

import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.agents.base_agent import BaseAgent
from app.agents.risk_agent import RiskAgent
from app.agents.incident_agent import IncidentAgent
from app.agents.knowledge_graph_agent import KnowledgeGraphAgent
from app.agents.compliance_agent import ComplianceAgent
from app.agents.emergency_response_agent import EmergencyResponseAgent
from app.agents.response_aggregator import response_aggregator
from app.models.agent_models import AggregatedResponse, PipelineStep
from app.services.plant_state_service import plant_state_service, VALID_ZONES


# Agent pipeline order -- each agent's output feeds the next
AGENT_PIPELINE: List[BaseAgent] = [
    RiskAgent(),
    IncidentAgent(),
    KnowledgeGraphAgent(),
    ComplianceAgent(),
    EmergencyResponseAgent(),
]

AGENT_MAP: Dict[str, BaseAgent] = {a.name: a for a in AGENT_PIPELINE}


class AgentManager:
    """Orchestrates the multi-agent analysis pipeline."""

    async def analyze(
        self,
        zone: str,
        agents_to_run: Optional[List[str]] = None,
        include_summary: bool = True,
    ) -> AggregatedResponse:
        """Run the full agent pipeline for a zone.

        Args:
            zone: Zone to analyze (e.g. "Zone A").
            agents_to_run: Specific agents to run. None = run all.
            include_summary: Whether to include Gemini summary.

        Returns:
            AggregatedResponse with all agent results + pipeline status.
        """
        if zone not in VALID_ZONES:
            raise ValueError(f"Unknown zone: {zone}. Valid zones: {VALID_ZONES}")

        pipeline_start = time.time()

        # Build shared context
        zone_state = plant_state_service.get_zone_state(zone)
        context: Dict[str, Any] = {
            "zone": zone,
            "zone_state": zone_state,
        }

        # Determine which agents to run
        agents = AGENT_PIPELINE
        if agents_to_run:
            agents = [a for a in AGENT_PIPELINE if a.name in agents_to_run]

        # Build pipeline steps for visualization
        pipeline: List[PipelineStep] = [
            PipelineStep(
                agent_name=a.name,
                display_name=a.display_name,
                icon=a.icon,
                status="pending",
                order=i,
            )
            for i, a in enumerate(agents)
        ]

        # Execute agents sequentially
        results: List[Dict[str, Any]] = []

        for i, agent in enumerate(agents):
            pipeline[i].status = "running"

            result = await agent.run(context)
            results.append(result)

            # Update pipeline status
            pipeline[i].status = result.get("status", "completed")
            pipeline[i].duration_ms = result.get("duration_ms", 0.0)

        # Aggregate results
        aggregated = await response_aggregator.aggregate(
            results=results,
            include_summary=include_summary,
        )

        total_duration = round((time.time() - pipeline_start) * 1000, 2)

        # Get zone name
        zone_name = zone_state.zone_name if zone_state else zone

        return AggregatedResponse(
            zone=zone,
            zone_name=zone_name,
            results=aggregated["results"],
            pipeline=[p.model_dump() for p in pipeline],
            overall_summary=aggregated.get("overall_summary"),
            total_duration_ms=total_duration,
            agents_completed=aggregated["agents_completed"],
            agents_failed=aggregated["agents_failed"],
            analyzed_at=datetime.utcnow().isoformat(),
        )


# Singleton
agent_manager = AgentManager()
