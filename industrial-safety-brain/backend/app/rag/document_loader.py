"""
document_loader.py -- Loads documents (PDF, TXT, Markdown) for RAG ingestion.

Extracts text and metadata from supported file formats.
Each document yields a list of pages/sections with metadata attached.
"""

import os
from typing import List, Optional

from app.models.rag_models import RawDocument, DocumentMetadata


# Supported file extensions
SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md"}


def _load_pdf(filepath: str, doc_type: str) -> List[RawDocument]:
    """Load a PDF file and extract text per page."""
    try:
        # pyrefly: ignore [missing-import]
        from PyPDF2 import PdfReader
    except ImportError:
        raise ImportError("PyPDF2 is required for PDF support. Install: pip install PyPDF2")

    reader = PdfReader(filepath)
    filename = os.path.basename(filepath)
    documents: List[RawDocument] = []

    for page_num, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        text = text.strip()
        if not text:
            continue

        documents.append(RawDocument(
            content=text,
            metadata=DocumentMetadata(
                source_filename=filename,
                document_type=doc_type,
                page_number=page_num,
                total_pages=len(reader.pages),
                title=filename.replace(".pdf", "").replace("_", " ").title(),
                section=f"Page {page_num}",
            ),
        ))

    return documents


def _load_text(filepath: str, doc_type: str) -> List[RawDocument]:
    """Load a TXT or Markdown file as a single document."""
    filename = os.path.basename(filepath)
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read().strip()

    if not content:
        return []

    ext = os.path.splitext(filename)[1]
    title = filename.replace(ext, "").replace("_", " ").replace("-", " ").title()

    return [RawDocument(
        content=content,
        metadata=DocumentMetadata(
            source_filename=filename,
            document_type=doc_type,
            page_number=1,
            total_pages=1,
            title=title,
            section="Full Document",
        ),
    )]


def load_document(
    filepath: str,
    doc_type: str = "General",
) -> List[RawDocument]:
    """Load a document from disk and extract text with metadata.

    Args:
        filepath: Absolute or relative path to the file.
        doc_type: Document category (Incident Report, SOP, OISD Guideline, etc.)

    Returns:
        List of RawDocument objects (one per page/section).

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file extension is not supported.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Document not found: {filepath}")

    ext = os.path.splitext(filepath)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type: {ext}. Supported: {SUPPORTED_EXTENSIONS}"
        )

    if ext == ".pdf":
        return _load_pdf(filepath, doc_type)
    else:
        return _load_text(filepath, doc_type)


def load_from_bytes(
    content: bytes,
    filename: str,
    doc_type: str = "General",
) -> List[RawDocument]:
    """Load a document from in-memory bytes (for file upload endpoints).

    Writes to a temp file, loads, then cleans up.
    """
    import tempfile

    ext = os.path.splitext(filename)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type: {ext}. Supported: {SUPPORTED_EXTENSIONS}"
        )

    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        return load_document(tmp_path, doc_type)
    finally:
        os.unlink(tmp_path)
