"""MCP server route composition."""

from fastapi import APIRouter

from apps.api.routes.mcp_servers_routes import config_router, share_router

router = APIRouter(tags=["MCP Servers"])
router.include_router(config_router, prefix="/mcp-servers")
router.include_router(share_router, prefix="/mcp-servers")
