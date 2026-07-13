"""
retriever.py -- Semantic retrieval from the vector store.

Configurable top-K, metadata filtering, and multi-category retrieval.
"""

from typing import Dict, List, Optional

from app.models.rag_models import RetrievedDocument
from app.rag.embedding_service import embedding_service
from app.rag.vector_store import vector_store

# Default retrieval settings
DEFAULT_TOP_K = 5


class Retriever:
    """Semantic retriever for RAG.

    Wraps embedding generation + vector store query into a
    clean retrieval interface.
    """

    def retrieve(
        self,
        query: str,
        top_k: int = DEFAULT_TOP_K,
        document_type: Optional[str] = None,
    ) -> List[RetrievedDocument]:
        """Retrieve documents semantically similar to the query.

        Args:
            query: Natural language search query.
            top_k: Maximum results to return.
            document_type: Optional filter (e.g. "Incident Report", "OISD Guideline").

        Returns:
            List of RetrievedDocument sorted by relevance.
        """
        query_embedding = embedding_service.embed_query(query)

        where_filter = None
        if document_type:
            where_filter = {"document_type": document_type}

        return vector_store.query(
            query_embedding=query_embedding,
            top_k=top_k,
            where_filter=where_filter,
        )

    def retrieve_multi_category(
        self,
        query: str,
        categories: Dict[str, int],
    ) -> Dict[str, List[RetrievedDocument]]:
        """Retrieve from multiple document categories.

        Args:
            query: Natural language search query.
            categories: Mapping of document_type -> top_k.
                Example: {"Incident Report": 3, "OISD Guideline": 2}

        Returns:
            Dict mapping category to list of results.
        """
        results: Dict[str, List[RetrievedDocument]] = {}
        query_embedding = embedding_service.embed_query(query)

        for doc_type, top_k in categories.items():
            docs = vector_store.query(
                query_embedding=query_embedding,
                top_k=top_k,
                where_filter={"document_type": doc_type},
            )
            results[doc_type] = docs

        return results

    def retrieve_all(
        self,
        query: str,
        top_k: int = DEFAULT_TOP_K,
    ) -> List[RetrievedDocument]:
        """Retrieve from all document types without filtering."""
        return self.retrieve(query=query, top_k=top_k, document_type=None)


# Singleton
retriever = Retriever()
