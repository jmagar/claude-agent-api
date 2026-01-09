"""FastAPI application entry point."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from apps.api import __version__
from apps.api.config import get_settings
from apps.api.dependencies import close_cache, close_db, init_cache, init_db
from apps.api.exceptions import APIError, RequestTimeoutError
from apps.api.middleware.auth import ApiKeyAuthMiddleware
from apps.api.middleware.correlation import CorrelationIdMiddleware
from apps.api.middleware.logging import RequestLoggingMiddleware, configure_logging
from apps.api.middleware.ratelimit import configure_rate_limiting
from apps.api.routes import (
    checkpoints,
    health,
    interactions,
    query,
    session_control,
    sessions,
    skills,
    websocket,
)
from apps.api.services.shutdown import get_shutdown_manager, reset_shutdown_manager

logger = structlog.get_logger(__name__)


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
    app.add_middleware(ApiKeyAuthMiddleware)
    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(RequestLoggingMiddleware, skip_paths=["/health", "/"])
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Configure rate limiting (T124)
    configure_rate_limiting(app)

    # Register exception handlers
    @app.exception_handler(APIError)
    async def api_error_handler(_request: Request, exc: APIError) -> JSONResponse:
        """Handle API errors."""
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.to_dict(),
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

    # Include routers
    app.include_router(health.router, prefix="/api/v1")
    app.include_router(query.router, prefix="/api/v1")
    app.include_router(sessions.router, prefix="/api/v1")
    app.include_router(session_control.router, prefix="/api/v1")
    app.include_router(checkpoints.router, prefix="/api/v1")
    app.include_router(interactions.router, prefix="/api/v1")
    app.include_router(skills.router, prefix="/api/v1")
    app.include_router(websocket.router, prefix="/api/v1")

    # Also mount health at root for convenience
    app.include_router(health.router)

    return app


# Create app instance
app = create_app()
