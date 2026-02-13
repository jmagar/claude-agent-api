"""Shared fixtures for Phase 2 semantic tests."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, TypedDict
from uuid import uuid4

import pytest

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from httpx import AsyncClient, Response


class SseEvent(TypedDict):
    """SSE event structure."""

    event: str
    data: dict[str, object]


@pytest.fixture
def second_api_key() -> str:
    """Second API key for cross-tenant isolation tests."""
    return f"test-api-key-{uuid4().hex[:8]}"


@pytest.fixture
def second_auth_headers(second_api_key: str) -> dict[str, str]:
    """Auth headers for second tenant."""
    return {"X-API-Key": second_api_key}


@pytest.fixture
def sse_event_collector() -> Callable[[Response], Awaitable[list[SseEvent]]]:
    """Helper to collect and validate SSE events from streaming responses."""
    async def collect_events(response: Response) -> list[SseEvent]:
        """Parse SSE stream and return list of events.

        Args:
            response: HTTP response with SSE stream

        Returns:
            List of SseEvent dicts
        """
        events: list[SseEvent] = []
        event_type = None
        async for line in response.aiter_lines():
            if line.startswith("event:"):
                event_type = line.split(":", 1)[1].strip()
            elif line.startswith("data:"):
                data = json.loads(line.split(":", 1)[1].strip())
                if event_type:
                    events.append({"event": event_type, "data": data})
                    event_type = None
        return events
    return collect_events


@pytest.fixture
def validate_sse_sequence() -> Callable[[list[SseEvent], list[str]], None]:
    """Validate SSE event sequence matches expected pattern."""
    def validate(events: list[SseEvent], expected_sequence: list[str]) -> None:
        """Assert events follow expected order.

        Args:
            events: List of SseEvent dicts
            expected_sequence: List of event names in order
        """
        actual_sequence = [e["event"] for e in events]
        assert actual_sequence == expected_sequence, (
            f"Event sequence mismatch.\n"
            f"Expected: {expected_sequence}\n"
            f"Actual: {actual_sequence}"
        )
    return validate


@pytest.fixture
async def mock_session_other_tenant(
    async_client: AsyncClient,
    second_auth_headers: dict[str, str],
) -> str:
    """Create session owned by second tenant for isolation tests."""
    from fastapi import Request

    from apps.api.adapters.session_repo import SessionRepository
    from apps.api.dependencies import get_app_state
    from apps.api.services.session import SessionService

    # Get app state from test client
    request = Request(scope={"type": "http", "app": async_client._transport.app})  # type: ignore[arg-type]
    app_state = get_app_state(request)

    assert app_state.cache is not None, "Cache must be initialized"
    assert app_state.session_maker is not None, "Session maker must be initialized"

    # Create session for second tenant
    async with app_state.session_maker() as db_session:
        repo = SessionRepository(db_session)
        service = SessionService(cache=app_state.cache, db_repo=repo)
        session = await service.create_session(
            model="sonnet",
            session_id=str(uuid4()),
            owner_api_key=second_auth_headers["X-API-Key"],
        )
        return session.id
