"""MCP server management and share endpoints with filesystem discovery."""

import structlog
from datetime import UTC, datetime
from typing import cast

from fastapi import APIRouter, Query
from sqlalchemy.exc import IntegrityError, OperationalError

from apps.api.dependencies import (
    ApiKey,
    McpDiscoverySvc,
    McpServerConfigSvc,
    McpShareSvc,
)
from apps.api.exceptions import APIError, McpShareNotFoundError, ValidationError
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
from apps.api.services.mcp_discovery import McpServerInfo
from apps.api.services.mcp_server_configs import McpServerRecord

router = APIRouter(prefix="/mcp-servers", tags=["MCP Servers"])
logger = structlog.get_logger(__name__)

# Sensitive key patterns for credential sanitization
_SENSITIVE_ENV_PATTERNS = [
    "api_key",
    "apikey",
    "secret",
    "password",
    "token",
    "auth",
    "credential",
]
_SENSITIVE_HEADER_PATTERNS = [
    "auth",
    "token",
    "authorization",
]


def _parse_datetime(value: str | None) -> datetime:
    """Parse ISO timestamps to datetime.

    Args:
        value: ISO format timestamp string or None.

    Returns:
        Parsed datetime or current time if value is None.

    Raises:
        ValidationError: If timestamp format is invalid (corrupted data).
    """
    if value is None:
        return datetime.now(UTC)

    try:
        return datetime.fromisoformat(value)
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


def _sanitize_mapping(
    mapping: dict[str, object],
    sensitive_keys: list[str],
) -> dict[str, str]:
    """Redact values when keys match sensitive patterns.

    Returns dict[str, str] by converting all values to strings.
    """
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
        sanitized["env"] = _sanitize_mapping(
            cast("dict[str, object]", sanitized["env"]),
            _SENSITIVE_ENV_PATTERNS,
        )

    if isinstance(sanitized.get("headers"), dict):
        sanitized["headers"] = _sanitize_mapping(
            cast("dict[str, object]", sanitized["headers"]),
            _SENSITIVE_HEADER_PATTERNS,
        )

    return sanitized


def _map_filesystem_server(
    name: str,
    server: McpServerInfo,
    id_prefix: str = "fs:",
) -> McpServerConfigResponse:
    """Map filesystem server discovery result to response.

    Args:
        name: Server name from filesystem config.
        server: Server configuration dictionary.
        id_prefix: Prefix for server ID (default: "fs:").

    Returns:
        McpServerConfigResponse with sanitized credentials.
    """
    # McpServerInfo.env and .headers are dict[str, str]
    # Cast to dict[str, object] for _sanitize_mapping (str is a subtype of object)
    sanitized_env = _sanitize_mapping(
        cast("dict[str, object]", server.get("env", {})),
        _SENSITIVE_ENV_PATTERNS,
    )
    sanitized_headers = _sanitize_mapping(
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


def _map_server(record: McpServerRecord) -> McpServerConfigResponse:
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
    api_key: ApiKey,
    mcp_discovery: McpDiscoverySvc,
    mcp_config: McpServerConfigSvc,
    source: str | None = Query(
        None,
        description="Filter by source: 'filesystem', 'database', or None for both",
    ),
) -> McpServerListResponse:
    """List all MCP server configurations from filesystem and database.

    MCP servers are discovered from:
    - Filesystem: ~/.claude.json (global), .mcp.json, .claude/mcp.json (project)
    - Database: Servers created via API (scoped to authenticated API key)

    Use the 'source' query param to filter by source.
    Note: Filesystem server env/headers are redacted for security.
    """
    servers: list[McpServerConfigResponse] = []

    # Get filesystem servers (unless filtering to database only)
    if source != "database":
        fs_servers = mcp_discovery.discover_servers()
        for name, server in fs_servers.items():
            servers.append(_map_filesystem_server(name, server))

    # Get database servers (unless filtering to filesystem only)
    # Filter by authenticated API key
    if source != "filesystem":
        try:
            db_servers = await mcp_config.list_servers_for_api_key(api_key)
            for s in db_servers:
                servers.append(_map_server(s))
        except OperationalError as e:
            logger.error(
                "database_operational_error",
                operation="list_servers",
                error=str(e),
                error_id="ERR_DB_OPERATIONAL",
            )
            raise APIError(
                message="Database temporarily unavailable",
                code="DATABASE_UNAVAILABLE",
                status_code=503,
            ) from e
        except APIError:
            # Re-raise APIError (including ValidationError subclass) to preserve status codes
            raise
        except Exception as e:
            logger.error(
                "database_error",
                operation="list_servers",
                error=str(e),
                error_id="ERR_DB_UNEXPECTED",
            )
            raise APIError(
                message="Failed to retrieve MCP servers",
                code="INTERNAL_ERROR",
                status_code=500,
            ) from e

    return McpServerListResponse(servers=servers)


