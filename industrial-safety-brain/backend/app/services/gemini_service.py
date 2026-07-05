# pyrefly: ignore [missing-import]
import google.generativeai as genai
from app.config import settings

# System instruction that scopes the AI as an industrial safety expert
SYSTEM_INSTRUCTION = (
    "You are SafetyBrain AI, an expert industrial safety assistant. "
    "You provide accurate, concise guidance on workplace safety, "
    "hazard identification, OSHA regulations, risk assessments, "
    "PPE requirements, and incident prevention. "
    "Always prioritize worker safety in your responses."
)


class GeminiService:
    """Handles all communication with the Google Gemini API.

    Uses lazy initialisation so the app can start even if the key is
    missing — the error surfaces only when /chat is actually called.
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

    async def generate_response(self, message: str) -> str:
        """Send a message to Gemini and return the text response."""
        if self._model is None:
            self._init_model()
        response = self._model.generate_content(message)
        return response.text


gemini_service = GeminiService()
