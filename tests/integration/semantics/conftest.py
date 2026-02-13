"""Shared fixtures for Phase 2 semantic tests."""

from __future__ import annotations

from uuid import uuid4

import pytest


@pytest.fixture
def second_api_key() -> str:
    """Second API key for cross-tenant isolation tests."""
    return f"test-api-key-{uuid4().hex[:8]}"


@pytest.fixture
def second_auth_headers(second_api_key: str) -> dict[str, str]:
    """Auth headers for second tenant."""
    return {"X-API-Key": second_api_key}
