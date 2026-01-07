"""Validation utilities for request schemas.

Contains security patterns (T128) and validation functions for:
- Null byte detection
- Path traversal prevention
- SSRF prevention (internal URL blocking)
- Tool name validation
- Model name validation
"""

import re

from apps.api.types import BUILT_IN_TOOLS, VALID_MODEL_PREFIXES, VALID_SHORT_MODEL_NAMES

# Security: Pattern for dangerous shell metacharacters
SHELL_METACHAR_PATTERN = re.compile(r"[;&|`$(){}[\]<>!\n\r\\]")

# Security: Pattern for path traversal attempts
PATH_TRAVERSAL_PATTERN = re.compile(r"(?:\.\./|\.\.\\|%2e%2e%2f|%2e%2e/|\.%2e/|%2e\./)")

# Security: Pattern for null bytes
NULL_BYTE_PATTERN = re.compile(r"\x00")

# Security: Blocked internal URL patterns for SSRF prevention
BLOCKED_URL_PATTERNS = (
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "::1",
    "169.254.",  # Link-local
    "10.",  # Private Class A
    "172.16.",
    "172.17.",
    "172.18.",
    "172.19.",
    "172.20.",
    "172.21.",
    "172.22.",
    "172.23.",
    "172.24.",
    "172.25.",
    "172.26.",
    "172.27.",
    "172.28.",
    "172.29.",
    "172.30.",
    "172.31.",  # Private Class B
    "192.168.",  # Private Class C
    "metadata.google.internal",  # Cloud metadata
    "metadata.aws.",
    "instance-data",
)


def validate_no_null_bytes(value: str, field_name: str) -> str:
    """Check for null bytes (T128 security).

    Args:
        value: String to validate.
        field_name: Name of field for error message.

    Returns:
        The validated string.

    Raises:
        ValueError: If null bytes found.
    """
    if NULL_BYTE_PATTERN.search(value):
        raise ValueError(f"Null bytes not allowed in {field_name}")
    return value


def validate_no_path_traversal(value: str, field_name: str) -> str:
    """Check for path traversal attempts (T128 security).

    Args:
        value: String to validate.
        field_name: Name of field for error message.

    Returns:
        The validated string.

    Raises:
        ValueError: If path traversal detected.
    """
    if PATH_TRAVERSAL_PATTERN.search(value.lower()):
        raise ValueError(f"Path traversal not allowed in {field_name}")
    return value


def validate_url_not_internal(url: str) -> str:
    """Check URL is not targeting internal resources (T128 SSRF prevention).

    Args:
        url: URL to validate.

    Returns:
        The validated URL.

    Raises:
        ValueError: If URL targets internal resources.
    """
    url_lower = url.lower()
    for pattern in BLOCKED_URL_PATTERNS:
        if pattern in url_lower:
            raise ValueError("URLs targeting internal resources are not allowed")
    return url


def validate_tool_name(tool: str) -> bool:
    """Check if a tool name is valid.

    Args:
        tool: Tool name to validate.

    Returns:
        True if valid (built-in or MCP tool).
    """
    # Built-in tools are valid
    if tool in BUILT_IN_TOOLS:
        return True
    # MCP tools have mcp__ prefix (e.g., mcp__server__tool)
    return bool(tool.startswith("mcp__"))


def validate_model_name(model: str | None) -> str | None:
    """Validate that a model name is valid.

    Accepts:
        - Short names: "sonnet", "opus", "haiku"
        - Full model IDs: "claude-sonnet-4-*", "claude-opus-4-*", etc.

    Args:
        model: Model name to validate.

    Returns:
        Validated model name.

    Raises:
        ValueError: If model name is invalid.
    """
    if model is None:
        return None

    # Reject empty strings
    if not model:
        raise ValueError(
            "Model cannot be empty. Valid options: sonnet, opus, haiku, "
            "or full model IDs like claude-sonnet-4-20250514"
        )

    # Accept short model names
    if model in VALID_SHORT_MODEL_NAMES:
        return model

    # Accept full model IDs with valid prefixes
    if any(model.startswith(prefix) for prefix in VALID_MODEL_PREFIXES):
        return model

    # Invalid model name
    raise ValueError(
        f"Invalid model: '{model}'. Valid options: sonnet, opus, haiku, "
        "or full model IDs like claude-sonnet-4-20250514, "
        "claude-3-5-sonnet-20241022"
    )
