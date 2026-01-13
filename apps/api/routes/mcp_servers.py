"""MCP server management and share endpoints with filesystem discovery."""

from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from fastapi import APIRouter, Query

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
from apps.api.services.mcp_discovery import McpDiscoveryService
from apps.api.services.mcp_server_configs import McpServerConfigService
from apps.api.services.mcp_share import McpShareService

router = APIRouter(prefix="/mcp-servers", tags=["MCP Servers"])


def _get_mcp_discovery_service() -> McpDiscoveryService:
    """Get MCP discovery service for filesystem discovery."""
    return McpDiscoveryService(project_path=Path.cwd())


def _parse_datetime(value: str | None) -> datetime:
    """<summary>Parse ISO timestamps to datetime.</summary>"""
    if value:
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            pass
    return datetime.now(UTC)


def _sanitize_mapping(
    mapping: dict[str, Any],
    sensitive_keys: list[str],
) -> dict[str, Any]:
    """Redact values when keys match sensitive patterns."""
    sanitized: dict[str, Any] = {}
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
            cast("dict[str, Any]", sanitized["env"]),
            ["api_key", "apikey", "secret", "password", "token", "auth", "credential"],
        )

    if isinstance(sanitized.get("headers"), dict):
        sanitized["headers"] = _sanitize_mapping(
            cast("dict[str, Any]", sanitized["headers"]),
            ["auth", "token"],
        )

    return sanitized


def _map_server(record) -> McpServerConfigResponse:
    """<summary>Map database server record to response.</summary>"""
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
        source="database",
    )


@router.get("", response_model=McpServerListResponse)
async def list_mcp_servers(
    _api_key: ApiKey,
    cache: Cache,
    source: str | None = Query(
        None,
        description="Filter by source: 'filesystem', 'database', or None for both",
    ),
) -> McpServerListResponse:
    """List all MCP server configurations from filesystem and database.

    MCP servers are discovered from:
    - Filesystem: ~/.claude.json (global), .mcp.json, .claude/mcp.json (project)
    - Database: Servers created via API

    Use the 'source' query param to filter by source.
    Note: Filesystem server env/headers are redacted for security.
    """
    servers: list[McpServerConfigResponse] = []

    # Get filesystem servers (unless filtering to database only)
    if source != "database":
        fs_service = _get_mcp_discovery_service()
        fs_servers = fs_service.discover_servers()
        for name, server in fs_servers.items():
            # Redact sensitive data from filesystem servers
            env = server.get("env", {})
            headers = server.get("headers", {})
            sanitized_env = _sanitize_mapping(
                env,
                ["api_key", "apikey", "secret", "password", "token", "auth", "credential"],
            )
            sanitized_headers = _sanitize_mapping(
                headers,
                ["auth", "token", "authorization"],
            )

            servers.append(
                McpServerConfigResponse(
                    id=f"fs:{name}",  # Prefix to distinguish from DB
                    name=name,
                    transport_type=server.get("type", "stdio"),
                    command=server.get("command"),
                    args=server.get("args", []),
                    url=server.get("url"),
                    headers=sanitized_headers,
                    env=sanitized_env,
                    enabled=True,
                    status="active",
                    source="filesystem",
                )
            )

    # Get database servers (unless filtering to filesystem only)
    if source != "filesystem":
        db_service = McpServerConfigService(cache)
        db_servers = await db_service.list_servers()
        for s in db_servers:
            servers.append(_map_server(s))

    return McpServerListResponse(servers=servers)


@router.post("", response_model=McpServerConfigResponse, status_code=201)
async def create_mcp_server(
    request: McpServerCreateRequest,
    _api_key: ApiKey,
    cache: Cache,
) -> McpServerConfigResponse:
    """Create a new MCP server configuration in the database.

    Note: To add filesystem-based MCP servers, edit ~/.claude.json (global)
    or create .mcp.json / .claude/mcp.json in your project.
    """
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
    """Get MCP server configuration by name.

    For filesystem servers, use the 'fs:' prefix (e.g., 'fs:my-server').
    For database servers, use the name directly.
    """
    # Check if it's a filesystem server
    if name.startswith("fs:"):
        server_name = name[3:]  # Remove 'fs:' prefix
        fs_service = _get_mcp_discovery_service()
        fs_servers = fs_service.discover_servers()

        if server_name in fs_servers:
            server = fs_servers[server_name]
            # Redact sensitive data
            env = server.get("env", {})
            headers = server.get("headers", {})
            sanitized_env = _sanitize_mapping(
                env,
                ["api_key", "apikey", "secret", "password", "token", "auth", "credential"],
            )
            sanitized_headers = _sanitize_mapping(
                headers,
                ["auth", "token", "authorization"],
            )

            return McpServerConfigResponse(
                id=name,
                name=server_name,
                transport_type=server.get("type", "stdio"),
                command=server.get("command"),
                args=server.get("args", []),
                url=server.get("url"),
                headers=sanitized_headers,
                env=sanitized_env,
                enabled=True,
                status="active",
                source="filesystem",
            )

        raise APIError(
            message="Filesystem MCP server not found",
            code="MCP_SERVER_NOT_FOUND",
            status_code=404,
        )

    # Otherwise, look up in database
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
    """Update a database MCP server configuration.

    Note: Filesystem MCP servers cannot be updated via API.
    Edit ~/.claude.json or .mcp.json directly.
    """
    # Filesystem servers cannot be updated via API
    if name.startswith("fs:"):
        raise APIError(
            message="Filesystem MCP servers cannot be updated via API. Edit the config file directly.",
            code="MCP_SERVER_READONLY",
            status_code=400,
        )

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
    """Delete a database MCP server configuration.

    Note: Filesystem MCP servers cannot be deleted via API.
    Edit ~/.claude.json or .mcp.json directly.
    """
    # Filesystem servers cannot be deleted via API
    if name.startswith("fs:"):
        raise APIError(
            message="Filesystem MCP servers cannot be deleted via API. Edit the config file directly.",
            code="MCP_SERVER_READONLY",
            status_code=400,
        )

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
                name=cast("str | None", resource.get("name")),
                description=cast("str | None", resource.get("description")),
                mimeType=cast("str | None", resource.get("mimeType")),
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
                mimeType=cast("str | None", resource.get("mimeType")),
                text=cast("str | None", resource.get("text")),
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
