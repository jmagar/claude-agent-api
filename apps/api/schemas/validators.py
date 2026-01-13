"""Validation utilities for request schemas.

Contains security patterns (T128) and validation functions for:
- Null byte detection
- Path traversal prevention
- SSRF prevention (internal URL blocking)
- Tool name validation
- Model name validation
"""

import ipaddress
import re
from urllib.parse import urlparse

from apps.api.constants import BUILT_IN_TOOLS
from apps.api.types import (
    VALID_FULL_MODEL_IDS,
    VALID_MODEL_PREFIXES,
    VALID_SHORT_MODEL_NAMES,
)

# Security: Pattern for dangerous shell metacharacters
SHELL_METACHAR_PATTERN = re.compile(r"[;&|`$(){}[\]<>!\n\r\\]")

# Security: Pattern for path traversal attempts
PATH_TRAVERSAL_PATTERN = re.compile(r"(?:\.\./|\.\.\\|%2e%2e%2f|%2e%2e/|\.%2e/|%2e\./)")

# Security: Pattern for null bytes
NULL_BYTE_PATTERN = re.compile(r"\x00")


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
    parsed = urlparse(url)
    hostname = parsed.hostname

    if not hostname:
        raise ValueError("Invalid URL: missing hostname")

    # Check for blocked hostnames
    hostname_lower = hostname.lower()
    if (
        hostname_lower in ("localhost", "metadata.google.internal")
        or hostname_lower.startswith("metadata.aws.")
        or hostname_lower == "instance-data"
    ):
        raise ValueError("URLs targeting internal resources are not allowed")

    # Try to parse as IP address
    try:
        ip = ipaddress.ip_address(hostname)
    except ValueError:
        # Not an IP address, which is fine - hostname validation passed
        return url

    # If we got here, it's a valid IP - check if it's internal
    if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
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
        - Full model IDs: "claude-opus-4-20250514", "claude-sonnet-4-5-20250929", etc.

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
            "or full model IDs like claude-opus-4-5-20251101"
        )

    # Accept short model names
    if model in VALID_SHORT_MODEL_NAMES:
        return model

    # Accept exact full model IDs
    if model in VALID_FULL_MODEL_IDS:
        return model

    # Accept full model IDs with valid prefixes (for future model versions)
    if any(model.startswith(prefix) for prefix in VALID_MODEL_PREFIXES):
        return model

    # Invalid model name
    raise ValueError(
        f"Invalid model: '{model}'. Valid options: sonnet, opus, haiku, "
        "or full model IDs like claude-opus-4-5-20251101, "
        "claude-sonnet-4-5-20250929, claude-3-7-sonnet-20250219"
    )
