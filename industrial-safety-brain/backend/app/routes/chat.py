# pyrefly: ignore [missing-import]
from fastapi import APIRouter, HTTPException
from app.models.chat_models import ChatRequest, ChatResponse, ErrorResponse
from app.services.gemini_service import gemini_service

router = APIRouter(tags=["Chat"])


@router.post(
    "/chat",
    response_model=ChatResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        503: {"model": ErrorResponse, "description": "Gemini API unavailable"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def chat(request: ChatRequest) -> ChatResponse:
    """Process a chat message through Gemini and return the AI response.

    Architecture: Route → Service → Gemini API
    """
    try:
        ai_response = await gemini_service.generate_response(request.message)
        return ChatResponse(response=ai_response)

    except ValueError as e:
        # Missing or invalid API key
        raise HTTPException(status_code=503, detail=str(e))

    except Exception as e:
        error_msg = str(e).lower()

        # Gemini-specific failures
        if "quota" in error_msg or "resource" in error_msg:
            raise HTTPException(
                status_code=429,
                detail="Gemini API rate limit exceeded. Please wait and retry.",
            )
        if "api key" in error_msg or "permission" in error_msg:
            raise HTTPException(
                status_code=503,
                detail="Gemini API key is invalid or lacks permission.",
            )

        # Catch-all
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate response: {str(e)}",
        )
