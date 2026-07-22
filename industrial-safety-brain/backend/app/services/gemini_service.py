import asyncio
import logging
import random
import time
import traceback

# pyrefly: ignore [missing-import]
import google.generativeai as genai
from app.config import settings
from app.exceptions import RateLimitError

logger = logging.getLogger("safety_brain.gemini")

# System instruction that scopes the AI as an industrial safety expert
SYSTEM_INSTRUCTION = (
    "You are SafetyBrain AI, an expert industrial safety assistant. "
    "You provide accurate, concise guidance on workplace safety, "
    "hazard identification, OSHA regulations, risk assessments, "
    "PPE requirements, and incident prevention. "
    "Always prioritize worker safety in your responses."
)

# Retry configuration
MAX_RETRIES = 4
BASE_DELAY_SECONDS = 3  # 3s, 6s, 12s, 24s exponential backoff


class GeminiService:
    """Handles all communication with the Google Gemini API.

    Uses lazy initialisation so the app can start even if the key is
    missing — the error surfaces only when /chat is actually called.

    Includes:
    - Automatic retry with exponential backoff + jitter for rate limits.
    - Respects Retry-After hints from the API when available.
    - Concurrency control: only ONE Gemini call at a time (semaphore).
    - Global cooldown: after a 429, ALL subsequent calls wait.
    """

    def __init__(self) -> None:
        self._model = None
        self.call_count: int = 0  # Track total Gemini calls for verification

        # Concurrency control: serialize all Gemini requests
        self._semaphore = asyncio.Semaphore(1)

        # Global cooldown: timestamp until which no calls should be attempted
        self._cooldown_until: float = 0.0

    def _init_model(self) -> None:
        """Configure the SDK and create the model on first use."""
        settings.validate()
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self._model = genai.GenerativeModel(
            model_name=settings.GEMINI_MODEL,
            system_instruction=SYSTEM_INSTRUCTION,
        )

    @staticmethod
    def _is_rate_limit_error(error: Exception) -> bool:
        """Check if the exception is a rate limit / quota error."""
        msg = str(error).lower()
        return any(kw in msg for kw in ("quota", "resource", "rate", "429", "exhausted"))

    @staticmethod
    def _extract_retry_after(error: Exception) -> int | None:
        """Extract Retry-After delay from error metadata if available.

        Google API errors sometimes include retry info in error details
        or in the string representation.
        """
        import re

        # Check for google.api_core style errors with retry_info
        metadata = getattr(error, "metadata", None)
        if metadata:
            try:
                for key, value in metadata:
                    if key.lower() == "retry-after":
                        try:
                            return int(value)
                        except (ValueError, TypeError):
                            pass
            except (TypeError, ValueError):
                pass  # metadata not iterable

        # Check for retry delay in error message (e.g., "retry after 30 seconds")
        msg = str(error).lower()
        match = re.search(r"retry\s*(?:after|in)\s*(\d+)\s*s", msg)
        if match:
            return int(match.group(1))

        return None

    @property
    def cooldown_remaining(self) -> float:
        """Seconds remaining in the global cooldown, or 0 if none."""
        return max(0.0, self._cooldown_until - time.monotonic())

    def _set_cooldown(self, seconds: float) -> None:
        """Set a global cooldown — all subsequent calls will wait."""
        self._cooldown_until = time.monotonic() + seconds
        logger.warning("Global cooldown set: %.1fs", seconds)

    async def generate_response(self, message: str, caller: str = "unknown") -> str:
        """Send a message to Gemini and return the text response.

        Serialized via semaphore — only one request at a time.
        Retries up to MAX_RETRIES times with exponential backoff on rate limit errors.
        Respects Retry-After hints from the API.
        Non-rate-limit errors are raised immediately.

        Args:
            message: The prompt to send to Gemini.
            caller: Identifier for the calling service (for logging).

        Raises:
            RateLimitError: When all retries are exhausted due to rate limiting.
        """
        if self._model is None:
            self._init_model()

        # Wait for the semaphore — serializes all Gemini calls
        queue_start = time.monotonic()
        async with self._semaphore:
            queued_time = time.monotonic() - queue_start

            self.call_count += 1
            call_id = self.call_count

            logger.info(
                "Gemini call #%d | caller=%s | prompt=%d chars | queued=%.1fs",
                call_id, caller, len(message), queued_time,
            )

            # Respect global cooldown (from a previous 429)
            cooldown = self.cooldown_remaining
            if cooldown > 0:
                logger.info(
                    "Gemini call #%d | global cooldown active, waiting %.1fs",
                    call_id, cooldown,
                )
                await asyncio.sleep(cooldown)

            call_start = time.monotonic()
            last_error = None

            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    response = self._model.generate_content(message)
                    elapsed = time.monotonic() - call_start

                    logger.info(
                        "Gemini call #%d | SUCCESS | attempt=%d | elapsed=%.1fs",
                        call_id, attempt, elapsed,
                    )
                    return response.text

                except Exception as e:
                    last_error = e
                    elapsed = time.monotonic() - call_start

                    if self._is_rate_limit_error(e):
                        # Extract Retry-After or compute backoff
                        retry_after = self._extract_retry_after(e)
                        if retry_after is not None:
                            delay = float(retry_after)
                        else:
                            delay = BASE_DELAY_SECONDS * (2 ** (attempt - 1))
                            # Add jitter (±25%) to avoid thundering herd
                            delay = delay * (0.75 + random.random() * 0.5)

                        if attempt < MAX_RETRIES:
                            # Set global cooldown so other queued requests also wait
                            self._set_cooldown(delay)

                            logger.warning(
                                "Gemini call #%d | 429 RATE LIMIT | attempt=%d/%d | "
                                "retrying in %.1fs | elapsed=%.1fs | caller=%s",
                                call_id, attempt, MAX_RETRIES, delay, elapsed, caller,
                            )
                            await asyncio.sleep(delay)
                        else:
                            # All retries exhausted
                            self._set_cooldown(30.0)  # 30s cooldown for next caller

                            logger.error(
                                "Gemini call #%d | 429 EXHAUSTED | all %d retries failed | "
                                "elapsed=%.1fs | caller=%s",
                                call_id, MAX_RETRIES, elapsed, caller,
                            )
                            raise RateLimitError(
                                message="Gemini API rate limit exceeded. Please wait and try again.",
                                details=f"All {MAX_RETRIES} retries exhausted after {elapsed:.1f}s. "
                                        f"Retry after: {retry_after or 30}s",
                            )
                    else:
                        # Non-rate-limit error — raise immediately
                        logger.error(
                            "Gemini call #%d | ERROR | attempt=%d | elapsed=%.1fs | "
                            "caller=%s | %s: %s",
                            call_id, attempt, elapsed, caller,
                            type(e).__name__, e,
                        )
                        raise

            # Should not reach here, but just in case
            raise last_error


gemini_service = GeminiService()
