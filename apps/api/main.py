"""FastAPI application entry point."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Protocol, cast

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from packaging.version import parse as parse_version

from apps.api import __version__
from apps.api.config import get_settings
from apps.api.dependencies import AppState, close_cache, close_db, init_cache, init_db
from apps.api.exception_handlers import register_exception_handlers
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
    memories,
    projects,
    query,
    session_control,
    sessions,
    skills,
    slash_commands,
    tool_presets,
    websocket,
)
from apps.api.routes.openai import assistants as openai_assistants
from apps.api.routes.openai import chat as openai_chat
from apps.api.routes.openai import models as openai_models
from apps.api.routes.openai import threads as openai_threads
from apps.api.services.shutdown import get_shutdown_manager, reset_shutdown_manager

logger = structlog.get_logger(__name__)

# Minimum supported SDK version - update when new SDK features are required
MIN_SDK_VERSION = "0.1.19"


class _AddMiddlewareCallable(Protocol):
    """Protocol for FastAPI add_middleware method."""

    def __call__(
        self,
        middleware_class: type[object],
        **options: object,
    ) -> None:
        """Add middleware to the application.

        Args:
            middleware_class: Middleware class to add.
            **options: Middleware configuration options.
        """
        ...


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
    import os

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

    # Create application state (M-01, ARC-04)
    app_state = AppState()
    _app.state.app_state = app_state

    # SECURITY NOTE: Mem0's OpenAI embedder requires OPENAI_API_KEY to be set,
    # even when using HuggingFace embedder with TEI. This is a workaround for
    # Mem0's validation logic which unconditionally checks for OpenAI credentials
    # regardless of the actual embedder provider in use.
    #
    # The default value "not-needed" (from settings.tei_api_key) is a placeholder,
    # NOT a real credential. TEI endpoints don't require authentication, but Mem0's
    # OpenAI client wrapper validates this environment variable before allowing any
    # embedder to be used.
    #
    # This is set once at startup (idempotent check) and does NOT expose any real
    # credentials. It satisfies Mem0's validation without compromising security.
    #
    # RISKS:
    # - Environment variable pollution: OPENAI_API_KEY is globally visible to all
    #   code in this process, including third-party dependencies
    # - Potential conflicts: If any dependency actually uses OPENAI_API_KEY for
    #   OpenAI API calls, it will fail with authentication errors
    # - Silent failures: Errors caused by this workaround may be non-obvious
    #
    # TODO: Track upstream fix in Mem0 to remove OpenAI dependency requirement
    # when using alternative embedder providers (HuggingFace, Cohere, etc.)
    # See: https://github.com/mem0ai/mem0/issues/3439
    if not os.environ.get("OPENAI_API_KEY"):
        os.environ["OPENAI_API_KEY"] = settings.tei_api_key
        logger.debug(
            "openai_api_key_set",
            reason="mem0_huggingface_embedder_validation_workaround",
            tei_api_key="<redacted>" if settings.tei_api_key else "<unset>",
        )

    # Initialize database
    await init_db(app_state, settings)

    # Initialize cache
    await init_cache(app_state, settings)

    logger.info("Application started", version=__version__)

    yield

    # Graceful shutdown (T131)
    logger.info("Initiating graceful shutdown")
    shutdown_manager = get_shutdown_manager()
    shutdown_manager.initiate_shutdown()

    # Wait for active sessions to complete (max 30 seconds)
    await shutdown_manager.wait_for_sessions(timeout=30)

    # Cleanup resources
    await close_cache(app_state)
    await close_db(app_state)

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
    # Reverse order so auth runs first, then correlation, then logging, then CORS.
    # Cast to protocol to satisfy type checker (FastAPI's stubs use ParamSpec which is incompatible).
    add_middleware = cast("_AddMiddlewareCallable", app.add_middleware)
    add_middleware(ApiKeyAuthMiddleware)
    add_middleware(BearerAuthMiddleware)
    add_middleware(CorrelationIdMiddleware)
    add_middleware(
        RequestLoggingMiddleware,
        skip_paths=["/health", "/"],
    )
    add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["Content-Type", "X-API-Key", "X-Correlation-ID"],
    )

    # Configure rate limiting (T124)
    configure_rate_limiting(app)

    # Register exception handlers
    register_exception_handlers(app, settings)

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
    app.include_router(memories.router)  # Prefix already set in router
    app.include_router(tool_presets.router, prefix="/api/v1")

    # OpenAI-compatible endpoints
    app.include_router(openai_chat.router, prefix="/v1")
    app.include_router(openai_models.router, prefix="/v1")
    app.include_router(openai_assistants.router, prefix="/v1")
    app.include_router(openai_threads.router, prefix="/v1")

    # Also mount health at root for convenience
    app.include_router(health.router)

    return app


# Create app instance
app = create_app()
