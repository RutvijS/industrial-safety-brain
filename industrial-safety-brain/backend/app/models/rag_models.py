"""
rag_models.py -- Pydantic models for the RAG / Incident Intelligence module.

These models support document ingestion, retrieval, citation formatting,
and the final incident intelligence response.
"""

# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field
from typing import Dict, List, Optional


# ── Document Ingestion Models ───────────────────────────────

class DocumentMetadata(BaseModel):
    """Metadata attached to a source document."""

    source_filename: str
    document_type: str = Field(
        default="General",
        description="Incident Report, SOP, OISD Guideline, Factory Act, Near Miss, etc.",
    )
    page_number: int = 1
    total_pages: int = 1
    title: str = ""
    section: str = ""


class RawDocument(BaseModel):
    """A raw document loaded from disk (pre-chunking)."""

    content: str
    metadata: DocumentMetadata


class DocumentChunk(BaseModel):
    """A chunk of a document ready for embedding and storage."""

    content: str
    chunk_index: int = 0
    source_filename: str = ""
    document_type: str = ""
    page_number: int = 1
    title: str = ""
    section: str = ""


class DocumentInfo(BaseModel):
    """Info about an indexed document (for listing)."""

    doc_id: str
    source_filename: str
    document_type: str
    title: str
    chunk_count: int = 0
    page_count: int = 1


class IngestResponse(BaseModel):
    """Response after document ingestion."""

    status: str = "success"
    documents_processed: int = 0
    chunks_created: int = 0
    documents: List[DocumentInfo] = Field(default_factory=list)


# ── Retrieval Models ────────────────────────────────────────

class RetrievedDocument(BaseModel):
    """A document chunk retrieved from the vector store."""

    content: str
    source_filename: str = ""
    document_type: str = ""
    page_number: int = 1
    title: str = ""
    section: str = ""
    relevance_score: float = 0.0


class Citation(BaseModel):
    """A citation referencing a specific source."""

    source: str = Field(description="Filename or document title")
    document_type: str = ""
    page: int = 1
    section: str = ""
    excerpt: str = Field(default="", description="Relevant excerpt from the source")
    relevance: float = 0.0


# ── Intelligence Response Models ────────────────────────────

class SupportingEvidence(BaseModel):
    """Evidence supporting a risk assessment from retrieved documents."""

    evidence_type: str = Field(description="incident, regulation, sop, lesson")
    summary: str
    source: str
    relevance: float = 0.0


class LessonLearned(BaseModel):
    """A lesson learned from a historical incident or audit."""

    lesson: str
    source: str
    incident_reference: str = ""
    applicability: str = ""


class IncidentIntelligenceRequest(BaseModel):
    """Input for the incident intelligence endpoint."""

    zone: str = Field(description="Zone to analyze (e.g. Zone A)")
    include_explanation: bool = Field(
        default=True,
        description="Whether to include Gemini explanation",
    )


class IncidentIntelligenceResponse(BaseModel):
    """Complete incident intelligence output."""

    zone: str
    zone_name: str = ""
    risk_level: str = ""
    risk_score: int = 0
    similar_incidents: List[RetrievedDocument] = Field(default_factory=list)
    lessons_learned: List[LessonLearned] = Field(default_factory=list)
    related_regulations: List[RetrievedDocument] = Field(default_factory=list)
    supporting_documents: List[RetrievedDocument] = Field(default_factory=list)
    citations: List[Citation] = Field(default_factory=list)
    llm_explanation: Optional[str] = Field(
        default=None,
        description="Grounded explanation from Gemini using retrieved evidence only",
    )
    retrieval_count: int = 0
    analyzed_at: str = ""
