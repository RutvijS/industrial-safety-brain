"""
agent.py -- REST endpoint for the Agentic AI Orchestrator.

POST /agent-analysis  — Run multi-agent analysis on a zone
"""

# pyrefly: ignore [missing-import]
from fastapi import APIRouter, HTTPException

from app.models.agent_models import AgentRequest, AggregatedResponse
from app.agents.agent_manager import agent_manager

router = APIRouter(tags=["Agent Orchestrator"])


@router.post("/agent-analysis", response_model=AggregatedResponse)
async def run_agent_analysis(request: AgentRequest) -> AggregatedResponse:
    """Run multi-agent analysis for a zone.

    Executes the agent pipeline:
    Risk → Incident Intelligence → Knowledge Graph → Compliance → Emergency

    Each agent wraps an existing service. If one fails, others continue.
    """
    try:
        return await agent_manager.analyze(
            zone=request.zone,
            agents_to_run=request.agents_to_run,
            include_summary=request.include_summary,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Agent analysis failed: {e}",
        )
