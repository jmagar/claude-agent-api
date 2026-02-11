"""Route modules for MCP servers."""

from .config_endpoints import router as config_router
from .share_endpoints import router as share_router

__all__ = ["config_router", "share_router"]
