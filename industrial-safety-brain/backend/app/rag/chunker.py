"""
chunker.py -- Splits documents into overlapping chunks for vector storage.

Uses a sliding-window approach with configurable chunk size and overlap.
Preserves all metadata from the source document on each chunk.
"""

from typing import List

from app.models.rag_models import DocumentChunk, RawDocument

# Defaults (configurable)
DEFAULT_CHUNK_SIZE = 800       # characters per chunk
DEFAULT_CHUNK_OVERLAP = 150    # overlap between adjacent chunks
MIN_CHUNK_SIZE = 50            # skip chunks smaller than this


def chunk_document(
    doc: RawDocument,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> List[DocumentChunk]:
    """Split a RawDocument into overlapping chunks.

    Args:
        doc: A RawDocument with content and metadata.
        chunk_size: Maximum characters per chunk.
        chunk_overlap: Overlap between adjacent chunks.

    Returns:
        List of DocumentChunk objects with preserved metadata.
    """
    text = doc.content.strip()
    if len(text) < MIN_CHUNK_SIZE:
        return []

    chunks: List[DocumentChunk] = []
    start = 0
    chunk_index = 0

    while start < len(text):
        end = start + chunk_size

        # Try to break at sentence boundary
        if end < len(text):
            # Look for the last period, newline, or sentence break
            for sep in [". ", ".\n", "\n\n", "\n", ". "]:
                last_sep = text.rfind(sep, start, end)
                if last_sep > start + MIN_CHUNK_SIZE:
                    end = last_sep + len(sep)
                    break

        chunk_text = text[start:end].strip()

        if len(chunk_text) >= MIN_CHUNK_SIZE:
            chunks.append(DocumentChunk(
                content=chunk_text,
                chunk_index=chunk_index,
                source_filename=doc.metadata.source_filename,
                document_type=doc.metadata.document_type,
                page_number=doc.metadata.page_number,
                title=doc.metadata.title,
                section=doc.metadata.section,
            ))
            chunk_index += 1

        # Advance with overlap
        start = end - chunk_overlap if end < len(text) else len(text)

    return chunks


def chunk_documents(
    docs: List[RawDocument],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> List[DocumentChunk]:
    """Chunk multiple documents."""
    all_chunks: List[DocumentChunk] = []
    for doc in docs:
        all_chunks.extend(chunk_document(doc, chunk_size, chunk_overlap))
    return all_chunks