@router.post("", response_model=McpServerConfigResponse, status_code=201)
async def create_mcp_server(
    request: McpServerCreateRequest,
    api_key: ApiKey,
    mcp_config: McpServerConfigSvc,
) -> McpServerConfigResponse:
    """Create a new MCP server configuration in the database.

    Note: To add filesystem-based MCP servers, edit ~/.claude.json (global)
    or create .mcp.json / .claude/mcp.json in your project.
    Server is scoped to the authenticated API key.

    Raises:
        APIError: If server already exists, database error, or validation fails.
    """
    try:
        server = await mcp_config.create_server_for_api_key(
            api_key=api_key,
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
    except OperationalError as e:
        logger.error(
            "database_operational_error",
            operation="create_server",
            name=request.name,
            error=str(e),
            error_id="ERR_DB_OPERATIONAL",
        )
        raise APIError(
            message="Database temporarily unavailable",
            code="DATABASE_UNAVAILABLE",
            status_code=503,
        ) from e
    except APIError:
        # Re-raise our own errors
        raise
    except Exception as e:
        logger.error(
            "database_error",
            operation="create_server",
            name=request.name,
            error=str(e),
            error_id="ERR_DB_UNEXPECTED",
        )
        raise APIError(
            message="Failed to create MCP server",
            code="INTERNAL_ERROR",
            status_code=500,
        ) from e


@router.get("/{name}", response_model=McpServerConfigResponse)
async def get_mcp_server(
    name: str,
    api_key: ApiKey,
    mcp_discovery: McpDiscoverySvc,
    mcp_config: McpServerConfigSvc,
) -> McpServerConfigResponse:
    """Get MCP server configuration by name.

    For filesystem servers, use the 'fs:' prefix (e.g., 'fs:my-server').
    For database servers, use the name directly (scoped to authenticated API key).
    """
    # Check if it's a filesystem server
    if name.startswith("fs:"):
        server_name = name[3:]  # Remove 'fs:' prefix
        fs_servers = mcp_discovery.discover_servers()

        if server_name in fs_servers:
            server = fs_servers[server_name]
            return _map_filesystem_server(server_name, server, id_prefix="fs:")

        raise APIError(
            message="Filesystem MCP server not found",
            code="MCP_SERVER_NOT_FOUND",
            status_code=404,
        )

    # Otherwise, look up in database (scoped to API key)
    try:
        db_server: McpServerRecord | None = await mcp_config.get_server_for_api_key(
            api_key, name
        )
        if db_server is None:
            raise APIError(
                message="MCP server not found",
                code="MCP_SERVER_NOT_FOUND",
                status_code=404,
            )
        return _map_server(db_server)
    except OperationalError as e:
        logger.error(
            "database_operational_error",
            operation="get_server",
            name=name,
            error=str(e),
            error_id="ERR_DB_OPERATIONAL",
        )
        raise APIError(
            message="Database temporarily unavailable",
            code="DATABASE_UNAVAILABLE",
            status_code=503,
        ) from e
    except APIError:
        # Re-raise our own errors (404)
        raise
    except Exception as e:
        logger.error(
            "database_error",
            operation="get_server",
            name=name,
            error=str(e),
            error_id="ERR_DB_UNEXPECTED",
        )
        raise APIError(
            message="Failed to retrieve MCP server",
            code="INTERNAL_ERROR",
            status_code=500,
        ) from e


@router.put("/{name}", response_model=McpServerConfigResponse)
async def update_mcp_server(
    name: str,
    request: McpServerUpdateRequest,
    api_key: ApiKey,
    mcp_config: McpServerConfigSvc,
) -> McpServerConfigResponse:
    """Update a database MCP server configuration.

    Note: Filesystem MCP servers cannot be updated via API.
    Edit ~/.claude.json or .mcp.json directly.
    Updates are scoped to the authenticated API key.
    """
    # Filesystem servers cannot be updated via API
    if name.startswith("fs:"):
        raise APIError(
            message="Filesystem MCP servers cannot be updated via API. Edit the config file directly.",
            code="MCP_SERVER_READONLY",
            status_code=400,
        )

    try:
        server = await mcp_config.update_server_for_api_key(
            api_key, name, request.type, request.config
        )
        if server is None:
            raise APIError(
                message="MCP server not found",
                code="MCP_SERVER_NOT_FOUND",
                status_code=404,
            )
        return _map_server(server)
    except OperationalError as e:
        logger.error(
            "database_operational_error",
            operation="update_server",
            name=name,
            error=str(e),
            error_id="ERR_DB_OPERATIONAL",
        )
        raise APIError(
            message="Database temporarily unavailable",
            code="DATABASE_UNAVAILABLE",
            status_code=503,
        ) from e
    except APIError:
        # Re-raise our own errors
        raise
    except Exception as e:
        logger.error(
            "database_error",
            operation="update_server",
            name=name,
            error=str(e),
            error_id="ERR_DB_UNEXPECTED",
        )
        raise APIError(
            message="Failed to update MCP server",
            code="INTERNAL_ERROR",
            status_code=500,
        ) from e


@router.delete("/{name}", status_code=204)
async def delete_mcp_server(
    name: str,
    api_key: ApiKey,
    mcp_config: McpServerConfigSvc,
) -> None:
    """Delete a database MCP server configuration.

    Note: Filesystem MCP servers cannot be deleted via API.
    Edit ~/.claude.json or .mcp.json directly.
    Deletion is scoped to the authenticated API key.
    """
    # Filesystem servers cannot be deleted via API
    if name.startswith("fs:"):
        raise APIError(
            message="Filesystem MCP servers cannot be deleted via API. Edit the config file directly.",
            code="MCP_SERVER_READONLY",
            status_code=400,
        )

    try:
        deleted = await mcp_config.delete_server_for_api_key(api_key, name)
        if not deleted:
            raise APIError(
                message="MCP server not found",
                code="MCP_SERVER_NOT_FOUND",
                status_code=404,
            )
    except OperationalError as e:
        logger.error(
            "database_operational_error",
            operation="delete_server",
            name=name,
            error=str(e),
            error_id="ERR_DB_OPERATIONAL",
        )
        raise APIError(
            message="Database temporarily unavailable",
            code="DATABASE_UNAVAILABLE",
            status_code=503,
        ) from e
    except APIError:
        # Re-raise our own errors
        raise
    except Exception as e:
        logger.error(
            "database_error",
            operation="delete_server",
            name=name,
            error=str(e),
            error_id="ERR_DB_UNEXPECTED",
        )
        raise APIError(
            message="Failed to delete MCP server",
            code="INTERNAL_ERROR",
            status_code=500,
        ) from e


@router.get("/{name}/resources", response_model=McpResourceListResponse)
async def list_mcp_resources(
    name: str,
    api_key: ApiKey,
    mcp_config: McpServerConfigSvc,
) -> McpResourceListResponse:
    """List MCP server resources (scoped to authenticated API key).

    Raises:
        APIError: If server not found or database error occurs.
    """
    try:
        server = await mcp_config.get_server_for_api_key(api_key, name)
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
    except OperationalError as e:
        logger.error(
            "database_operational_error",
            operation="list_resources",
            name=name,
            error=str(e),
            error_id="ERR_DB_OPERATIONAL",
        )
        raise APIError(
            message="Database temporarily unavailable",
            code="DATABASE_UNAVAILABLE",
            status_code=503,
        ) from e
    except APIError:
        # Re-raise our own errors
        raise
    except Exception as e:
        logger.error(
            "database_error",
            operation="list_resources",
            name=name,
            error=str(e),
            error_id="ERR_DB_UNEXPECTED",
        )
        raise APIError(
            message="Failed to retrieve MCP server resources",
            code="INTERNAL_ERROR",
            status_code=500,
        ) from e


@router.get("/{name}/resources/{uri:path}", response_model=McpResourceContentResponse)
async def get_mcp_resource(
    name: str,
    uri: str,
    api_key: ApiKey,
    mcp_config: McpServerConfigSvc,
) -> McpResourceContentResponse:
    """Get MCP resource content (scoped to authenticated API key).

    Raises:
        APIError: If server or resource not found, or database error occurs.
    """
    try:
        server = await mcp_config.get_server_for_api_key(api_key, name)
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
    except OperationalError as e:
        logger.error(
            "database_operational_error",
            operation="get_resource",
            name=name,
            uri=uri,
            error=str(e),
            error_id="ERR_DB_OPERATIONAL",
        )
        raise APIError(
            message="Database temporarily unavailable",
            code="DATABASE_UNAVAILABLE",
            status_code=503,
        ) from e
    except APIError:
        # Re-raise our own errors
        raise
    except Exception as e:
        logger.error(
            "database_error",
            operation="get_resource",
            name=name,
            uri=uri,
            error=str(e),
            error_id="ERR_DB_UNEXPECTED",
        )
        raise APIError(
            message="Failed to retrieve MCP resource",
            code="INTERNAL_ERROR",
            status_code=500,
        ) from e


@router.post("/{name}/share", response_model=McpShareCreateResponse)
async def create_mcp_share(
    name: str,
    payload: McpShareCreateRequest,
    _api_key: ApiKey,
    mcp_share: McpShareSvc,
) -> McpShareCreateResponse:
    """Create and persist a share token for an MCP server."""
    sanitized_config = sanitize_mcp_config(payload.config)
    token, share_payload = await mcp_share.create_share(
        name=name, config=sanitized_config
    )

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
    mcp_share: McpShareSvc,
) -> McpSharePayloadResponse:
    """Resolve a share token to its persisted payload."""
    payload = await mcp_share.get_share(token)
    if payload is None:
        raise McpShareNotFoundError(token)

    return McpSharePayloadResponse(
        name=payload.name,
        config=payload.config,
        created_at=payload.created_at,
    )
