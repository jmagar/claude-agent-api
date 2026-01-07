"""Shared pytest fixtures for all tests."""

import logging
import os
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

# Set test environment variables before importing app
os.environ.setdefault("API_KEY", "test-api-key-12345")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@100.120.242.29:53432/test")
os.environ.setdefault("REDIS_URL", "redis://100.120.242.29:53380/0")
os.environ.setdefault("DEBUG", "true")

from apps.api.config import get_settings
from apps.api.dependencies import close_cache, close_db, init_cache, init_db
from apps.api.main import app

logger = logging.getLogger(__name__)


@pytest.fixture
def anyio_backend() -> str:
    """Use asyncio as the async backend."""
    return "asyncio"


@pytest.fixture
def test_api_key() -> str:
    """API key for testing."""
    return "test-api-key-12345"


@pytest.fixture
def auth_headers(test_api_key: str) -> dict[str, str]:
    """Headers with API key authentication."""
    return {"X-API-Key": test_api_key}


@pytest.fixture
def _auth_headers(auth_headers: dict[str, str]) -> dict[str, str]:
    """Underscore-prefixed alias for skipped tests."""
    return auth_headers


@pytest.fixture(scope="function")
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client for testing with ASGI transport.

    Initializes the app lifecycle (db, cache) before tests.
    Uses function scope to avoid Redis connection issues across tests.
    """
    # Clear the settings cache to ensure test env vars are used
    get_settings.cache_clear()

    # Clear the global cache instance to force re-initialization
    from apps.api import dependencies
    dependencies._redis_cache = None
    dependencies._async_engine = None
    dependencies._async_session_maker = None

    # Also clear service singletons
    from apps.api.routes import query, sessions
    sessions._session_service = None
    sessions._agent_service = None
    query._agent_service = None

    settings = get_settings()

    # Initialize resources
    await init_db(settings)
    await init_cache(settings)

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            yield client
    finally:
        # Cleanup resources - cache first to avoid event loop issues
        try:
            await close_cache()
        except RuntimeError as e:
            logger.debug("Cache cleanup skipped: %s", str(e))
        try:
            await close_db()
        except RuntimeError as e:
            logger.debug("Database cleanup skipped: %s", str(e))


@pytest.fixture
async def _async_client(async_client: AsyncClient) -> AsyncClient:
    """Underscore-prefixed alias for skipped tests."""
    return async_client


@pytest.fixture
def sample_query_request() -> dict[str, str | list[str]]:
    """Sample query request for testing."""
    return {
        "prompt": "List files in the current directory",
        "allowed_tools": ["Glob", "Read"],
    }


@pytest.fixture
def sample_session_id() -> str:
    """Sample session ID for testing."""
    return "test-session-12345"


@pytest.fixture
async def mock_session_id(_async_client: AsyncClient) -> str:
    """Create a mock session that exists in the system.

    Creates a real session by making a query, then returns its ID.
    """
    from apps.api.dependencies import get_cache
    from apps.api.services.session import SessionService

    cache = await get_cache()
    service = SessionService(cache=cache)
    session = await service.create_session(model="sonnet", session_id="mock-existing-session-001")
    return session.id


@pytest.fixture
async def mock_active_session_id(_async_client: AsyncClient) -> str:
    """Create a mock active session that can be interrupted.

    Creates a session and registers it with the agent service as active.
    """
    from apps.api.dependencies import get_cache
    from apps.api.routes.sessions import get_agent_service
    from apps.api.services.session import SessionService

    # Create session in session service
    cache = await get_cache()
    service = SessionService(cache=cache)
    session = await service.create_session(model="sonnet", session_id="mock-active-session-001")

    # Register with agent service as active
    import asyncio

    agent_service = get_agent_service()
    agent_service._active_sessions[session.id] = asyncio.Event()

    return session.id
