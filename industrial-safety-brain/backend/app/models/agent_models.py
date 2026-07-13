"""
agent_models.py -- Pydantic models for the Agentic AI Orchestrator.

These models define the request/response structure for multi-agent analysis.
"""

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


class AgentRequest(BaseModel):
    """Input for multi-agent analysis."""

    zone: str = Field(description="Zone to analyze (e.g. Zone A)")
    agents_to_run: Optional[List[str]] = Field(
        default=None,
        description="Specific agents to run. None = run all.",
    )
    include_summary: bool = Field(
        default=True,
        description="Whether to include Gemini summary.",
    )


class AgentStatus(BaseModel):
    """Status of a single agent execution."""

    agent_name: str
    status: str = Field(description="completed, failed, skipped")
    duration_ms: float = 0.0
    error: Optional[str] = None


class AgentResult(BaseModel):
    """Output of a single agent."""

    agent_name: str
    agent_type: str = ""
    status: str = "completed"
    data: Dict[str, Any] = Field(default_factory=dict)
    duration_ms: float = 0.0
    error: Optional[str] = None


class PipelineStep(BaseModel):
    """A step in the agent pipeline visualization."""

    agent_name: str
    display_name: str = ""
    icon: str = ""
    status: str = "pending"
    duration_ms: float = 0.0
    order: int = 0


class AggregatedResponse(BaseModel):
    """Complete multi-agent analysis output."""

    zone: str
    zone_name: str = ""
    results: List[AgentResult] = Field(default_factory=list)
    pipeline: List[PipelineStep] = Field(default_factory=list)
    overall_summary: Optional[str] = None
    total_duration_ms: float = 0.0
    agents_completed: int = 0
    agents_failed: int = 0
    analyzed_at: str = ""
