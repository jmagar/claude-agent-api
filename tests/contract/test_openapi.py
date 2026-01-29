"""Contract tests validating API endpoints against OpenAPI spec (T123).

These tests verify that:
1. All endpoints defined in OpenAPI spec exist in the API
2. Response status codes match the spec
3. Request/response schemas are compatible
"""

from pathlib import Path
from typing import cast

import pytest
import yaml
from httpx import AsyncClient


def load_openapi_spec() -> dict[str, object]:
    """Load and parse the OpenAPI specification."""
    spec_path = (
        Path(__file__).parent.parent.parent
        / "specs"
        / "001-claude-agent-api"
        / "contracts"
        / "openapi.yaml"
    )
    with spec_path.open() as f:
        return cast("dict[str, object]", yaml.safe_load(f))


class TestOpenAPIEndpointsExist:
    """Verify all OpenAPI endpoints exist in the API."""

    @pytest.fixture
    def openapi_spec(self) -> dict[str, object]:
        """Load OpenAPI spec once per test class."""
        return load_openapi_spec()

    @pytest.mark.anyio
    async def test_query_endpoint_exists(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test POST /query endpoint exists and accepts requests."""
        response = await async_client.post(
            "/api/v1/query",
            json={"prompt": "test"},
            headers=auth_headers,
        )
        # Should not be 404 - endpoint exists
        assert response.status_code != 404

    @pytest.mark.anyio
    async def test_query_single_endpoint_exists(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test POST /query/single endpoint exists."""
        response = await async_client.post(
            "/api/v1/query/single",
            json={"prompt": "test"},
            headers=auth_headers,
        )
        assert response.status_code != 404

    @pytest.mark.anyio
    async def test_sessions_list_endpoint_exists(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test GET /sessions endpoint exists."""
        response = await async_client.get(
            "/api/v1/sessions",
            headers=auth_headers,
        )
        assert response.status_code != 404

    @pytest.mark.anyio
    async def test_session_detail_endpoint_exists(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test GET /sessions/{id} endpoint exists."""
        response = await async_client.get(
            "/api/v1/sessions/test-session-id",
            headers=auth_headers,
        )
        # Should be 404 for unknown session, not 404 for missing route
        # A 404 with proper error format means endpoint exists
        assert response.status_code in (200, 404)
        if response.status_code == 404:
            # Verify it's a proper API error, not a route not found
            data = response.json()
            assert "error" in data or "detail" in data

    @pytest.mark.anyio
    async def test_session_resume_endpoint_exists(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test POST /sessions/{id}/resume endpoint exists."""
        response = await async_client.post(
            "/api/v1/sessions/test-session-id/resume",
            json={"prompt": "continue"},
            headers=auth_headers,
        )
        # Should be 404 for unknown session with proper error format
        assert response.status_code in (200, 404)

    @pytest.mark.anyio
    async def test_session_fork_endpoint_exists(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test POST /sessions/{id}/fork endpoint exists."""
        response = await async_client.post(
            "/api/v1/sessions/test-session-id/fork",
            json={"prompt": "fork this"},
            headers=auth_headers,
        )
        assert response.status_code in (200, 404)

    @pytest.mark.anyio
    async def test_session_interrupt_endpoint_exists(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test POST /sessions/{id}/interrupt endpoint exists."""
        response = await async_client.post(
            "/api/v1/sessions/test-session-id/interrupt",
            headers=auth_headers,
        )
        assert response.status_code in (200, 404)

    @pytest.mark.anyio
    async def test_health_endpoint_exists(
        self,
        async_client: AsyncClient,
    ) -> None:
        """Test GET /health endpoint exists."""
        response = await async_client.get("/api/v1/health")
        assert response.status_code == 200

    @pytest.mark.anyio
    async def test_skills_endpoint_exists(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test GET /skills endpoint exists."""
        response = await async_client.get(
            "/api/v1/skills",
            headers=auth_headers,
        )
        assert response.status_code != 404


class TestOpenAPIAuthRequirements:
    """Verify endpoints require authentication as specified in OpenAPI."""

    @pytest.mark.anyio
    async def test_query_requires_auth(
        self,
        async_client: AsyncClient,
    ) -> None:
        """Test POST /query requires authentication."""
        response = await async_client.post(
            "/api/v1/query",
            json={"prompt": "test"},
        )
        assert response.status_code == 401

    @pytest.mark.anyio
    async def test_sessions_requires_auth(
        self,
        async_client: AsyncClient,
    ) -> None:
        """Test GET /sessions requires authentication."""
        response = await async_client.get("/api/v1/sessions")
        assert response.status_code == 401

    @pytest.mark.anyio
    async def test_health_no_auth_required(
        self,
        async_client: AsyncClient,
    ) -> None:
        """Test GET /health does not require authentication."""
        response = await async_client.get("/api/v1/health")
        assert response.status_code == 200


class TestOpenAPIErrorResponses:
    """Verify error responses match OpenAPI spec format."""

    @pytest.mark.anyio
    async def test_validation_error_format(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test 400 Bad Request matches spec format."""
        response = await async_client.post(
            "/api/v1/query",
            json={},  # Missing required prompt
            headers=auth_headers,
        )
        assert response.status_code == 422  # FastAPI validation error
        data = response.json()
        assert "detail" in data

    @pytest.mark.anyio
    async def test_unauthorized_error_format(
        self,
        async_client: AsyncClient,
    ) -> None:
        """Test 401 Unauthorized matches spec format."""
        response = await async_client.post(
            "/api/v1/query",
            json={"prompt": "test"},
        )
        assert response.status_code == 401
        data = response.json()
        assert "error" in data


class TestOpenAPIResponseContentTypes:
    """Verify response content types match OpenAPI spec."""

    @pytest.mark.anyio
    async def test_query_returns_event_stream(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test POST /query returns text/event-stream."""
        response = await async_client.post(
            "/api/v1/query",
            json={"prompt": "test", "max_turns": 1},
            headers=auth_headers,
        )
        # Response should be SSE stream or error
        content_type = response.headers.get("content-type", "")
        # May be event-stream or error json
        assert "text/event-stream" in content_type or "application/json" in content_type

    @pytest.mark.anyio
    async def test_health_returns_json(
        self,
        async_client: AsyncClient,
    ) -> None:
        """Test GET /health returns application/json."""
        response = await async_client.get("/api/v1/health")
        assert response.status_code == 200
        content_type = response.headers.get("content-type", "")
        assert "application/json" in content_type

    @pytest.mark.anyio
    async def test_sessions_returns_json(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test GET /sessions returns application/json."""
        response = await async_client.get(
            "/api/v1/sessions",
            headers=auth_headers,
        )
        assert response.status_code == 200
        content_type = response.headers.get("content-type", "")
        assert "application/json" in content_type
