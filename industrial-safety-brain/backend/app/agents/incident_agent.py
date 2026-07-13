"""
incident_agent.py -- Incident Intelligence Agent.

Wraps the existing IncidentIntelligenceService (RAG).
Never duplicates retrieval or prompt logic.

Input:  Risk Assessment
Output: RAG results (similar incidents, lessons, citations)
"""

from typing import Any, Dict

from app.agents.base_agent import BaseAgent


class IncidentAgent(BaseAgent):
    """Wraps IncidentIntelligenceService for evidence-backed analysis."""

    name = "incident_agent"
    display_name = "Incident Intelligence Agent"
    icon = "📚"

    def validate(self, context: Dict[str, Any]) -> bool:
        return "risk_assessment" in context

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        from app.services.incident_intelligence_service import (
            incident_intelligence_service,
        )

        assessment = context["risk_assessment"]

        # Run incident intelligence (includes RAG retrieval + optional Gemini)
        result = await incident_intelligence_service.analyze(
            assessment=assessment,
            include_explanation=False,  # Gemini summary handled by aggregator
        )

        # Store for downstream
        context["incident_intelligence"] = result

        return {
            "similar_incidents": [
                {
                    "title": d.title or d.source_filename,
                    "document_type": d.document_type,
                    "relevance": d.relevance_score,
                    "content_preview": d.content[:200],
                }
                for d in result.similar_incidents
            ],
            "lessons_learned": [
                {"lesson": l.lesson[:200], "source": l.source}
                for l in result.lessons_learned
            ],
            "related_regulations": [
                {
                    "title": d.title or d.source_filename,
                    "document_type": d.document_type,
                    "relevance": d.relevance_score,
                }
                for d in result.related_regulations
            ],
            "citations_count": len(result.citations),
            "retrieval_count": result.retrieval_count,
        }
