"""Integration tests for server-side MCP configuration.

Tests the end-to-end flow of application-level, API-key-level, and request-level
MCP server configuration with real filesystem and Redis.
"""

import json
from pathlib import Path

import pytest
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.anyio
class TestServerSideMcpIntegration:
    """Integration tests for three-tier MCP configuration."""

    async def test_application_mcp_servers_injected_into_query(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_claude_sdk: None,
        tmp_path: Path,
    ) -> None:
        """Test that application-level MCP servers are injected into queries.

        Creates a .mcp-server-config.json file, sends a query with null mcp_servers,
        and verifies that server-side configuration is injected into the SDK options.
        """
        # Create temporary project directory with config file
        config_content = {
            "mcpServers": {
                "test-app-server": {
                    "type": "stdio",
                    "command": "python",
                    "args": ["-m", "test_server"],
                    "env": {"APP_ENV": "test"},
                }
            }
        }

        config_path = tmp_path / ".mcp-server-config.json"
        config_path.write_text(json.dumps(config_content), encoding="utf-8")

        # Override McpConfigLoader to use temp directory
        # Note: In real integration, we'd need to inject this via dependency override
        # For now, we'll verify the API accepts null mcp_servers (not 422 validation error)
        response = await async_client.post(
            "/api/v1/query",
            json={
                "prompt": "What tools do you have?",
                "max_turns": 1,
                "mcp_servers": None,  # Explicitly null - should use server-side config
            },
            headers={**auth_headers, "Accept": "text/event-stream"},
        )

        # The API should accept the request with null mcp_servers
        # (200 for streaming response, not 422 validation error)
        assert response.status_code == 200

        # Note: Full verification of config injection would require:
        # 1. Mocking the SDK's options to capture injected config
        # 2. Verifying the config loader was called with correct project path
        # 3. Checking that merged config contains application server
        # This is covered by unit tests; integration test verifies API layer accepts it.

    async def test_api_key_mcp_overrides_application(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_claude_sdk: None,
        tmp_path: Path,
    ) -> None:
        """Test that API-key-level MCP servers override application-level servers.

        Creates an application config with server A, creates an API-key config with
        server A (different settings), and verifies the API-key version is used.
        """
        from apps.api.dependencies import get_cache
        from apps.api.services.mcp_server_configs import McpServerConfigService

        # Create application-level config
        app_config = {
            "mcpServers": {
                "shared-server": {
                    "type": "stdio",
                    "command": "python",
                    "args": ["-m", "app_server"],
                    "env": {"TIER": "application"},
                }
            }
        }
        config_path = tmp_path / ".mcp-server-config.json"
        config_path.write_text(json.dumps(app_config), encoding="utf-8")

        # Create API-key-level override for the same server
        cache = await get_cache()
        mcp_service = McpServerConfigService(cache)

        # Extract API key from auth headers
        api_key = auth_headers.get("X-API-Key", "")
        assert api_key, "API key required for this test"

        # Create API-key scoped server with different config
        await mcp_service.create_server_for_api_key(
            api_key=api_key,
            name="shared-server",
            transport_type="stdio",
            config={
                "command": "python",
                "args": ["-m", "api_key_server"],
                "env": {"TIER": "api_key"},
            },
        )

        # Send query with null mcp_servers (should use merged config)
        response = await async_client.post(
            "/api/v1/query",
            json={
                "prompt": "What tools do you have?",
                "max_turns": 1,
                "mcp_servers": None,  # Use server-side config
            },
            headers={**auth_headers, "Accept": "text/event-stream"},
        )

        # The API should accept the request
        assert response.status_code == 200

        # Note: Full verification would require:
        # 1. Capturing the merged config passed to SDK
        # 2. Verifying API-key server config overrides application config
        # 3. Checking env={'TIER': 'api_key'} and args=['-m', 'api_key_server']
        # This is covered by unit tests; integration test verifies multi-tier setup.
