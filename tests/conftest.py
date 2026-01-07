"""Shared pytest fixtures for all tests."""

import os
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

# Set test environment variables before importing app
os.environ.setdefault("API_KEY", "test-api-key-12345")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-anthropic-key")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:53432/test")
os.environ.setdefault("REDIS_URL", "redis://localhost:53379/0")
os.environ.setdefault("DEBUG", "true")

from apps.api.main import app


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


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client for testing with ASGI transport."""
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        yield client


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
