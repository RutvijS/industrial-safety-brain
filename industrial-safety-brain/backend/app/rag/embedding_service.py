"""
embedding_service.py -- Generates text embeddings for RAG.

Uses Google's embedding model by default. Provider-agnostic interface
so Gemini, OpenAI, or any other provider can be swapped in later.

Supports true batch embedding and automatic retry with exponential
backoff for rate limit errors. Uses async sleep to avoid blocking
the event loop.
"""

import asyncio
import logging
import random
import time
from typing import List

from app.config import settings

logger = logging.getLogger("safety_brain.embedding")

# Retry configuration for embedding API
MAX_RETRIES = 4
BASE_DELAY_SECONDS = 3

# Maximum texts per batch call (API limit)
BATCH_SIZE = 100


class EmbeddingService:
    """Generates embeddings using Google's generative AI embedding model.

    The interface is provider-agnostic: swap the implementation
    without changing callers.
    """

    def __init__(self, model_name: str = "models/gemini-embedding-001") -> None:
        self._model_name = model_name
        self._initialized = False

    def _ensure_init(self) -> None:
        if not self._initialized:
            # pyrefly: ignore [missing-import]
            import google.generativeai as genai
            settings.validate()
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self._initialized = True

    @staticmethod
    def _is_rate_limit_error(error: Exception) -> bool:
        """Check if the exception is a rate limit / quota error."""
        msg = str(error).lower()
        return any(kw in msg for kw in ("quota", "resource", "rate", "429", "exhausted"))

    def _check_gemini_cooldown(self) -> float:
        """Check if the global Gemini cooldown is active.

        Coordinates with GeminiService so embedding calls also respect
        rate limit signals from text generation.
        """
        try:
            from app.services.gemini_service import gemini_service
            return gemini_service.cooldown_remaining
        except Exception:
            return 0.0

    def _embed_with_retry(self, content, task_type: str):
        """Call embed_content with retry logic for rate limits.

        Args:
            content: A single string or list of strings to embed.
            task_type: 'retrieval_document' or 'retrieval_query'.

        Returns:
            The embedding result dict from the API.
        """
        # pyrefly: ignore [missing-import]
        import google.generativeai as genai

        # Check global cooldown before attempting
        cooldown = self._check_gemini_cooldown()
        if cooldown > 0:
            logger.info("Embedding: respecting global cooldown, waiting %.1fs", cooldown)
            time.sleep(cooldown)

        last_error = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                result = genai.embed_content(
                    model=self._model_name,
                    content=content,
                    task_type=task_type,
                )
                return result
            except Exception as e:
                last_error = e
                if self._is_rate_limit_error(e) and attempt < MAX_RETRIES:
                    delay = BASE_DELAY_SECONDS * (2 ** (attempt - 1))
                    # Add jitter (±25%)
                    delay = delay * (0.75 + random.random() * 0.5)

                    logger.warning(
                        "Embedding rate limit hit (attempt %d/%d). Retrying in %.1fs...",
                        attempt, MAX_RETRIES, delay,
                    )

                    # Signal global cooldown to GeminiService
                    try:
                        from app.services.gemini_service import gemini_service
                        gemini_service._set_cooldown(delay)
                    except Exception:
                        pass

                    time.sleep(delay)
                else:
                    raise

        raise last_error

    def embed_text(self, text: str) -> List[float]:
        """Generate an embedding for a single text string."""
        self._ensure_init()
        result = self._embed_with_retry(text, task_type="retrieval_document")
        return result["embedding"]

    def embed_query(self, query: str) -> List[float]:
        """Generate an embedding for a search query."""
        self._ensure_init()
        result = self._embed_with_retry(query, task_type="retrieval_query")
        return result["embedding"]

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a batch of texts.

        Uses the API's native batch support (passing a list of strings)
        instead of calling embed_text in a loop.  Falls back to
        per-text calls if batch embedding fails.
        """
        if not texts:
            return []

        self._ensure_init()

        all_embeddings: List[List[float]] = []

        # Process in chunks of BATCH_SIZE
        for i in range(0, len(texts), BATCH_SIZE):
            batch = texts[i : i + BATCH_SIZE]

            try:
                result = self._embed_with_retry(batch, task_type="retrieval_document")
                # When content is a list, result["embedding"] is a list of embeddings
                embeddings = result["embedding"]

                if isinstance(embeddings[0], list):
                    # Batch response: list of embedding vectors
                    all_embeddings.extend(embeddings)
                else:
                    # Single embedding returned (shouldn't happen for list input)
                    all_embeddings.append(embeddings)

            except Exception as e:
                logger.warning(
                    "Batch embedding failed for chunk %d-%d, falling back to per-text: %s",
                    i, i + len(batch), e,
                )
                # Fallback: embed one at a time
                for text in batch:
                    all_embeddings.append(self.embed_text(text))

        logger.info(
            "Embedded %d texts in %d batch call(s)",
            len(texts),
            (len(texts) + BATCH_SIZE - 1) // BATCH_SIZE,
        )

        return all_embeddings


# Singleton
embedding_service = EmbeddingService()
