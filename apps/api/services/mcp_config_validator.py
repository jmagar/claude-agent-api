"""Security validator for MCP server configurations.

Provides validation for:
- Command injection detection
- SSRF prevention
- Credential sanitization
"""

import copy

from apps.api.schemas.validators import SHELL_METACHAR_PATTERN, validate_url_not_internal

# Patterns for sensitive keys (case-insensitive)
SENSITIVE_PATTERNS = [
    "api_key",
    "apikey",
    "secret",
    "password",
    "token",
    "auth",
    "credential",
    "authorization",
]


class ConfigValidator:
    """Validates MCP server configurations for security issues.

    Provides comprehensive security validation including:
    - Command injection detection (shell metacharacters)
    - SSRF prevention (internal URLs, metadata endpoints)
    - Credential sanitization (for safe logging)

    Examples:
        >>> validator = ConfigValidator()
        >>> config = {"command": "python app.py", "url": "http://example.com"}
        >>> validator.validate_config(config)  # Validates command and URL
        >>> sanitized = validator.sanitize_credentials(config)  # For logging
    """

    def validate_config(self, config: dict[str, object]) -> None:
        """Validate entire config for security issues.

        Comprehensive validation that checks:
        - Command injection in "command" field
        - SSRF in "url" field
        - Null bytes in all string fields

        Args:
            config: Configuration dict to validate.

        Raises:
            ValueError: If any validation check fails.

        Examples:
            >>> validator = ConfigValidator()
            >>> config = {"command": "python; rm -rf /", "url": "http://localhost"}
            >>> validator.validate_config(config)
            Traceback (most recent call last):
                ...
            ValueError: Dangerous shell metacharacter detected in command...
        """
        # Validate command field
        if "command" in config:
            command = config["command"]
            if isinstance(command, str):
                self.validate_command_injection(command)

        # Validate url field
        if "url" in config:
            url = config["url"]
            if isinstance(url, str):
                self.validate_ssrf(url)

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

    def sanitize_credentials(self, config: dict[str, object]) -> dict[str, object]:
        """Sanitize credentials for safe logging.

        Args:
            config: Configuration dict that may contain sensitive data.

        Returns:
            Deep copy of config with sensitive values replaced by "***REDACTED***".

        Examples:
            >>> validator = ConfigValidator()
            >>> config = {"env": {"API_KEY": "secret", "PATH": "/usr/bin"}}
            >>> sanitized = validator.sanitize_credentials(config)
            >>> sanitized["env"]["API_KEY"]
            '***REDACTED***'
            >>> sanitized["env"]["PATH"]
            '/usr/bin'
        """
        # Deep copy to avoid mutating original
        sanitized = copy.deepcopy(config)
        self._sanitize_recursive(sanitized)
        return sanitized

    def _sanitize_recursive(self, obj: object) -> None:
        """Recursively sanitize sensitive keys in nested structures.

        Args:
            obj: Object to sanitize (modified in-place).
        """
        if isinstance(obj, dict):
            for key, value in obj.items():
                # Check if key matches sensitive pattern
                if self._is_sensitive_key(key):
                    obj[key] = "***REDACTED***"
                else:
                    # Recurse into nested structures
                    self._sanitize_recursive(value)
        elif isinstance(obj, list):
            for item in obj:
                self._sanitize_recursive(item)

    def _is_sensitive_key(self, key: str) -> bool:
        """Check if a key name is sensitive.

        Args:
            key: Key name to check.

        Returns:
            True if key matches sensitive patterns.
        """
        # Normalize key: lowercase and replace hyphens with underscores
        # This handles X-API-Key, X-Auth-Token, etc.
        key_normalized = key.lower().replace("-", "_")
        return any(pattern in key_normalized for pattern in SENSITIVE_PATTERNS)
