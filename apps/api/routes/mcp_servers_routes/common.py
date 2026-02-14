"""Shared helpers for MCP server routes."""

from datetime import UTC, datetime
from typing import cast

import structlog

from apps.api.exceptions import ValidationError
from apps.api.schemas.responses import McpServerConfigResponse
from apps.api.services.mcp_discovery import McpServerInfo
from apps.api.services.mcp_server_configs import McpServerRecord

logger = structlog.get_logger(__name__)

_SENSITIVE_ENV_PATTERNS = [
    "api_key",
    "apikey",
    "secret",
    "password",
    "token",
    "auth",
    "credential",
]
_SENSITIVE_HEADER_PATTERNS = ["auth", "token", "authorization"]


def parse_datetime(value: str | None) -> datetime | None:
    """Parse ISO timestamps to datetime with strict validation."""
    if value is None:
        return None

    try:
        parsed = datetime.fromisoformat(value)
        # Ensure timezone-aware datetime (add UTC if naive)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed
    except ValueError as e:
        logger.error(
            "datetime_parse_failed",
            value=value,
            error=str(e),
            error_id="ERR_DATETIME_PARSE_FAILED",
        )
        raise ValidationError(
            message=f"Invalid timestamp format: {value}",
            field="timestamp",
        ) from e


def sanitize_mapping(
    mapping: dict[str, object],
    sensitive_keys: list[str],
) -> dict[str, str]:
    """Redact values when keys match sensitive patterns."""
    sanitized: dict[str, str] = {}
    for key, value in mapping.items():
        lower_key = key.lower()
        if any(pattern in lower_key for pattern in sensitive_keys):
            sanitized[key] = "***REDACTED***"
        else:
            sanitized[key] = str(value) if value is not None else ""
    return sanitized


def sanitize_mcp_config(config: dict[str, object]) -> dict[str, object]:
    """Sanitize MCP server config for sharing."""
    sanitized: dict[str, object] = dict(config)

    if isinstance(sanitized.get("env"), dict):
        sanitized["env"] = sanitize_mapping(
            cast("dict[str, object]", sanitized["env"]),
            _SENSITIVE_ENV_PATTERNS,
        )

    if isinstance(sanitized.get("headers"), dict):
        sanitized["headers"] = sanitize_mapping(
            cast("dict[str, object]", sanitized["headers"]),
            _SENSITIVE_HEADER_PATTERNS,
        )

    return sanitized


def map_filesystem_server(
    name: str,
    server: McpServerInfo,
    id_prefix: str = "fs:",
) -> McpServerConfigResponse:
    """Map filesystem server discovery result to API response."""
    sanitized_env = sanitize_mapping(
        cast("dict[str, object]", server.get("env", {})),
        _SENSITIVE_ENV_PATTERNS,
    )
    sanitized_headers = sanitize_mapping(
        cast("dict[str, object]", server.get("headers", {})),
        _SENSITIVE_HEADER_PATTERNS,
    )

    return McpServerConfigResponse(
        id=f"{id_prefix}{name}",
        name=name,
        transport_type=cast("str", server.get("type", "stdio")),
        command=server.get("command"),
        args=cast("list[str]", server.get("args", [])),
        url=server.get("url"),
        headers=sanitized_headers,
        env=sanitized_env,
        enabled=True,
        status="active",
        source="filesystem",
    )


def map_server(record: McpServerRecord) -> McpServerConfigResponse:
    """Map database server record to response.

    Sanitizes sensitive headers and environment variables to prevent credential leakage.
    """
    # Sanitize credentials before returning to client
    sanitized_env = (
        sanitize_mapping(
            cast("dict[str, object]", record.env),
            _SENSITIVE_ENV_PATTERNS,
        )
        if record.env
        else {}
    )
    sanitized_headers = (
        sanitize_mapping(
            cast("dict[str, object]", record.headers),
            _SENSITIVE_HEADER_PATTERNS,
        )
        if record.headers
        else {}
    )

    return McpServerConfigResponse(
        id=record.id,
        name=record.name,
        transport_type=record.transport_type,
        command=record.command,
        args=record.args,
        url=record.url,
        headers=sanitized_headers,
        env=sanitized_env,
        enabled=record.enabled,
        status=record.status,
        error=record.error,
        created_at=parse_datetime(record.created_at),
        updated_at=parse_datetime(record.updated_at) if record.updated_at else None,
        metadata=record.metadata,
        source="database",
    )
