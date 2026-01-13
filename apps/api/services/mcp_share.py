"""MCP share token service."""

import secrets
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, cast

import structlog

from apps.api.config import get_settings
from apps.api.exceptions import CacheError
from apps.api.protocols import Cache

logger = structlog.get_logger(__name__)


@dataclass
class McpSharePayload:
    """Payload stored for MCP share tokens."""

    name: str
    config: dict[str, object]
    created_at: str


class McpShareService:
    """Service for issuing and resolving MCP share tokens."""

    def __init__(self, cache: Cache) -> None:
        """Initialize the share service.

        Args:
            cache: Cache backend for storing share payloads.
        """
        self._cache = cache
        settings = get_settings()
        self._ttl_seconds = settings.mcp_share_ttl_seconds

    def _cache_key(self, token: str) -> str:
        """Build a cache key for a share token."""
        return f"mcp_share:{token}"

    async def create_share(
        self,
        name: str,
        config: dict[str, object],
    ) -> tuple[str, McpSharePayload]:
        """Create a share token and persist its payload.

        Args:
            name: MCP server name.
            config: Sanitized MCP server configuration.

        Returns:
            Tuple of share token and payload.
        """
        payload = McpSharePayload(
            name=name,
            config=config,
            created_at=datetime.now(UTC).isoformat(),
        )

        for _ in range(5):
            token = secrets.token_urlsafe(32)
            key = self._cache_key(token)

            if await self._cache.exists(key):
                continue

            await self._cache.set_json(key, payload.__dict__, ttl=self._ttl_seconds)
            return token, payload

        logger.error("Failed to allocate MCP share token", name=name)
        raise CacheError("Unable to allocate MCP share token")

    async def get_share(self, token: str) -> McpSharePayload | None:
        """Retrieve a share payload by token.

        Args:
            token: Share token.

        Returns:
            Share payload or None when not found.
        """
        payload = await self._cache.get_json(self._cache_key(token))
        if payload is None:
            return None
        return McpSharePayload(
            name=str(payload.get("name", "")),
            config=cast("dict[str, Any]", payload.get("config", {})),
            created_at=str(payload.get("created_at", "")),
        )
