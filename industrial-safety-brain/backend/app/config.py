import os

# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings loaded from environment variables.

    All secrets and tunables live here — nothing is hardcoded elsewhere.
    """

    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

    # CORS
    FRONTEND_ORIGIN: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

    # Neo4j
    NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "password")

    # App metadata
    APP_TITLE: str = "Industrial Safety Brain"
    APP_DESCRIPTION: str = "AI-powered Industrial Safety Intelligence API"
    APP_VERSION: str = "1.0.0"

    def validate(self) -> None:
        """Raise immediately if required secrets are missing."""
        if not self.GEMINI_API_KEY or self.GEMINI_API_KEY == "YOUR_API_KEY":
            raise ValueError(
                "GEMINI_API_KEY is not set or still has the placeholder value. "
                "Open backend/.env and paste your real API key."
            )


settings = Settings()
