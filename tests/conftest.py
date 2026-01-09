"""Shared pytest fixtures for all tests."""

import logging
import os
from collections.abc import AsyncGenerator, Generator
from unittest.mock import MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

# Set test environment variables before importing app
os.environ.setdefault("API_KEY", "test-api-key-12345")
# Note: Use localhost for default test env, override via DATABASE_URL/REDIS_URL for specific environments
os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://test:test@localhost:53432/test"
)
os.environ.setdefault("REDIS_URL", "redis://localhost:53380/0")
os.environ.setdefault("DEBUG", "true")

from apps.api.config import get_settings
from apps.api.dependencies import close_cache, close_db, init_cache, init_db
from apps.api.main import create_app

logger = logging.getLogger(__name__)
ALLOW_REAL_CLAUDE_ENV = "ALLOW_REAL_CLAUDE_API"


def _is_truthy(value: str | None) -> bool:
    """Return True when an env var is set to a truthy value."""
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}


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
    dependencies._agent_service = None  # Clear agent service singleton

    settings = get_settings()

    # Initialize resources
    await init_db(settings)
    await init_cache(settings)

    # Create fresh app instance for this test to avoid event loop issues
    # with BaseHTTPMiddleware when reusing app across different event loops
    test_app = create_app()

    try:
        transport = ASGITransport(app=test_app)
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


@pytest.fixture(autouse=True)
def enforce_claude_sdk_policy(request: pytest.FixtureRequest) -> Generator[None, None, None]:
    """Mock Claude SDK for non-e2e tests and guard against real calls."""
    is_e2e = request.node.get_closest_marker("e2e") is not None
    allow_real = _is_truthy(os.environ.get(ALLOW_REAL_CLAUDE_ENV))

    if is_e2e:
        if not allow_real:
            pytest.skip(
                f"Set {ALLOW_REAL_CLAUDE_ENV}=true to run e2e tests that call Claude."
            )
        yield
        return

    request.getfixturevalue("mock_claude_sdk")
    yield

    import claude_agent_sdk

    if not isinstance(claude_agent_sdk.ClaudeSDKClient, MagicMock):
        pytest.fail(
            "Real Claude SDK client detected outside e2e. "
            f"Mark the test with @pytest.mark.e2e and set {ALLOW_REAL_CLAUDE_ENV}=true."
        )

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
    session = await service.create_session(
        model="sonnet", session_id="mock-existing-session-001"
    )
    return session.id


@pytest.fixture
async def mock_active_session_id(_async_client: AsyncClient) -> str:
    """Create a mock active session that can be interrupted.

    Creates a session and registers it with the agent service as active.
    """
    import asyncio

    from apps.api.dependencies import (
        get_cache,
        set_agent_service_singleton,
    )
    from apps.api.services.agent import AgentService
    from apps.api.services.session import SessionService

    # Create session in session service
    cache = await get_cache()
    service = SessionService(cache=cache)
    session = await service.create_session(
        model="sonnet", session_id="mock-active-session-001"
    )

    # Create agent service singleton and register session as active
    agent_service = AgentService()
    agent_service._active_sessions[session.id] = asyncio.Event()
    set_agent_service_singleton(agent_service)

    return session.id


@pytest.fixture
async def mock_session_with_checkpoints(
    _async_client: AsyncClient,
) -> str:
    """Create a mock session with checkpoints for testing.

    Creates a session and adds sample checkpoints to it.
    """
    from datetime import UTC, datetime
    from uuid import uuid4

    from apps.api.dependencies import get_cache
    from apps.api.services.session import SessionService

    cache = await get_cache()
    service = SessionService(cache=cache)

    # Create session
    session_id = f"mock-session-with-checkpoints-{uuid4().hex[:8]}"
    await service.create_session(model="sonnet", session_id=session_id)

    # Add checkpoints directly to cache
    checkpoint_id = f"checkpoint-{uuid4().hex[:8]}"
    checkpoint_data: dict[str, object] = {
        "id": checkpoint_id,
        "session_id": session_id,
        "user_message_uuid": f"msg-{uuid4().hex[:8]}",
        "created_at": datetime.now(UTC).isoformat(),
        "files_modified": ["/path/to/file1.py", "/path/to/file2.py"],
    }

    # Store individual checkpoint in cache (for validation lookup)
    individual_key = f"checkpoint:{checkpoint_id}"
    await cache.set_json(individual_key, checkpoint_data, 3600)

    # Store checkpoint in cache using checkpoints list key (for listing)
    checkpoints_key = f"checkpoints:{session_id}"
    await cache.set_json(checkpoints_key, {"checkpoints": [checkpoint_data]}, 3600)

    return session_id


@pytest.fixture
async def mock_checkpoint_id(
    mock_session_with_checkpoints: str,
    _async_client: AsyncClient,
) -> str:
    """Get the checkpoint ID from the mock session with checkpoints."""
    from apps.api.dependencies import get_cache

    cache = await get_cache()
    checkpoints_key = f"checkpoints:{mock_session_with_checkpoints}"
    data = await cache.get_json(checkpoints_key)

    if data and "checkpoints" in data:
        checkpoints = data["checkpoints"]
        if isinstance(checkpoints, list) and len(checkpoints) > 0:
            checkpoint = checkpoints[0]
            if isinstance(checkpoint, dict) and "id" in checkpoint:
                return str(checkpoint["id"])

    raise ValueError("No checkpoint found in mock session")


@pytest.fixture
async def mock_checkpoint_from_other_session(
    _async_client: AsyncClient,
) -> str:
    """Create a checkpoint that belongs to a different session.

    Used to test that rewind rejects checkpoints from other sessions.
    """
    from datetime import UTC, datetime
    from uuid import uuid4

    from apps.api.dependencies import get_cache
    from apps.api.services.session import SessionService

    cache = await get_cache()
    service = SessionService(cache=cache)

    # Create another session
    other_session_id = f"other-session-{uuid4().hex[:8]}"
    await service.create_session(model="sonnet", session_id=other_session_id)

    # Add checkpoint to that other session
    checkpoint_id = f"other-checkpoint-{uuid4().hex[:8]}"
    checkpoint_data: dict[str, object] = {
        "id": checkpoint_id,
        "session_id": other_session_id,
        "user_message_uuid": f"msg-{uuid4().hex[:8]}",
        "created_at": datetime.now(UTC).isoformat(),
        "files_modified": ["/path/to/other/file.py"],
    }

    # Store individual checkpoint in cache (for validation lookup)
    individual_key = f"checkpoint:{checkpoint_id}"
    await cache.set_json(individual_key, checkpoint_data, 3600)

    # Store checkpoint in cache using checkpoints list key (for listing)
    checkpoints_key = f"checkpoints:{other_session_id}"
    await cache.set_json(checkpoints_key, {"checkpoints": [checkpoint_data]}, 3600)

    return checkpoint_id


# Import mock fixtures
from tests.mocks.claude_sdk import mock_claude_sdk  # noqa: F401, E402
