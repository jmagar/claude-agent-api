"""MCP server share endpoints."""

from fastapi import APIRouter

from apps.api.dependencies import ApiKey, Cache
from apps.api.exceptions import McpShareNotFoundError
from apps.api.schemas.requests.mcp_share import McpShareCreateRequest
from apps.api.schemas.responses import (
    McpShareCreateResponse,
    McpSharePayloadResponse,
)
from apps.api.services.mcp_share import McpShareService

router = APIRouter(prefix="/mcp-servers", tags=["MCP Servers"])


def _sanitize_mapping(
    mapping: dict[str, object],
    sensitive_keys: list[str],
) -> dict[str, object]:
    """Redact values when keys match sensitive patterns."""
    sanitized: dict[str, object] = {}
    for key, value in mapping.items():
        lower_key = key.lower()
        if any(pattern in lower_key for pattern in sensitive_keys):
            sanitized[key] = "***REDACTED***"
        else:
            sanitized[key] = value
    return sanitized


def sanitize_mcp_config(config: dict[str, object]) -> dict[str, object]:
    """Sanitize MCP server config for sharing."""
    sanitized: dict[str, object] = dict(config)

    if isinstance(sanitized.get("env"), dict):
        sanitized["env"] = _sanitize_mapping(
            sanitized["env"],
            ["api_key", "apikey", "secret", "password", "token", "auth", "credential"],
        )

    if isinstance(sanitized.get("headers"), dict):
        sanitized["headers"] = _sanitize_mapping(
            sanitized["headers"],
            ["auth", "token"],
        )

    return sanitized


@router.post("/{name}/share", response_model=McpShareCreateResponse)
async def create_mcp_share(
    name: str,
    payload: McpShareCreateRequest,
    _api_key: ApiKey,
    cache: Cache,
) -> McpShareCreateResponse:
    """Create and persist a share token for an MCP server."""
    service = McpShareService(cache)
    sanitized_config = sanitize_mcp_config(payload.config)
    token, share_payload = await service.create_share(name=name, config=sanitized_config)

    return McpShareCreateResponse(
        share_token=token,
        name=share_payload.name,
        config=share_payload.config,
        created_at=share_payload.created_at,
    )


@router.get("/share/{token}", response_model=McpSharePayloadResponse)
async def get_mcp_share(
    token: str,
    _api_key: ApiKey,
    cache: Cache,
) -> McpSharePayloadResponse:
    """Resolve a share token to its persisted payload."""
    service = McpShareService(cache)
    payload = await service.get_share(token)
    if payload is None:
        raise McpShareNotFoundError(token)

    return McpSharePayloadResponse(
        name=payload.name,
        config=payload.config,
        created_at=payload.created_at,
    )
