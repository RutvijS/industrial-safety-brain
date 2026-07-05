# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Incoming chat message from the client."""

    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="The user's message to SafetyBrain AI.",
    )


class ChatResponse(BaseModel):
    """AI-generated response returned to the client."""

    response: str = Field(
        ...,
        description="The AI assistant's reply.",
    )


class ErrorResponse(BaseModel):
    """Standardised error payload."""

    detail: str = Field(
        ...,
        description="Human-readable error description.",
    )
