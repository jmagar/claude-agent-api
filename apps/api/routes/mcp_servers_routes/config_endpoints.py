"""MCP server config/discovery/resource endpoints."""
# ruff: noqa: TC001

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, cast

import structlog
from fastapi import APIRouter, Query
from sqlalchemy.exc import IntegrityError, OperationalError

from apps.api.dependencies import (
    ApiKey,
    McpDiscoverySvc,
    McpServerConfigSvc,
)
from apps.api.exceptions import APIError
from apps.api.schemas.requests.mcp_servers import (
    McpServerCreateRequest,
    McpServerUpdateRequest,
)
from apps.api.schemas.responses import (
    McpResourceContentResponse,
    McpResourceListResponse,
    McpResourceResponse,
    McpServerConfigResponse,
    McpServerListResponse,
)

from .common import map_filesystem_server, map_server

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable
    from typing import TypeVar

    from apps.api.services.mcp_server_configs import McpServerRecord

    T = TypeVar("T")

router = APIRouter()
logger = structlog.get_logger(__name__)


async def handle_database_errors(
    operation: str,
    func: Callable[[], Awaitable[T]],
    **log_context: str | int | float | bool,
) -> T:
    """Shared error handler for database operations.

    Args:
        operation: Name of the operation being performed (e.g., "list_servers")
        func: Async function to execute with error handling
        **log_context: Additional context to include in error logs

    Returns:
        Result from the function execution

    Raises:
        APIError: Translated database error with appropriate status code
    """
    try:
        return await func()
    except OperationalError as e:
        logger.error(
            "database_operational_error",
            operation=operation,
            error=str(e),
            error_id="ERR_DB_OPERATIONAL",
            **log_context,
        )
        raise APIError(
            message="Database temporarily unavailable",
            code="DATABASE_UNAVAILABLE",
            status_code=503,
        ) from e
    except IntegrityError:
        # Let IntegrityError pass through so caller can handle it
        # (e.g., create_mcp_server needs to return 409 for duplicates)
        raise
    except APIError:
        raise
    except Exception as e:
        logger.error(
            "database_error",
            operation=operation,
            error=str(e),
            error_id="ERR_DB_UNEXPECTED",
            **log_context,
        )
        raise APIError(
            message=f"Failed to {operation.replace('_', ' ')}",
            code="INTERNAL_ERROR",
            status_code=500,
        ) from e


@router.get("", response_model=McpServerListResponse)
async def list_mcp_servers(
    api_key: ApiKey,
    mcp_discovery: McpDiscoverySvc,
    mcp_config: McpServerConfigSvc,
    source: str | None = Query(
        None,
        description="Filter by source: 'filesystem', 'database', or None for both",
    ),
) -> McpServerListResponse:
    """List all MCP server configurations from filesystem and database."""
    servers: list[McpServerConfigResponse] = []

    if source != "database":
        fs_servers = await asyncio.to_thread(mcp_discovery.discover_servers)
        for name, server in fs_servers.items():
            servers.append(map_filesystem_server(name, server))

    if source != "filesystem":
        db_servers = await handle_database_errors(
            operation="list_servers",
            func=lambda: mcp_config.list_servers_for_api_key(api_key),
        )
        for server in db_servers:
            servers.append(map_server(server))

    return McpServerListResponse(servers=servers)


@router.post("", response_model=McpServerConfigResponse, status_code=201)
async def create_mcp_server(
    request: McpServerCreateRequest,
    api_key: ApiKey,
    mcp_config: McpServerConfigSvc,
) -> McpServerConfigResponse:
    """Create a new MCP server configuration in the database."""
    try:
        server = await handle_database_errors(
            operation="create_server",
            func=lambda: mcp_config.create_server_for_api_key(
                api_key=api_key,
                name=request.name,
                transport_type=request.type,
                config=request.config,
            ),
            name=request.name,
        )
        if server is None:
            raise APIError(
                message="MCP server with this name already exists",
                code="MCP_SERVER_EXISTS",
                status_code=409,
            )
        return map_server(server)
    except IntegrityError as e:
        logger.error(
            "database_integrity_error",
            operation="create_server",
            name=request.name,
            error=str(e),
            error_id="ERR_DB_INTEGRITY",
        )
        raise APIError(
            message="MCP server with this name already exists",
            code="MCP_SERVER_EXISTS",
            status_code=409,
        ) from e


