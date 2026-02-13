"""MCP server route composition."""

from fastapi import APIRouter

from apps.api.routes.mcp_servers_routes import (
    _parse_datetime,
    config_router,
    share_router,
)

router = APIRouter(tags=["MCP Servers"])
router.include_router(config_router, prefix="/mcp-servers")
router.include_router(share_router, prefix="/mcp-servers")

__all__ = ["_parse_datetime", "router"]
