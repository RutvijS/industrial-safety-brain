import logging
import uuid
from datetime import datetime, timezone

# pyrefly: ignore [missing-import]
from fastapi import FastAPI, Request
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware
# pyrefly: ignore [missing-import]
from fastapi.responses import JSONResponse

from app.config import settings
from app.exceptions import ApplicationError
from app.routes.chat import router as chat_router
from app.routes.data import router as data_router
from app.routes.plant_state import router as plant_state_router
from app.routes.risk import router as risk_router
from app.routes.rag import router as rag_router
from app.routes.geospatial import router as geospatial_router
from app.routes.knowledge_graph import router as kg_router
from app.routes.agent import router as agent_router
from app.routes.compliance import router as compliance_router

# ── Structured Logging ─────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("safety_brain")

app = FastAPI(
    title=settings.APP_TITLE,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allow ONLY the Vite dev server origin from config
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# Register routes
app.include_router(chat_router)
app.include_router(data_router)
app.include_router(plant_state_router)
app.include_router(risk_router)
app.include_router(rag_router)
app.include_router(geospatial_router)
app.include_router(kg_router)
app.include_router(agent_router)
app.include_router(compliance_router)


# ── Request ID Middleware ───────────────────────────────────

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Attach a unique request ID to every request for tracing."""
    request_id = request.headers.get("X-Request-ID", uuid.uuid4().hex[:12])
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# ── Global Exception Handlers ──────────────────────────────

def _error_response(status_code: int, error_type: str, message: str,
                    details: str = None, request_id: str = None) -> JSONResponse:
    """Build a consistent error JSON response."""
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": {
                "type": error_type,
                "message": message,
                "details": details,
                "request_id": request_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        },
    )


@app.exception_handler(ApplicationError)
async def handle_application_error(request: Request, exc: ApplicationError):
    """Handle all typed application exceptions with structured JSON."""
    request_id = getattr(request.state, "request_id", None)
    logger.warning(
        "ApplicationError | type=%s | status=%d | msg=%s | request_id=%s",
        exc.error_type, exc.status_code, exc.message, request_id,
    )
    return _error_response(
        status_code=exc.status_code,
        error_type=exc.error_type,
        message=exc.message,
        details=exc.details,
        request_id=request_id,
    )


@app.exception_handler(Exception)
async def handle_unhandled_exception(request: Request, exc: Exception):
    """Catch-all for unhandled exceptions — never expose stack traces."""
    request_id = getattr(request.state, "request_id", None)
    logger.exception(
        "Unhandled exception | request_id=%s | %s: %s",
        request_id, type(exc).__name__, exc,
    )
    return _error_response(
        status_code=500,
        error_type="InternalServerError",
        message="An unexpected error occurred. Please try again.",
        request_id=request_id,
    )


@app.get("/")
async def root() -> dict:
    """Root endpoint — confirms the API is reachable."""
    return {
        "service": settings.APP_TITLE,
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }


@app.get("/health")
async def health_check() -> dict:
    """Comprehensive health check — reports connectivity for all services."""
    checks = {}

    # Gemini
    try:
        from app.services.gemini_service import gemini_service
        checks["gemini"] = "ok" if gemini_service else "unavailable"
    except Exception:
        checks["gemini"] = "unavailable"

    # ChromaDB
    try:
        from app.rag.vector_store import vector_store
        count = vector_store.get_document_count()
        checks["chromadb"] = f"ok ({count} docs)"
    except Exception:
        checks["chromadb"] = "unavailable"

    # Neo4j
    try:
        from app.services.knowledge_graph_service import kg_service
        checks["neo4j"] = "ok" if kg_service.is_connected else "unavailable"
    except Exception:
        checks["neo4j"] = "unavailable"

    # Datasets
    try:
        from app.services.data_service import data_service
        checks["datasets"] = f"ok ({len(data_service.get_sensors())} sensors)"
    except Exception:
        checks["datasets"] = "unavailable"

    all_ok = all("ok" in v for v in checks.values())
    return {
        "status": "ok" if all_ok else "degraded",
        "services": checks,
        "version": settings.APP_VERSION,
    }

