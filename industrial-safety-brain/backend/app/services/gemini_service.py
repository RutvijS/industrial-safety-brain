import asyncio
import logging
import time

# pyrefly: ignore [missing-import]
import google.generativeai as genai
from app.config import settings

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
MAX_RETRIES = 3
BASE_DELAY_SECONDS = 2  # 2s, 4s, 8s exponential backoff


class GeminiService:
    """Handles all communication with the Google Gemini API.

    Uses lazy initialisation so the app can start even if the key is
    missing — the error surfaces only when /chat is actually called.

    Includes automatic retry with exponential backoff for rate limits.
    """

    def __init__(self) -> None:
        self._model = None

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

    async def generate_response(self, message: str) -> str:
        """Send a message to Gemini and return the text response.

        Retries up to 3 times with exponential backoff on rate limit errors.
        Non-rate-limit errors are raised immediately.
        """
        if self._model is None:
            self._init_model()

        last_error = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = self._model.generate_content(message)
                return response.text
            except Exception as e:
                last_error = e
                if self._is_rate_limit_error(e) and attempt < MAX_RETRIES:
                    delay = BASE_DELAY_SECONDS * (2 ** (attempt - 1))
                    logger.warning(
                        "Gemini rate limit hit (attempt %d/%d). Retrying in %ds...",
                        attempt, MAX_RETRIES, delay,
                    )
                    await asyncio.sleep(delay)
                else:
                    raise

        # Should not reach here, but just in case
        raise last_error


gemini_service = GeminiService()

