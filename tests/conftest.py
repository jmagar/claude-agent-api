"""Shared pytest fixtures for all tests."""

import logging
import os
from collections.abc import AsyncGenerator, Generator
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from alembic.config import Config
from filelock import FileLock
from httpx import ASGITransport, AsyncClient

from alembic import command

# Set test environment variables before importing app
os.environ.setdefault("API_KEY", "test-api-key-12345")
# Note: Use host.docker.internal since we're in code-server container and services run on host
os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://test:test@host.docker.internal:53432/test"
)
os.environ.setdefault("REDIS_URL", "redis://host.docker.internal:53380/0")
os.environ.setdefault("DEBUG", "true")

from apps.api.config import get_settings
from apps.api.dependencies import close_cache, close_db, init_cache, init_db
from apps.api.main import create_app
from tests.helpers.e2e_client import (
    get_e2e_base_url,
    get_e2e_timeout_seconds,
    should_use_live_e2e_client,
)

logger = logging.getLogger(__name__)
ALLOW_REAL_CLAUDE_ENV = "ALLOW_REAL_CLAUDE_API"


def _is_truthy(value: str | None) -> bool:
    """Return True when an env var is set to a truthy value."""
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}


@pytest.fixture(scope="session", autouse=True)
def apply_migrations() -> None:
    """Apply alembic migrations for the test database.

    Uses FileLock for cross-platform serialization across pytest-xdist workers.
    """
    lock_path = Path(".cache/pytest-migrations.lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)

    with FileLock(lock_path):
        config = Config(str(Path("alembic.ini")))
        config.set_main_option("sqlalchemy.url", get_settings().database_url)
        command.upgrade(config, "head")


@pytest.fixture
def anyio_backend() -> str:
    """Use asyncio as the async backend."""
    return "asyncio"


@pytest.fixture
def test_api_key() -> str:
    """API key for testing.

    Uses API_KEY from environment (set by CI or conftest defaults).
    Falls back to hardcoded value if not set.
    """
    return os.environ.get("API_KEY", "test-api-key-12345")


@pytest.fixture
def auth_headers(test_api_key: str) -> dict[str, str]:
    """Headers with API key authentication."""
    return {"X-API-Key": test_api_key}


@pytest.fixture
def _auth_headers(auth_headers: dict[str, str]) -> dict[str, str]:
    """Underscore-prefixed alias for skipped tests."""
    return auth_headers


@pytest.fixture(scope="function")
async def async_client(
    request: pytest.FixtureRequest,
) -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client for testing with ASGI transport.

    Initializes the app lifecycle (db, cache) before tests.
    Uses function scope to avoid Redis connection issues across tests.
    """
    is_e2e = request.node.get_closest_marker("e2e") is not None
    if should_use_live_e2e_client(is_e2e=is_e2e, env=os.environ):
        base_url = get_e2e_base_url(os.environ)
        assert base_url is not None
        timeout_seconds = get_e2e_timeout_seconds(os.environ)
        async with AsyncClient(base_url=base_url, timeout=timeout_seconds) as client:
            yield client
        return

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
def enforce_claude_sdk_policy(
    request: pytest.FixtureRequest,
) -> Generator[None, None, None]:
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
async def mock_session_id(_async_client: AsyncClient, test_api_key: str) -> str:
    """Create a mock session that exists in the system.

    Creates a real session by making a query, then returns its ID.
    """
    from uuid import uuid4

    from apps.api.adapters.session_repo import SessionRepository
    from apps.api.dependencies import get_cache, get_db
    from apps.api.services.session import SessionService

    cache = await get_cache()
    db_gen = get_db()
    db_session = await anext(db_gen)
    try:
        repo = SessionRepository(db_session)
        service = SessionService(cache=cache, db_repo=repo)
        session = await service.create_session(
            model="sonnet",
            session_id=str(uuid4()),
            owner_api_key=test_api_key,
        )
        return session.id
    finally:
        await db_gen.aclose()


@pytest.fixture
async def mock_active_session_id(
    _async_client: AsyncClient,
) -> AsyncGenerator[str, None]:
    """Create a mock active session that can be interrupted.

    Creates a session and registers it with the agent service as active.
    Cleans up the active session registration after the test completes.
    """
    from uuid import uuid4

    from apps.api.adapters.session_repo import SessionRepository
    from apps.api.dependencies import (
        get_cache,
        get_db,
        set_agent_service_singleton,
    )
    from apps.api.services.agent import AgentService
    from apps.api.services.session import SessionService

    # Create session in session service
    cache = await get_cache()
    db_gen = get_db()
    db_session = await anext(db_gen)
    repo = SessionRepository(db_session)
    service = SessionService(cache=cache, db_repo=repo)
    session = await service.create_session(
        model="sonnet",
        session_id=str(uuid4()),
    )

    # Create agent service singleton with cache and register session as active
    agent_service = AgentService(cache=cache)
    # Register session as active in Redis (distributed)
    await agent_service._register_active_session(session.id)
    set_agent_service_singleton(agent_service)

    try:
        yield session.id
    finally:
        await db_gen.aclose()
        # Cleanup: Unregister session to prevent interference with other tests
        try:
            await agent_service._unregister_active_session(session.id)
        except Exception as e:
            logger.debug("Failed to unregister active session: %s", str(e))


@pytest.fixture
async def mock_session_with_checkpoints(
    _async_client: AsyncClient,
) -> str:
    """Create a mock session with checkpoints for testing.

    Creates a session and adds sample checkpoints to it.
    """
    from datetime import UTC, datetime
    from uuid import uuid4

    from apps.api.adapters.session_repo import SessionRepository
    from apps.api.dependencies import get_cache, get_db
    from apps.api.services.session import SessionService

    cache = await get_cache()
    db_gen = get_db()
    db_session = await anext(db_gen)
    repo = SessionRepository(db_session)
    service = SessionService(cache=cache, db_repo=repo)

    # Create session
    session_id = str(uuid4())
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

    await db_gen.aclose()
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

    from apps.api.adapters.session_repo import SessionRepository
    from apps.api.dependencies import get_cache, get_db
    from apps.api.services.session import SessionService

    cache = await get_cache()
    db_gen = get_db()
    db_session = await anext(db_gen)
    repo = SessionRepository(db_session)
    service = SessionService(cache=cache, db_repo=repo)

    # Create another session
    other_session_id = str(uuid4())
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

    await db_gen.aclose()
    return checkpoint_id


# Import mock fixtures
from tests.mocks.claude_sdk import mock_claude_sdk  # noqa: F401, E402
