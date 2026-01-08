"""End-to-end tests that actually call Claude API."""

import pytest
from httpx import AsyncClient


@pytest.mark.e2e
@pytest.mark.anyio
async def test_real_claude_query(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Test real Claude API call (no mocking).

    This test actually calls Claude and should be run sparingly.
    """
    response = await async_client.post(
        "/api/v1/query",
        json={"prompt": "Say hello"},
        headers=auth_headers,
    )

    assert response.status_code == 200

    # Verify we get real events from Claude
    # Events are SSE formatted: "event: <type>\ndata: <json>\n\n"
    response_text = response.text

    # Check for required event types in the response
    assert "event: init" in response_text
    assert "event: message" in response_text
    assert "event: result" in response_text
    assert "event: done" in response_text
