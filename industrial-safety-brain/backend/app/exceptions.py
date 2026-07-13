"""
exceptions.py -- Centralized exception hierarchy for Industrial Safety Brain.

Every custom exception maps to a specific HTTP status code.
The global exception handler in main.py catches these and returns
structured JSON responses. Business logic never needs to construct
HTTPException directly -- raise the appropriate typed exception instead.

Usage:
    from app.exceptions import NotFoundError, ExternalServiceError
    raise NotFoundError("Zone X not found")
    raise ExternalServiceError("Gemini API timed out", service="gemini")
"""


class ApplicationError(Exception):
    """Base class for all application exceptions.

    Attributes:
        message:     Human-readable error description (safe to expose).
        status_code: HTTP status code to return.
        error_type:  Machine-readable error type string.
        details:     Optional additional context (safe to expose).
    """

    status_code: int = 500
    error_type: str = "ApplicationError"

    def __init__(self, message: str = "An unexpected error occurred", details: str = None) -> None:
        self.message = message
        self.details = details
        super().__init__(self.message)


# ── Client Errors (4xx) ────────────────────────────────────

class ValidationError(ApplicationError):
    """Invalid request data that fails business validation."""
    status_code = 400
    error_type = "ValidationError"


class NotFoundError(ApplicationError):
    """Requested resource does not exist."""
    status_code = 404
    error_type = "NotFoundError"


class ResourceConflictError(ApplicationError):
    """Resource state conflict (e.g., duplicate report ID)."""
    status_code = 409
    error_type = "ResourceConflictError"


class RateLimitError(ApplicationError):
    """External API rate limit exceeded."""
    status_code = 429
    error_type = "RateLimitError"


class DocumentProcessingError(ApplicationError):
    """Failed to parse, chunk, or embed a document."""
    status_code = 400
    error_type = "DocumentProcessingError"


# ── Server Errors (5xx) ────────────────────────────────────

class ConfigurationError(ApplicationError):
    """Missing or invalid server configuration."""
    status_code = 500
    error_type = "ConfigurationError"


class ExternalServiceError(ApplicationError):
    """An external service (Gemini, Neo4j, ChromaDB) is unreachable or returned an error."""
    status_code = 502
    error_type = "ExternalServiceError"

    def __init__(self, message: str, service: str = "unknown", details: str = None) -> None:
        self.service = service
        super().__init__(message=message, details=details or f"Service: {service}")


class GeminiServiceError(ExternalServiceError):
    """Gemini API failure."""
    error_type = "GeminiServiceError"

    def __init__(self, message: str = "Gemini API is unavailable", details: str = None) -> None:
        super().__init__(message=message, service="gemini", details=details)


class Neo4jServiceError(ExternalServiceError):
    """Neo4j connection or query failure."""
    status_code = 503
    error_type = "Neo4jServiceError"

    def __init__(self, message: str = "Neo4j is unavailable", details: str = None) -> None:
        super().__init__(message=message, service="neo4j", details=details)


class ChromaServiceError(ExternalServiceError):
    """ChromaDB failure."""
    error_type = "ChromaServiceError"

    def __init__(self, message: str = "ChromaDB is unavailable", details: str = None) -> None:
        super().__init__(message=message, service="chromadb", details=details)


# ── Domain Errors (5xx) ────────────────────────────────────

class RiskEngineError(ApplicationError):
    """Risk Engine computation failure."""
    status_code = 500
    error_type = "RiskEngineError"


class RAGError(ApplicationError):
    """RAG pipeline failure (retrieval, embedding, or generation)."""
    status_code = 500
    error_type = "RAGError"


class KnowledgeGraphError(ApplicationError):
    """Knowledge Graph query or build failure."""
    status_code = 503
    error_type = "KnowledgeGraphError"


class ComplianceError(ApplicationError):
    """Compliance analysis failure."""
    status_code = 500
    error_type = "ComplianceError"


class AgentExecutionError(ApplicationError):
    """Agent orchestration pipeline failure."""
    status_code = 500
    error_type = "AgentExecutionError"


class EmergencyResponseError(ApplicationError):
    """Emergency response plan generation failure."""
    status_code = 500
    error_type = "EmergencyResponseError"
