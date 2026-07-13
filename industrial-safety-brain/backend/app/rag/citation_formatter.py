"""
citation_formatter.py -- Formats citations from retrieved documents.

Creates structured, traceable citations so every claim
can be traced back to its source document.
"""

from typing import List

from app.models.rag_models import Citation, RetrievedDocument


def format_citations(documents: List[RetrievedDocument]) -> List[Citation]:
    """Convert retrieved documents into structured citations.

    Args:
        documents: List of retrieved document chunks.

    Returns:
        List of Citation objects with source, page, section, and excerpt.
    """
    citations: List[Citation] = []

    for doc in documents:
        # Create a short excerpt (first 200 chars)
        excerpt = doc.content[:200].strip()
        if len(doc.content) > 200:
            excerpt += "..."

        citations.append(Citation(
            source=doc.title or doc.source_filename,
            document_type=doc.document_type,
            page=doc.page_number,
            section=doc.section,
            excerpt=excerpt,
            relevance=doc.relevance_score,
        ))

    return citations


def format_citation_text(citations: List[Citation]) -> str:
    """Format citations as a readable text block for prompts."""
    if not citations:
        return "No citations available."

    lines = []
    for i, c in enumerate(citations, 1):
        lines.append(
            f"[{i}] {c.source} "
            f"(Type: {c.document_type}, Page: {c.page}, Section: {c.section}) "
            f"- Relevance: {c.relevance:.0%}"
        )
    return "\n".join(lines)
