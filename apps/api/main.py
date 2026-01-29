"""FastAPI application entry point."""

from collections.abc import AsyncGenerator, Mapping, Sequence
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from packaging.version import parse as parse_version
from pydantic import ValidationError as PydanticValidationError

from apps.api import __version__
from apps.api.config import get_settings
from apps.api.dependencies import close_cache, close_db, init_cache, init_db
from apps.api.exceptions import APIError, RequestTimeoutError
from apps.api.middleware.auth import ApiKeyAuthMiddleware
from apps.api.middleware.correlation import CorrelationIdMiddleware
from apps.api.middleware.logging import RequestLoggingMiddleware, configure_logging
from apps.api.middleware.openai_auth import BearerAuthMiddleware
from apps.api.middleware.ratelimit import configure_rate_limiting
from apps.api.routes import (
    agents,
    checkpoints,
    health,
    interactions,
    mcp_servers,
    projects,
    query,
    session_control,
    sessions,
    skills,
    slash_commands,
    tool_presets,
    websocket,
)
from apps.api.routes.openai import chat as openai_chat
from apps.api.routes.openai import models as openai_models
from apps.api.services.openai.errors import ErrorTranslator
from apps.api.services.shutdown import get_shutdown_manager, reset_shutdown_manager

logger = structlog.get_logger(__name__)

# Minimum supported SDK version - update when new SDK features are required
MIN_SDK_VERSION = "0.1.19"


