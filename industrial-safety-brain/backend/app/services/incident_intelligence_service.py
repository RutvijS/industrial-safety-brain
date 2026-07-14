"""
incident_intelligence_service.py -- Orchestrates the RAG pipeline.

Architecture:
    RiskAssessment + ZoneState
        -> Retriever (semantic search)
        -> PromptBuilder (grounded prompt)
        -> GeminiService (explanation)
        -> CitationFormatter (traceable citations)
        -> IncidentIntelligenceResponse

IMPORTANT: This service NEVER calculates risk.
Risk Engine remains the single source of truth.
This service ONLY provides evidence-backed explanations.
"""

from datetime import datetime
from typing import List

from app.models.rag_models import (
    Citation,
    IncidentIntelligenceResponse,
    LessonLearned,
    RetrievedDocument,
)
from app.models.risk_models import ZoneRiskAssessment
from app.rag.citation_formatter import format_citations
from app.rag.prompt_builder import build_prompt
from app.rag.retriever import retriever
from app.rag.vector_store import vector_store


# Retrieval categories and their top-K settings
RETRIEVAL_CATEGORIES = {
    "Incident Report": 3,
    "Near Miss": 2,
    "SOP": 2,
    "OISD Guideline": 2,
    "Factory Act": 1,
    "DGMS Guideline": 1,
    "Emergency Procedure": 1,
}


class IncidentIntelligenceService:
    """Provides evidence-backed explanations for risk assessments.

    Uses RAG to retrieve relevant historical incidents, regulations,
    and SOPs, then sends them to Gemini for grounded explanation.
    """

    def _build_query(self, assessment: ZoneRiskAssessment) -> str:
        """Build a semantic search query from the risk assessment."""
        parts = [
            f"Industrial safety risk in {assessment.zone_name}",
            f"zone type: {assessment.zone_name}",
            f"risk level: {assessment.overall_risk}",
        ]

        # Add compound risk names
        for r in assessment.detected_compound_risks:
            parts.append(r.name)

        # Add key risk factors
        for f in assessment.risk_factors:
            if f.status in ("Warning", "Critical"):
                parts.append(f"{f.name} {f.status}")

        return ". ".join(parts)

    def _categorize_results(
        self,
        all_docs: List[RetrievedDocument],
    ) -> dict:
        """Sort retrieved documents into categories."""
        incidents = []
        regulations = []
        supporting = []

        for doc in all_docs:
            dtype = doc.document_type.lower()
            if "incident" in dtype or "near miss" in dtype:
                incidents.append(doc)
            elif any(t in dtype for t in ["oisd", "factory act", "dgms", "regulation"]):
                regulations.append(doc)
            else:
                supporting.append(doc)

        return {
            "incidents": incidents,
            "regulations": regulations,
            "supporting": supporting,
        }

    def _extract_lessons(
        self,
        incidents: List[RetrievedDocument],
    ) -> List[LessonLearned]:
        """Extract lessons learned from retrieved incident reports."""
        lessons: List[LessonLearned] = []

        for doc in incidents:
            # Extract a lesson from each incident document
            content_preview = doc.content[:300].strip()
            lessons.append(LessonLearned(
                lesson=content_preview,
                source=doc.source_filename,
                incident_reference=doc.title,
                applicability=f"Relevant to {doc.document_type} analysis",
            ))

        return lessons

    async def analyze(
        self,
        assessment: ZoneRiskAssessment,
        include_explanation: bool = True,
    ) -> IncidentIntelligenceResponse:
        """Run the full incident intelligence pipeline.

        1. Build semantic query from risk assessment
        2. Retrieve relevant documents (multi-category)
        3. Build grounded prompt
        4. Send to Gemini for explanation
        5. Format citations

        Args:
            assessment: Zone risk assessment from the Risk Engine.
            include_explanation: Whether to call Gemini for explanation.

        Returns:
            Complete IncidentIntelligenceResponse with evidence.
        """
        # Step 1: Build query
        query = self._build_query(assessment)

        # Step 2: Retrieve documents
        doc_count = vector_store.get_document_count()

        all_docs: List[RetrievedDocument] = []
        if doc_count > 0:
            # Try multi-category retrieval
            try:
                category_results = retriever.retrieve_multi_category(
                    query=query,
                    categories=RETRIEVAL_CATEGORIES,
                )
                for docs in category_results.values():
                    all_docs.extend(docs)
            except Exception:
                # Fallback to simple retrieval
                all_docs = retriever.retrieve_all(query=query, top_k=10)

        # Step 3: Categorize results
        categorized = self._categorize_results(all_docs)

        # Step 4: Extract lessons
        lessons = self._extract_lessons(categorized["incidents"])

        # Step 5: Format citations
        citations = format_citations(all_docs)

        # Step 6: LLM explanation is now handled by LLMSummaryService.
        # This service returns structured data only.
        explanation = None

        return IncidentIntelligenceResponse(
            zone=assessment.zone,
            zone_name=assessment.zone_name,
            risk_level=assessment.overall_risk,
            risk_score=assessment.risk_score,
            similar_incidents=categorized["incidents"],
            lessons_learned=lessons,
            related_regulations=categorized["regulations"],
            supporting_documents=categorized["supporting"],
            citations=citations,
            llm_explanation=explanation,
            retrieval_count=len(all_docs),
            analyzed_at=datetime.utcnow().isoformat(),
        )


# Singleton
incident_intelligence_service = IncidentIntelligenceService()
