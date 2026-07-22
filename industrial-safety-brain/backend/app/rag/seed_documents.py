"""
seed_documents.py -- Seeds ChromaDB with incident data from datasets on first launch.

Converts structured JSON incident records into rich text documents,
then uses the existing chunker + embedding service + vector store
pipeline to ingest them. Runs only when the collection is empty.
"""

import json
import logging
import os
from typing import List

from app.models.rag_models import DocumentChunk, RawDocument, DocumentMetadata
from app.rag.chunker import chunk_documents
from app.rag.embedding_service import embedding_service
from app.rag.vector_store import vector_store

logger = logging.getLogger("safety_brain")

# Path to the incidents dataset
INCIDENTS_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "datasets", "incidents", "incidents.json"
)


def _incident_to_text(incident: dict) -> str:
    """Convert a structured incident record into a rich text document."""
    return (
        f"INCIDENT REPORT: {incident['incident_id']}\n"
        f"\n"
        f"Date: {incident['date']}\n"
        f"Zone: {incident['zone']}\n"
        f"Equipment: {incident['equipment']}\n"
        f"Severity: {incident['severity']}\n"
        f"Injuries: {incident['injuries']}\n"
        f"\n"
        f"Description:\n"
        f"{incident['description']}\n"
        f"\n"
        f"Root Cause:\n"
        f"{incident['root_cause']}\n"
        f"\n"
        f"Corrective Action:\n"
        f"{incident['corrective_action']}\n"
        f"\n"
        f"Lessons Learned:\n"
        f"{incident['lessons_learned']}\n"
        f"\n"
        f"Related Regulation:\n"
        f"{incident['related_regulation']}\n"
    )


def _load_incidents() -> List[RawDocument]:
    """Load incidents from the JSON dataset and convert to RawDocuments."""
    incidents_path = os.path.normpath(INCIDENTS_PATH)

    if not os.path.exists(incidents_path):
        logger.warning("Incidents dataset not found at %s — skipping seed", incidents_path)
        return []

    with open(incidents_path, "r", encoding="utf-8") as f:
        incidents = json.load(f)

    raw_docs: List[RawDocument] = []
    for incident in incidents:
        text = _incident_to_text(incident)
        filename = f"{incident['incident_id']}.txt"
        raw_docs.append(RawDocument(
            content=text,
            metadata=DocumentMetadata(
                source_filename=filename,
                document_type="Incident Report",
                page_number=1,
                total_pages=1,
                title=f"{incident['incident_id']} — {incident['description'][:60]}",
                section=f"{incident['zone']} / {incident['equipment']}",
            ),
        ))

    return raw_docs


def seed_if_empty() -> None:
    """Seed ChromaDB with incident documents if the collection is empty.

    This is idempotent: it only runs when collection.count() == 0.
    """
    try:
        count = vector_store.get_document_count()
        if count > 0:
            logger.info("ChromaDB already has %d documents — skipping seed", count)
            return

        raw_docs = _load_incidents()
        if not raw_docs:
            logger.info("No incident documents to seed")
            return

        logger.info("Seeding %d incident documents into ChromaDB...", len(raw_docs))

        # Chunk the documents
        chunks = chunk_documents(raw_docs)
        if not chunks:
            logger.warning("Chunking produced 0 chunks — skipping seed")
            return

        # Generate embeddings
        texts = [c.content for c in chunks]
        embeddings = embedding_service.embed_batch(texts)

        # Store in vector database
        added = vector_store.add_chunks(chunks, embeddings)

        logger.info(
            "Seeded %d chunks from %d incidents into ChromaDB",
            added, len(raw_docs),
        )

    except Exception as e:
        logger.error("Failed to seed ChromaDB: %s", e)
