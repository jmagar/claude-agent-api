"""MCP server share-token endpoints."""

from fastapi import APIRouter, Header

from apps.api.dependencies import ApiKey, McpShareSvc
from apps.api.exceptions import McpShareNotFoundError
from apps.api.schemas.requests.mcp_share import McpShareCreateRequest
from apps.api.schemas.responses import McpShareCreateResponse, McpSharePayloadResponse

from .common import sanitize_mcp_config

router = APIRouter()


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


@router.get("/share", response_model=McpSharePayloadResponse)
async def get_mcp_share(
    _api_key: ApiKey,
    mcp_share: McpShareSvc,
    x_share_token: str = Header(..., alias="X-Share-Token"),
) -> McpSharePayloadResponse:
    """Resolve a share token to its persisted payload.

    Args:
        _api_key: API key from auth middleware.
        mcp_share: Injected MCP share service.
        x_share_token: Share token from X-Share-Token header (avoids exposure in access logs).

    Returns:
        MCP share payload with configuration and metadata.

    Raises:
        McpShareNotFoundError: If share token not found.
    """
    payload = await mcp_share.get_share(x_share_token)
    if payload is None:
        raise McpShareNotFoundError(x_share_token)

    return McpSharePayloadResponse(
        name=payload.name,
        config=payload.config,
        created_at=payload.created_at,
    )
