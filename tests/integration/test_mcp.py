"""Integration tests for MCP server integration (T068).

Tests MCP server connection and tool usage via the API.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.anyio
class TestMcpServerIntegration:
    """Integration tests for MCP server configuration."""

    async def test_query_with_mcp_server_config_accepted(
        self, async_client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test that MCP server configuration is accepted by the API.

        Note: This test verifies the API accepts and validates MCP server
        configuration. The actual SDK execution may fail in test environment
        without Claude CLI, but that's acceptable - we're testing the API layer.
        """
        response = await async_client.post(
            "/api/v1/query",
            json={
                "prompt": "What tools do you have?",
                "max_turns": 1,
                "mcp_servers": {
                    "test-server": {
                        "type": "stdio",
                        "command": "echo",
                        "args": ["hello"],
                    }
                },
            },
            headers={**auth_headers, "Accept": "text/event-stream"},
        )

        # The API should accept the request (200 for streaming response)
        # The SDK may fail internally but that's separate from API validation
        assert response.status_code == 200

    async def test_query_with_sse_mcp_server_config(
        self, async_client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test that SSE transport MCP servers are accepted."""
        response = await async_client.post(
            "/api/v1/query",
            json={
                "prompt": "Hello",
                "max_turns": 1,
                "mcp_servers": {
                    "remote-server": {
                        "type": "sse",
                        "url": "https://example.com/sse",
                        "headers": {"Authorization": "Bearer test"},
                    }
                },
            },
            headers={**auth_headers, "Accept": "text/event-stream"},
        )

        # Should accept the request even if server doesn't exist
        assert response.status_code == 200

    async def test_query_with_http_mcp_server_config(
        self, async_client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test that HTTP transport MCP servers are accepted."""
        response = await async_client.post(
            "/api/v1/query",
            json={
                "prompt": "Hello",
                "max_turns": 1,
                "mcp_servers": {
                    "http-server": {
                        "type": "http",
                        "url": "https://example.com/mcp",
                        "headers": {"X-API-Key": "test"},
                    }
                },
            },
            headers={**auth_headers, "Accept": "text/event-stream"},
        )

        assert response.status_code == 200

    async def test_query_with_env_var_syntax_in_mcp_config(
        self, async_client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test that environment variable syntax is accepted in MCP config."""
        response = await async_client.post(
            "/api/v1/query",
            json={
                "prompt": "Hello",
                "max_turns": 1,
                "mcp_servers": {
                    "env-server": {
                        "type": "stdio",
                        "command": "python",
                        "args": ["server.py"],
                        "env": {
                            "API_KEY": "${API_KEY:-default_key}",
                            "DEBUG": "${DEBUG}",
                        },
                    }
                },
            },
            headers={**auth_headers, "Accept": "text/event-stream"},
        )

        assert response.status_code == 200

    async def test_invalid_mcp_server_stdio_missing_command(
        self, async_client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test that stdio transport without command returns validation error."""
        response = await async_client.post(
            "/api/v1/query",
            json={
                "prompt": "Hello",
                "mcp_servers": {
                    "bad-server": {
                        "type": "stdio",
                        # Missing required 'command' field
                    }
                },
            },
            headers=auth_headers,
        )

        assert response.status_code == 422
        # Validation error for missing command

    async def test_invalid_mcp_server_sse_missing_url(
        self, async_client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test that sse transport without url returns validation error."""
        response = await async_client.post(
            "/api/v1/query",
            json={
                "prompt": "Hello",
                "mcp_servers": {
                    "bad-server": {
                        "type": "sse",
                        # Missing required 'url' field
                    }
                },
            },
            headers=auth_headers,
        )

        assert response.status_code == 422

    async def test_multiple_mcp_servers(
        self, async_client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test configuring multiple MCP servers."""
        response = await async_client.post(
            "/api/v1/query",
            json={
                "prompt": "Hello",
                "max_turns": 1,
                "mcp_servers": {
                    "server1": {
                        "type": "stdio",
                        "command": "python",
                        "args": ["server1.py"],
                    },
                    "server2": {
                        "type": "sse",
                        "url": "https://example.com/sse",
                    },
                    "server3": {
                        "type": "http",
                        "url": "https://example.com/mcp",
                    },
                },
            },
            headers={**auth_headers, "Accept": "text/event-stream"},
        )

        assert response.status_code == 200
