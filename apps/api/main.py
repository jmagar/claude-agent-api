"""FastAPI application entry point."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from apps.api import __version__
from apps.api.config import get_settings
from apps.api.dependencies import close_cache, close_db, init_cache, init_db
from apps.api.exceptions import APIError
from apps.api.middleware.auth import ApiKeyAuthMiddleware
from apps.api.middleware.correlation import CorrelationIdMiddleware
from apps.api.middleware.logging import RequestLoggingMiddleware, configure_logging
from apps.api.routes import health, query, sessions


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager.

    Initializes and cleans up resources.
    """
    settings = get_settings()

    # Configure logging
    configure_logging(
        log_level=settings.log_level,
        log_json=settings.log_json,
    )

    # Initialize database
    await init_db(settings)

    # Initialize cache
    await init_cache(settings)

    yield

    # Cleanup
    await close_cache()
    await close_db()


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
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestLoggingMiddleware, skip_paths=["/health", "/"])
    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(ApiKeyAuthMiddleware)

    # Register exception handlers
    @app.exception_handler(APIError)
    async def api_error_handler(_request: Request, exc: APIError) -> JSONResponse:
        """Handle API errors."""
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.to_dict(),
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

    # Also mount health at root for convenience
    app.include_router(health.router)

    return app


# Create app instance
app = create_app()
