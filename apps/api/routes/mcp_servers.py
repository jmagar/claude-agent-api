"""MCP server management and share endpoints."""

from datetime import datetime

from fastapi import APIRouter

from apps.api.dependencies import ApiKey, Cache
from apps.api.exceptions import APIError, McpShareNotFoundError
from apps.api.schemas.requests.mcp_servers import (
    McpServerCreateRequest,
    McpServerUpdateRequest,
)
from apps.api.schemas.requests.mcp_share import McpShareCreateRequest
from apps.api.schemas.responses import (
    McpResourceContentResponse,
    McpResourceListResponse,
    McpResourceResponse,
    McpServerConfigResponse,
    McpServerListResponse,
    McpShareCreateResponse,
    McpSharePayloadResponse,
)
from apps.api.services.mcp_server_configs import McpServerConfigService
from apps.api.services.mcp_share import McpShareService

router = APIRouter(prefix="/mcp-servers", tags=["MCP Servers"])


def _parse_datetime(value: str | None) -> datetime:
    """<summary>Parse ISO timestamps to datetime.</summary>"""
    if value:
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            pass
    return datetime.utcnow()


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


def _map_server(record) -> McpServerConfigResponse:
    """<summary>Map server record to response.</summary>"""
    return McpServerConfigResponse(
        id=record.id,
        name=record.name,
        transport_type=record.transport_type,
        command=record.command,
        args=record.args,
        url=record.url,
        headers=record.headers,
        env=record.env,
        enabled=record.enabled,
        status=record.status,
        error=record.error,
        created_at=_parse_datetime(record.created_at),
        updated_at=_parse_datetime(record.updated_at) if record.updated_at else None,
        metadata=record.metadata,
    )


@router.get("", response_model=McpServerListResponse)
async def list_mcp_servers(
    _api_key: ApiKey,
    cache: Cache,
) -> McpServerListResponse:
    """<summary>List MCP server configurations.</summary>"""
    service = McpServerConfigService(cache)
    servers = await service.list_servers()
    return McpServerListResponse(servers=[_map_server(s) for s in servers])


@router.post("", response_model=McpServerConfigResponse, status_code=201)
async def create_mcp_server(
    request: McpServerCreateRequest,
    _api_key: ApiKey,
    cache: Cache,
) -> McpServerConfigResponse:
    """<summary>Create a new MCP server configuration.</summary>"""
    service = McpServerConfigService(cache)
    server = await service.create_server(
        name=request.name,
        transport_type=request.type,
        config=request.config,
    )
    if server is None:
        raise APIError(
            message="MCP server with this name already exists",
            code="MCP_SERVER_EXISTS",
            status_code=409,
        )
    return _map_server(server)


@router.get("/{name}", response_model=McpServerConfigResponse)
async def get_mcp_server(
    name: str,
    _api_key: ApiKey,
    cache: Cache,
) -> McpServerConfigResponse:
    """<summary>Get MCP server configuration.</summary>"""
    service = McpServerConfigService(cache)
    server = await service.get_server(name)
    if server is None:
        raise APIError(
            message="MCP server not found",
            code="MCP_SERVER_NOT_FOUND",
            status_code=404,
        )
    return _map_server(server)


@router.put("/{name}", response_model=McpServerConfigResponse)
async def update_mcp_server(
    name: str,
    request: McpServerUpdateRequest,
    _api_key: ApiKey,
    cache: Cache,
) -> McpServerConfigResponse:
    """<summary>Update MCP server configuration.</summary>"""
    service = McpServerConfigService(cache)
    server = await service.update_server(name, request.type, request.config)
    if server is None:
        raise APIError(
            message="MCP server not found",
            code="MCP_SERVER_NOT_FOUND",
            status_code=404,
        )
    return _map_server(server)


@router.delete("/{name}", status_code=204)
async def delete_mcp_server(
    name: str,
    _api_key: ApiKey,
    cache: Cache,
) -> None:
    """<summary>Delete MCP server configuration.</summary>"""
    service = McpServerConfigService(cache)
    deleted = await service.delete_server(name)
    if not deleted:
        raise APIError(
            message="MCP server not found",
            code="MCP_SERVER_NOT_FOUND",
            status_code=404,
        )


@router.get("/{name}/resources", response_model=McpResourceListResponse)
async def list_mcp_resources(
    name: str,
    _api_key: ApiKey,
    cache: Cache,
) -> McpResourceListResponse:
    """<summary>List MCP server resources.</summary>"""
    service = McpServerConfigService(cache)
    server = await service.get_server(name)
    if server is None:
        raise APIError(
            message="MCP server not found",
            code="MCP_SERVER_NOT_FOUND",
            status_code=404,
        )

    resources = server.resources or []
    return McpResourceListResponse(
        resources=[
            McpResourceResponse(
                uri=str(resource.get("uri", "")),
                name=resource.get("name"),
                description=resource.get("description"),
                mimeType=resource.get("mimeType"),
            )
            for resource in resources
        ]
    )


@router.get("/{name}/resources/{uri:path}", response_model=McpResourceContentResponse)
async def get_mcp_resource(
    name: str,
    uri: str,
    _api_key: ApiKey,
    cache: Cache,
) -> McpResourceContentResponse:
    """<summary>Get MCP resource content.</summary>"""
    service = McpServerConfigService(cache)
    server = await service.get_server(name)
    if server is None:
        raise APIError(
            message="MCP server not found",
            code="MCP_SERVER_NOT_FOUND",
            status_code=404,
        )

    for resource in server.resources or []:
        if str(resource.get("uri")) == uri:
            return McpResourceContentResponse(
                uri=uri,
                mimeType=resource.get("mimeType"),
                text=resource.get("text"),
            )

    raise APIError(
        message="Resource not found",
        code="MCP_RESOURCE_NOT_FOUND",
        status_code=404,
    )


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
