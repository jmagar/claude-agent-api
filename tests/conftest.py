"""Shared pytest fixtures for all tests."""

from collections.abc import AsyncGenerator
from typing import Any

import pytest
from httpx import AsyncClient

# Will be imported once the app is created
# from apps.api.main import app


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
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client for testing.

    Once the app is created, uncomment the transport line.
    """
    # transport = ASGITransport(app=app)
    async with AsyncClient(
        # transport=transport,
        base_url="http://test",
    ) as client:
        yield client


@pytest.fixture
def sample_query_request() -> dict[str, Any]:
    """Sample query request for testing."""
    return {
        "prompt": "List files in the current directory",
        "allowed_tools": ["Glob", "Read"],
    }


@pytest.fixture
def sample_session_id() -> str:
    """Sample session ID for testing."""
    return "test-session-12345"
