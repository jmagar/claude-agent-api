"""Security validator for MCP server configurations.

Provides validation for:
- Command injection detection
- SSRF prevention
- Credential sanitization
"""

from apps.api.schemas.validators import SHELL_METACHAR_PATTERN, validate_url_not_internal


class ConfigValidator:
    """Validates MCP server configurations for security issues."""

    def validate_command_injection(self, command: str | None) -> str | None:
        """Validate command for shell metacharacters.

        Args:
            command: Command string to validate (e.g., "python script.py").
                     None is treated as valid (no command to validate).

        Returns:
            The validated command string, or None if input was None.

        Raises:
            ValueError: If shell metacharacters are detected in command.

        Examples:
            >>> validator = ConfigValidator()
            >>> validator.validate_command_injection("python app.py")
            'python app.py'
            >>> validator.validate_command_injection("python; rm -rf /")
            Traceback (most recent call last):
                ...
            ValueError: Dangerous shell metacharacter detected in command
        """
        if command is None:
            return None

        if SHELL_METACHAR_PATTERN.search(command):
            raise ValueError(
                "Dangerous shell metacharacter detected in command. "
                "Commands must not contain: ; & | ` $ ( ) { } [ ] < > ! \\ newlines"
            )

        return command

    def validate_ssrf(self, url: str | None) -> str | None:
        """Validate URL for SSRF prevention.

        Args:
            url: URL to validate (e.g., "http://example.com/api").
                 None is treated as valid (no URL to validate).

        Returns:
            The validated URL string, or None if input was None.

        Raises:
            ValueError: If URL targets internal resources (private IPs,
                       loopback, link-local, metadata endpoints).

        Examples:
            >>> validator = ConfigValidator()
            >>> validator.validate_ssrf("https://api.example.com")
            'https://api.example.com'
            >>> validator.validate_ssrf("http://localhost/api")
            Traceback (most recent call last):
                ...
            ValueError: URLs targeting internal resources are not allowed
        """
        if url is None:
            return None

        # Use existing validator from schemas/validators.py
        return validate_url_not_internal(url)
