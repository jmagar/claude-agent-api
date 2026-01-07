"""Integration tests for model selection (T105)."""

import json
import re

import pytest
from httpx import AsyncClient


class TestModelSelection:
    """Integration tests for model selection parameter."""

    @pytest.mark.anyio
    async def test_query_with_default_model_uses_sonnet(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that queries without model parameter default to sonnet."""
        response = await async_client.post(
            "/api/v1/query",
            json={
                "prompt": "Hello",
                "allowed_tools": [],
            },
            headers=auth_headers,
        )
        assert response.status_code == 200

        # Parse init event to check model
        content = response.text
        init_match = re.search(r'data: (\{"session_id".*?\})', content)
        assert init_match is not None, f"No init event found in: {content[:500]}"

        init_data = json.loads(init_match.group(1))
        assert init_data["model"] == "sonnet"

    @pytest.mark.anyio
    async def test_query_with_explicit_sonnet_model(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that queries with model=sonnet use sonnet."""
        response = await async_client.post(
            "/api/v1/query",
            json={
                "prompt": "Hello",
                "model": "sonnet",
                "allowed_tools": [],
            },
            headers=auth_headers,
        )
        assert response.status_code == 200

        content = response.text
        init_match = re.search(r'data: (\{"session_id".*?\})', content)
        assert init_match is not None

        init_data = json.loads(init_match.group(1))
        assert init_data["model"] == "sonnet"

    @pytest.mark.anyio
    async def test_query_with_opus_model(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that queries with model=opus use opus."""
        response = await async_client.post(
            "/api/v1/query",
            json={
                "prompt": "Hello",
                "model": "opus",
                "allowed_tools": [],
            },
            headers=auth_headers,
        )
        assert response.status_code == 200

        content = response.text
        init_match = re.search(r'data: (\{"session_id".*?\})', content)
        assert init_match is not None

        init_data = json.loads(init_match.group(1))
        assert init_data["model"] == "opus"

    @pytest.mark.anyio
    async def test_query_with_haiku_model(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that queries with model=haiku use haiku."""
        response = await async_client.post(
            "/api/v1/query",
            json={
                "prompt": "Hello",
                "model": "haiku",
                "allowed_tools": [],
            },
            headers=auth_headers,
        )
        assert response.status_code == 200

        content = response.text
        init_match = re.search(r'data: (\{"session_id".*?\})', content)
        assert init_match is not None

        init_data = json.loads(init_match.group(1))
        assert init_data["model"] == "haiku"

    @pytest.mark.anyio
    async def test_query_with_invalid_model_returns_422(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that queries with invalid model return validation error."""
        response = await async_client.post(
            "/api/v1/query",
            json={
                "prompt": "Hello",
                "model": "invalid-model",
                "allowed_tools": [],
            },
            headers=auth_headers,
        )
        assert response.status_code == 422

        data = response.json()
        assert "detail" in data
        # Verify error mentions valid model options
        error_str = str(data["detail"])
        assert "sonnet" in error_str or "model" in error_str.lower()

    @pytest.mark.anyio
    async def test_query_with_full_model_id_accepted(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that queries with full model ID are accepted."""
        response = await async_client.post(
            "/api/v1/query",
            json={
                "prompt": "Hello",
                "model": "claude-sonnet-4-20250514",
                "allowed_tools": [],
            },
            headers=auth_headers,
        )
        assert response.status_code == 200

        content = response.text
        init_match = re.search(r'data: (\{"session_id".*?\})', content)
        assert init_match is not None

        init_data = json.loads(init_match.group(1))
        assert init_data["model"] == "claude-sonnet-4-20250514"

    @pytest.mark.anyio
    async def test_result_event_contains_model_usage(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that result event contains model_usage breakdown."""
        response = await async_client.post(
            "/api/v1/query",
            json={
                "prompt": "Hello",
                "model": "sonnet",
                "allowed_tools": [],
            },
            headers=auth_headers,
        )
        assert response.status_code == 200

        content = response.text
        # Find result event - parse line by line to find result event JSON
        # SSE format: "event: result\ndata: {...json...}"
        result_data = None
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if "event: result" in line:
                # Find the next line containing JSON data
                for next_line in lines[i + 1 :]:
                    if next_line.startswith("data: {") or ": {" in next_line:
                        # Extract JSON from the line
                        json_start = next_line.find("{")
                        if json_start >= 0:
                            result_data = json.loads(next_line[json_start:])
                            break
                break

        assert result_data is not None, f"No result event found in: {content}"
        # model_usage should be present (may be None if single model)
        assert "model_usage" in result_data

    @pytest.mark.anyio
    async def test_single_query_with_model_parameter(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that /query/single endpoint respects model parameter."""
        response = await async_client.post(
            "/api/v1/query/single",
            json={
                "prompt": "Hello",
                "model": "haiku",
                "allowed_tools": [],
            },
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.json()
        assert data["model"] == "haiku"
