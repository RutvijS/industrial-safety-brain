"""
rag.py -- REST endpoints for Incident Intelligence + RAG.

POST /incident-intelligence  - Evidence-backed risk explanation
POST /ingest-documents       - Upload and ingest documents
GET  /documents              - List indexed documents
GET  /documents/{doc_id}     - Document metadata
"""

from datetime import datetime
from typing import List, Optional

# pyrefly: ignore [missing-import]
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.models.rag_models import (
    DocumentInfo,
    IncidentIntelligenceRequest,
    IncidentIntelligenceResponse,
    IngestResponse,
)
from app.rag.chunker import chunk_documents
from app.rag.document_loader import load_from_bytes
from app.rag.embedding_service import embedding_service
from app.rag.vector_store import vector_store
from app.services.incident_intelligence_service import incident_intelligence_service
from app.services.plant_state_service import plant_state_service, VALID_ZONES
from app.services.risk_engine import risk_engine

router = APIRouter(tags=["Incident Intelligence"])


@router.post("/incident-intelligence", response_model=IncidentIntelligenceResponse)
async def run_incident_intelligence(
    request: IncidentIntelligenceRequest,
) -> IncidentIntelligenceResponse:
    """Run incident intelligence analysis for a zone.

    1. Gets zone state from PlantStateService
    2. Runs risk analysis via RiskEngine
    3. Passes risk assessment to IncidentIntelligenceService
    4. Returns evidence-backed explanation with citations
    """
    if request.zone not in VALID_ZONES:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown zone: {request.zone}. Valid zones: {VALID_ZONES}",
        )

    try:
        # Get zone state and run risk analysis
        zone_state = plant_state_service.get_zone_state(request.zone)
        assessment = risk_engine.analyze_zone(zone_state)

        # Run incident intelligence
        return await incident_intelligence_service.analyze(
            assessment=assessment,
            include_explanation=request.include_explanation,
        )

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Incident intelligence analysis failed: {e}",
        )


@router.post("/ingest-documents", response_model=IngestResponse)
async def ingest_documents(
    files: List[UploadFile] = File(...),
    document_type: str = Form(default="General"),
) -> IngestResponse:
    """Upload and ingest one or more documents into the vector store.

    Supports PDF, TXT, and Markdown files.
    """
    all_doc_infos: List[DocumentInfo] = []
    total_chunks = 0

    for file in files:
        try:
            content = await file.read()
            filename = file.filename or "unknown"

            # Load and parse document
            raw_docs = load_from_bytes(content, filename, document_type)

            # Chunk the documents
            chunks = chunk_documents(raw_docs)

            if not chunks:
                continue

            # Generate embeddings
            texts = [c.content for c in chunks]
            embeddings = embedding_service.embed_batch(texts)

            # Store in vector database
            added = vector_store.add_chunks(chunks, embeddings)
            total_chunks += added

            all_doc_infos.append(DocumentInfo(
                doc_id=filename,
                source_filename=filename,
                document_type=document_type,
                title=chunks[0].title if chunks else filename,
                chunk_count=added,
                page_count=max(c.page_number for c in chunks) if chunks else 1,
            ))

        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to ingest {file.filename}: {e}",
            )

    return IngestResponse(
        status="success",
        documents_processed=len(all_doc_infos),
        chunks_created=total_chunks,
        documents=all_doc_infos,
    )


@router.get("/documents", response_model=List[DocumentInfo])
async def list_documents() -> List[DocumentInfo]:
    """List all indexed documents in the vector store."""
    try:
        docs = vector_store.list_documents()
        return [DocumentInfo(**d) for d in docs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {e}")


@router.get("/documents/{doc_id}")
async def get_document_info(doc_id: str) -> dict:
    """Get metadata for a specific indexed document."""
    try:
        docs = vector_store.list_documents()
        for d in docs:
            if d.get("doc_id") == doc_id or d.get("source_filename") == doc_id:
                return d
        raise HTTPException(status_code=404, detail=f"Document not found: {doc_id}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get document: {e}")
