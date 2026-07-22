# pyrefly: ignore [missing-import]
from fastapi import APIRouter, HTTPException
from app.models.chat_models import ChatRequest, ChatResponse, ErrorResponse
from app.services.llm_summary_service import llm_summary_service
from app.exceptions import RateLimitError

router = APIRouter(tags=["Chat"])


@router.post(
    "/chat",
    response_model=ChatResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        503: {"model": ErrorResponse, "description": "Gemini API unavailable"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def chat(request: ChatRequest) -> ChatResponse:
    """Process a chat message through LLMSummaryService and return the AI response.

    Architecture: Route → LLMSummaryService → GeminiService → Gemini API
    """
    try:
        ai_response = await llm_summary_service.chat(request.message)
        return ChatResponse(response=ai_response)

    except RateLimitError:
        # Let the global ApplicationError handler return a proper 429 JSON response
        raise

    except ValueError as e:
        # Missing or invalid API key
        raise HTTPException(status_code=503, detail=str(e))

    except Exception as e:
        error_msg = str(e).lower()

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

