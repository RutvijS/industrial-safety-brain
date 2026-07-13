"""
embedding_service.py -- Generates text embeddings for RAG.

Uses Google's embedding model by default. Provider-agnostic interface
so Gemini, OpenAI, or any other provider can be swapped in later.
"""

from typing import List

from app.config import settings


class EmbeddingService:
    """Generates embeddings using Google's generative AI embedding model.

    The interface is provider-agnostic: swap the implementation
    without changing callers.
    """

    def __init__(self, model_name: str = "models/embedding-001") -> None:
        self._model_name = model_name
        self._initialized = False

    def _ensure_init(self) -> None:
        if not self._initialized:
            # pyrefly: ignore [missing-import]
            import google.generativeai as genai
            settings.validate()
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self._initialized = True

    def embed_text(self, text: str) -> List[float]:
        """Generate an embedding for a single text string."""
        self._ensure_init()
        # pyrefly: ignore [missing-import]
        import google.generativeai as genai
        result = genai.embed_content(
            model=self._model_name,
            content=text,
            task_type="retrieval_document",
        )
        return result["embedding"]

    def embed_query(self, query: str) -> List[float]:
        """Generate an embedding for a search query."""
        self._ensure_init()
        # pyrefly: ignore [missing-import]
        import google.generativeai as genai
        result = genai.embed_content(
            model=self._model_name,
            content=query,
            task_type="retrieval_query",
        )
        return result["embedding"]

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a batch of texts."""
        return [self.embed_text(t) for t in texts]


# Singleton
embedding_service = EmbeddingService()
