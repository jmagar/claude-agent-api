"""Contract tests for query endpoints against OpenAPI spec."""

import pytest
from httpx import AsyncClient


class TestQueryContractPOST:
    """Contract tests for POST /api/v1/query endpoint."""

    @pytest.mark.anyio
    async def test_query_requires_authentication(
        self,
        async_client: AsyncClient,
    ) -> None:
        """Test that query endpoint requires API key."""
        response = await async_client.post(
            "/api/v1/query",
            json={"prompt": "Test prompt"},
        )
        assert response.status_code == 401
        data = response.json()
        assert data["error"]["code"] == "AUTHENTICATION_ERROR"

    @pytest.mark.anyio
    async def test_query_validates_prompt_required(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that prompt field is required."""
        response = await async_client.post(
            "/api/v1/query",
            json={},
            headers=auth_headers,
        )
        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_query_validates_prompt_not_empty(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that prompt cannot be empty."""
        response = await async_client.post(
            "/api/v1/query",
            json={"prompt": ""},
            headers=auth_headers,
        )
        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_query_validates_max_turns(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test max_turns validation."""
        response = await async_client.post(
            "/api/v1/query",
            json={"prompt": "Test", "max_turns": 0},
            headers=auth_headers,
        )
        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_query_returns_sse_content_type(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that query endpoint returns SSE content type."""
        # This test will need the actual endpoint implemented
        # For now, skip if endpoint not implemented
        pytest.skip("Endpoint not yet implemented")


class TestQuerySingleContractPOST:
    """Contract tests for POST /api/v1/query/single endpoint."""

    @pytest.mark.anyio
    async def test_query_single_requires_authentication(
        self,
        async_client: AsyncClient,
    ) -> None:
        """Test that single query endpoint requires API key."""
        response = await async_client.post(
            "/api/v1/query/single",
            json={"prompt": "Test prompt"},
        )
        assert response.status_code == 401

    @pytest.mark.anyio
    async def test_query_single_validates_prompt(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that prompt field is required."""
        response = await async_client.post(
            "/api/v1/query/single",
            json={},
            headers=auth_headers,
        )
        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_query_single_returns_json(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that single query returns JSON response."""
        # This test will need the actual endpoint implemented
        pytest.skip("Endpoint not yet implemented")