@router.get("/{name}", response_model=McpServerConfigResponse)
async def get_mcp_server(
    name: str,
    api_key: ApiKey,
    mcp_discovery: McpDiscoverySvc,
    mcp_config: McpServerConfigSvc,
) -> McpServerConfigResponse:
    """Get MCP server configuration by name."""
    if name.startswith("fs:"):
        server_name = name[3:]
        fs_servers = await asyncio.to_thread(mcp_discovery.discover_servers)
        if server_name in fs_servers:
            return map_filesystem_server(server_name, fs_servers[server_name], "fs:")
        raise APIError(
            message="Filesystem MCP server not found",
            code="MCP_SERVER_NOT_FOUND",
            status_code=404,
        )

    db_server: McpServerRecord | None = await handle_database_errors(
        operation="get_server",
        func=lambda: mcp_config.get_server_for_api_key(api_key, name),
        name=name,
    )
    if db_server is None:
        raise APIError(
            message="MCP server not found",
            code="MCP_SERVER_NOT_FOUND",
            status_code=404,
        )
    return map_server(db_server)


@router.put("/{name}", response_model=McpServerConfigResponse)
async def update_mcp_server(
    name: str,
    request: McpServerUpdateRequest,
    api_key: ApiKey,
    mcp_config: McpServerConfigSvc,
) -> McpServerConfigResponse:
    """Update a database MCP server configuration."""
    if name.startswith("fs:"):
        raise APIError(
            message="Filesystem MCP servers cannot be updated via API. Edit the config file directly.",
            code="MCP_SERVER_READONLY",
            status_code=400,
        )

    server = await handle_database_errors(
        operation="update_server",
        func=lambda: mcp_config.update_server_for_api_key(
            api_key, name, request.type, request.config
        ),
        name=name,
    )
    if server is None:
        raise APIError(
            message="MCP server not found",
            code="MCP_SERVER_NOT_FOUND",
            status_code=404,
        )
    return map_server(server)


@router.delete("/{name}", status_code=204)
async def delete_mcp_server(
    name: str,
    api_key: ApiKey,
    mcp_config: McpServerConfigSvc,
) -> None:
    """Delete a database MCP server configuration."""
    if name.startswith("fs:"):
        raise APIError(
            message="Filesystem MCP servers cannot be deleted via API. Edit the config file directly.",
            code="MCP_SERVER_READONLY",
            status_code=400,
        )

    deleted = await handle_database_errors(
        operation="delete_server",
        func=lambda: mcp_config.delete_server_for_api_key(api_key, name),
        name=name,
    )
    if not deleted:
        raise APIError(
            message="MCP server not found",
            code="MCP_SERVER_NOT_FOUND",
            status_code=404,
        )


@router.get("/{name}/resources", response_model=McpResourceListResponse)
async def list_mcp_resources(
    name: str,
    api_key: ApiKey,
    mcp_config: McpServerConfigSvc,
) -> McpResourceListResponse:
    """List MCP server resources (scoped to authenticated API key)."""
    server = await handle_database_errors(
        operation="list_resources",
        func=lambda: mcp_config.get_server_for_api_key(api_key, name),
        name=name,
    )
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
    api_key: ApiKey,
    mcp_config: McpServerConfigSvc,
) -> McpResourceContentResponse:
    """Get MCP resource content (scoped to authenticated API key)."""
    server = await handle_database_errors(
        operation="get_resource",
        func=lambda: mcp_config.get_server_for_api_key(api_key, name),
        name=name,
        uri=uri,
    )
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
