"""Contract tests for server-side MCP feature.

Verifies backward compatibility and integration with existing endpoints.
"""

import pytest
from httpx import AsyncClient


class TestServerSideMcpBackwardCompatibility:
    """Contract tests ensuring server-side MCP doesn't break existing behavior."""

    @pytest.mark.anyio
    async def test_existing_query_tests_pass_unchanged(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that existing query validation still works with server-side MCP.

        Re-runs subset of existing query contract tests to verify:
        - Authentication still required
        - Prompt validation unchanged
        - max_turns validation unchanged
        - Request with explicit mcp_servers still works
        """
        # Test 1: Authentication still required
        response = await async_client.post(
            "/api/v1/query/single",
            json={"prompt": "Test prompt"},
        )
        assert response.status_code == 401
        data = response.json()
        assert data["error"]["code"] == "AUTHENTICATION_ERROR"

        # Test 2: Prompt required validation unchanged
        response = await async_client.post(
            "/api/v1/query/single",
            json={},
            headers=auth_headers,
        )
        assert response.status_code == 422

        # Test 3: Empty prompt validation unchanged
        response = await async_client.post(
            "/api/v1/query/single",
            json={"prompt": ""},
            headers=auth_headers,
        )
        assert response.status_code == 422

        # Test 4: max_turns validation unchanged
        response = await async_client.post(
            "/api/v1/query/single",
            json={"prompt": "Test", "max_turns": 0},
            headers=auth_headers,
        )
        assert response.status_code == 422

        # Test 5: Request with explicit mcp_servers still works
        response = await async_client.post(
            "/api/v1/query/single",
            json={
                "prompt": "Test",
                "mcp_servers": {
                    "test": {
                        "command": "npx",
                        "args": ["-y", "@test/server"],
                    }
                },
            },
            headers=auth_headers,
        )
        # Should accept the request (200 OK), not validation error
        assert response.status_code == 200

        # Test 6: Request with null mcp_servers still works
        response = await async_client.post(
            "/api/v1/query/single",
            json={"prompt": "Test", "mcp_servers": None},
            headers=auth_headers,
        )
        assert response.status_code == 200

        # Test 7: Request without mcp_servers field still works
        response = await async_client.post(
            "/api/v1/query/single",
            json={"prompt": "Test"},
            headers=auth_headers,
        )
        assert response.status_code == 200