def verify_sdk_version() -> None:
    """Verify Claude Agent SDK version meets minimum requirements.

    Logs a warning if the installed SDK version is below the minimum required version.
    This check helps catch compatibility issues early during startup.

    Raises:
        RuntimeError: If SDK is not installed or version cannot be determined.
    """
    try:
        from claude_agent_sdk import __version__ as sdk_version
    except ImportError as e:
        raise RuntimeError(
            "Claude Agent SDK is not installed. "
            "Install it with: uv add claude-agent-sdk"
        ) from e

    installed = parse_version(sdk_version)
    minimum = parse_version(MIN_SDK_VERSION)

    if installed < minimum:
        logger.warning(
            "sdk_version_below_minimum",
            installed_version=sdk_version,
            minimum_version=MIN_SDK_VERSION,
            hint=f"Upgrade with: uv add claude-agent-sdk>={MIN_SDK_VERSION}",
        )
    else:
        logger.debug(
            "sdk_version_verified",
            installed_version=sdk_version,
            minimum_version=MIN_SDK_VERSION,
        )


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager.

    Initializes and cleans up resources with graceful shutdown (T131).
    """
    settings = get_settings()

    # Configure logging
    configure_logging(
        log_level=settings.log_level,
        log_json=settings.log_json,
    )

    # Verify SDK version compatibility
    verify_sdk_version()

    # Reset shutdown manager for fresh state
    reset_shutdown_manager()

    # Initialize database
    await init_db(settings)

    # Initialize cache
    await init_cache(settings)

    logger.info("Application started", version=__version__)

    yield

    # Graceful shutdown (T131)
    logger.info("Initiating graceful shutdown")
    shutdown_manager = get_shutdown_manager()
    shutdown_manager.initiate_shutdown()

    # Wait for active sessions to complete (max 30 seconds)
    await shutdown_manager.wait_for_sessions(timeout=30)

    # Cleanup resources
    await close_cache()
    await close_db()

    logger.info("Application shutdown complete")


def create_app() -> FastAPI:
    """Create and configure FastAPI application.

    Returns:
        Configured FastAPI application.
    """
    settings = get_settings()

    app = FastAPI(
        title="Claude Agent API",
        description="HTTP API wrapper for the Claude Agent Python SDK",
        version=__version__,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        lifespan=lifespan,
    )

    # Add middleware (order matters - first added is last executed)
    # Reverse order so auth runs first, then correlation, then logging, then CORS
    # Note: type: ignore comments are needed due to Starlette's middleware typing
    # using ParamSpec which ty cannot fully resolve for BaseHTTPMiddleware subclasses
    app.add_middleware(ApiKeyAuthMiddleware)  # type: ignore[invalid-argument-type]
    app.add_middleware(BearerAuthMiddleware)  # type: ignore[invalid-argument-type]
    app.add_middleware(CorrelationIdMiddleware)  # type: ignore[invalid-argument-type]
    app.add_middleware(
        RequestLoggingMiddleware,  # type: ignore[invalid-argument-type]
        skip_paths=["/health", "/"],
    )
    app.add_middleware(
        CORSMiddleware,  # type: ignore[invalid-argument-type]
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["Content-Type", "X-API-Key", "X-Correlation-ID"],
    )

    # Configure rate limiting (T124)
    configure_rate_limiting(app)

    # Register exception handlers
    @app.exception_handler(APIError)
    async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
        """Handle API errors.

        For OpenAI-compatible endpoints (/v1/*), translates errors to OpenAI format.
        For native endpoints (/api/v1/*), uses standard API error format.
        """
        # Check if this is an OpenAI endpoint
        if request.url.path.startswith("/v1/"):
            # Translate to OpenAI error format
            openai_error = ErrorTranslator.translate(exc)
            return JSONResponse(
                status_code=exc.status_code,
                content=openai_error,
            )

        # Use standard API error format for native endpoints
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.to_dict(),
        )

    def _serialize_validation_errors(
        errors: Sequence[Mapping[str, object]],
    ) -> list[dict[str, object]]:
        """Convert Pydantic errors to JSON-serializable format.

        Args:
            errors: List of error dicts from Pydantic validation.

        Returns:
            List of sanitized error dicts safe for JSON serialization.
        """
        serialized: list[dict[str, object]] = []
        for error in errors:
            loc = error.get("loc")
            # Build serialized_error with explicit type annotation
            serialized_error: dict[str, object] = {
                "loc": list(loc) if isinstance(loc, (list, tuple)) else [],
                "msg": str(error.get("msg", "")),
                "type": str(error.get("type", "")),
            }
            # Convert ctx to strings if present (ValueError objects are not JSON serializable)
            ctx = error.get("ctx")
            if isinstance(ctx, dict):
                ctx_dict: dict[str, str] = {str(k): str(v) for k, v in ctx.items()}
                serialized_error["ctx"] = ctx_dict
            serialized.append(serialized_error)
        return serialized

    @app.exception_handler(RequestValidationError)
    async def request_validation_error_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        """Handle FastAPI request validation errors (Pydantic validation before route handler).

        For OpenAI endpoints (/v1/*), converts to OpenAI error format with 400 status.
        For native endpoints, uses FastAPI's default 422 format.
        """
        # Check if this is an OpenAI endpoint
        if request.url.path.startswith("/v1/"):
            # Extract first error message for simplicity
            errors = exc.errors()
            first_error = errors[0] if errors else {}
            error_msg = first_error.get("msg", "Validation failed")
            field = ".".join(str(loc) for loc in first_error.get("loc", []))

            # Create APIError with 400 status for OpenAI translation
            api_error = APIError(
                message=error_msg,
                code="VALIDATION_ERROR",
                status_code=400,
                details={"field": field} if field else {},
            )

            # Translate to OpenAI error format
            openai_error = ErrorTranslator.translate(api_error)
            return JSONResponse(
                status_code=400,
                content=openai_error,
            )

        # For native endpoints, use FastAPI default format (422)
        return JSONResponse(
            status_code=422,
            content={"detail": _serialize_validation_errors(exc.errors())},
        )

    @app.exception_handler(PydanticValidationError)
    async def pydantic_validation_error_handler(
        request: Request,
        exc: PydanticValidationError,
    ) -> JSONResponse:
        """Handle Pydantic validation errors (raised in route handlers).

        For OpenAI endpoints (/v1/*), converts to OpenAI error format with 400 status.
        For native endpoints, uses FastAPI's default 422 format.
        """
        # Check if this is an OpenAI endpoint
        if request.url.path.startswith("/v1/"):
            # Extract first error message for simplicity
            errors = exc.errors()
            if errors:
                first_error = errors[0]
                error_msg = str(first_error.get("msg", "Validation failed"))
                field = ".".join(str(loc) for loc in first_error.get("loc", []))
            else:
                error_msg = "Validation failed"
                field = ""

            # Create APIError with 400 status for OpenAI translation
            api_error = APIError(
                message=error_msg,
                code="VALIDATION_ERROR",
                status_code=400,
                details={"field": field} if field else {},
            )

            # Translate to OpenAI error format
            openai_error = ErrorTranslator.translate(api_error)
            return JSONResponse(
                status_code=400,
                content=openai_error,
            )

        # For native endpoints, use FastAPI default format (422)
        return JSONResponse(
            status_code=422,
            content={"detail": _serialize_validation_errors(exc.errors())},
        )

    @app.exception_handler(TimeoutError)
    async def timeout_exception_handler(
        _request: Request,
        exc: TimeoutError,
    ) -> JSONResponse:
        """Handle timeout exceptions (T125)."""
        # Use exception message if available, otherwise default
        message = str(exc) if str(exc) else "Request timed out"
        timeout_error = RequestTimeoutError(
            message=message,
            timeout_seconds=settings.request_timeout,
            operation="request",
        )
        # Log for debugging
        logger.warning(
            "Request timeout",
            timeout_seconds=settings.request_timeout,
            error=str(exc),
        )
        return JSONResponse(
            status_code=timeout_error.status_code,
            content=timeout_error.to_dict(),
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(
        _request: Request,
        exc: Exception,
    ) -> JSONResponse:
        """Handle unexpected exceptions."""
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred",
                    "details": {"type": type(exc).__name__} if settings.debug else {},
                }
            },
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request,
        exc: HTTPException,
    ) -> JSONResponse:
        """Handle HTTPException (used by models endpoint).

        For OpenAI endpoints (/v1/*), converts to OpenAI error format.
        For native endpoints, uses FastAPI's default format.
        """

        def _map_http_exception_code(status_code: int) -> str:
            """Map HTTPException status codes to API error codes."""
            status_map = {
                400: "VALIDATION_ERROR",
                401: "AUTHENTICATION_ERROR",
                403: "FORBIDDEN",
                404: "NOT_FOUND",
                409: "CONFLICT",
                422: "VALIDATION_ERROR",
                429: "RATE_LIMIT_EXCEEDED",
                500: "INTERNAL_ERROR",
                503: "SERVICE_UNAVAILABLE",
            }
            return status_map.get(status_code, "HTTP_ERROR")

        # Check if this is an OpenAI endpoint
        if request.url.path.startswith("/v1/"):
            # Convert HTTPException to APIError for translation
            api_error = APIError(
                message=str(exc.detail),
                code=_map_http_exception_code(exc.status_code),
                status_code=exc.status_code,
            )

            # Translate to OpenAI error format
            openai_error = ErrorTranslator.translate(api_error)
            return JSONResponse(
                status_code=exc.status_code,
                content=openai_error,
            )

        # Use FastAPI default format for native endpoints
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )

    # Include routers
    app.include_router(health.router, prefix="/api/v1")
    app.include_router(projects.router, prefix="/api/v1")
    app.include_router(agents.router, prefix="/api/v1")
    app.include_router(query.router, prefix="/api/v1")
    app.include_router(sessions.router, prefix="/api/v1")
    app.include_router(session_control.router, prefix="/api/v1")
    app.include_router(checkpoints.router, prefix="/api/v1")
    app.include_router(interactions.router, prefix="/api/v1")
    app.include_router(skills.router, prefix="/api/v1")
    app.include_router(slash_commands.router, prefix="/api/v1")
    app.include_router(websocket.router, prefix="/api/v1")
    app.include_router(mcp_servers.router, prefix="/api/v1")
    app.include_router(tool_presets.router, prefix="/api/v1")

    # OpenAI-compatible endpoints
    app.include_router(openai_chat.router, prefix="/v1")
    app.include_router(openai_models.router, prefix="/v1")

    # Also mount health at root for convenience
    app.include_router(health.router)

    return app


# Create app instance
app = create_app()
