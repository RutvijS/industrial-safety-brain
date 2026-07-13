"""
vector_store.py -- ChromaDB wrapper for document chunk storage and retrieval.

Designed with an abstract interface so Pinecone/Qdrant can replace
ChromaDB without changing business logic.
"""

import os
from typing import Dict, List, Optional

from app.models.rag_models import DocumentChunk, RetrievedDocument


# ChromaDB collection name
COLLECTION_NAME = "safety_documents"

# Persist directory (relative to backend/)
CHROMA_PERSIST_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "chroma_db"
)


class VectorStore:
    """ChromaDB-backed vector store for RAG.

    Interface is abstract enough to swap in Pinecone or Qdrant
    by reimplementing this class alone.
    """

    def __init__(self) -> None:
        self._client = None
        self._collection = None

    def _ensure_init(self) -> None:
        """Lazy-initialize ChromaDB client and collection."""
        if self._client is not None:
            return

        try:
            # pyrefly: ignore [missing-import]
            import chromadb
            # pyrefly: ignore [missing-import]
            from chromadb.config import Settings as ChromaSettings
        except ImportError:
            raise ImportError(
                "chromadb is required. Install: pip install chromadb"
            )

        persist_dir = os.path.normpath(CHROMA_PERSIST_DIR)
        os.makedirs(persist_dir, exist_ok=True)

        self._client = chromadb.Client(ChromaSettings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=persist_dir,
            anonymized_telemetry=False,
        ))

        self._collection = self._client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    def add_chunks(
        self,
        chunks: List[DocumentChunk],
        embeddings: List[List[float]],
    ) -> int:
        """Add document chunks with their embeddings.

        Returns the number of chunks added.
        """
        self._ensure_init()

        ids = []
        documents = []
        metadatas = []

        for i, chunk in enumerate(chunks):
            chunk_id = f"{chunk.source_filename}__chunk_{chunk.chunk_index}"
            ids.append(chunk_id)
            documents.append(chunk.content)
            metadatas.append({
                "source_filename": chunk.source_filename,
                "document_type": chunk.document_type,
                "page_number": chunk.page_number,
                "title": chunk.title,
                "section": chunk.section,
                "chunk_index": chunk.chunk_index,
            })

        self._collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

        return len(ids)

    def query(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        where_filter: Optional[Dict] = None,
    ) -> List[RetrievedDocument]:
        """Search for similar chunks.

        Args:
            query_embedding: The query vector.
            top_k: Number of results to return.
            where_filter: ChromaDB metadata filter (e.g. {"document_type": "Incident Report"}).

        Returns:
            List of RetrievedDocument sorted by relevance.
        """
        self._ensure_init()

        kwargs = {
            "query_embeddings": [query_embedding],
            "n_results": top_k,
            "include": ["documents", "metadatas", "distances"],
        }
        if where_filter:
            kwargs["where"] = where_filter

        try:
            results = self._collection.query(**kwargs)
        except Exception:
            return []

        documents: List[RetrievedDocument] = []

        if not results or not results.get("documents"):
            return documents

        for i, doc_text in enumerate(results["documents"][0]):
            meta = results["metadatas"][0][i] if results.get("metadatas") else {}
            distance = results["distances"][0][i] if results.get("distances") else 1.0
            # ChromaDB returns cosine distance; convert to similarity
            relevance = max(0.0, 1.0 - distance)

            documents.append(RetrievedDocument(
                content=doc_text,
                source_filename=meta.get("source_filename", ""),
                document_type=meta.get("document_type", ""),
                page_number=meta.get("page_number", 1),
                title=meta.get("title", ""),
                section=meta.get("section", ""),
                relevance_score=round(relevance, 4),
            ))

        return documents

    def get_document_count(self) -> int:
        """Return total number of chunks in the store."""
        self._ensure_init()
        return self._collection.count()

    def list_documents(self) -> List[Dict]:
        """List unique source documents with metadata."""
        self._ensure_init()

        try:
            all_data = self._collection.get(include=["metadatas"])
        except Exception:
            return []

        if not all_data or not all_data.get("metadatas"):
            return []

        # Group by source filename
        doc_map: Dict[str, Dict] = {}
        for i, meta in enumerate(all_data["metadatas"]):
            fname = meta.get("source_filename", "unknown")
            if fname not in doc_map:
                doc_map[fname] = {
                    "doc_id": all_data["ids"][i].split("__chunk_")[0] if all_data.get("ids") else fname,
                    "source_filename": fname,
                    "document_type": meta.get("document_type", ""),
                    "title": meta.get("title", ""),
                    "chunk_count": 0,
                    "page_count": meta.get("page_number", 1),
                }
            doc_map[fname]["chunk_count"] += 1
            doc_map[fname]["page_count"] = max(
                doc_map[fname]["page_count"],
                meta.get("page_number", 1),
            )

        return list(doc_map.values())

    def delete_document(self, source_filename: str) -> int:
        """Delete all chunks for a specific document. Returns count deleted."""
        self._ensure_init()
        try:
            all_data = self._collection.get(
                where={"source_filename": source_filename},
                include=[],
            )
            if all_data and all_data.get("ids"):
                self._collection.delete(ids=all_data["ids"])
                return len(all_data["ids"])
        except Exception:
            pass
        return 0


# Singleton
vector_store = VectorStore()
