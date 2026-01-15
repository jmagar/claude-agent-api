"""MCP server configuration service."""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from apps.api.protocols import Cache


@dataclass
class McpServerRecord:
    """<summary>MCP server configuration stored in cache.</summary>"""

    id: str
    name: str
    transport_type: str
    command: str | None
    args: list[str] | None
    url: str | None
    headers: dict[str, str] | None
    env: dict[str, str] | None
    enabled: bool
    status: str
    error: str | None
    created_at: str
    updated_at: str | None
    metadata: dict[str, object] | None
    resources: list[dict[str, object]] | None


class McpServerConfigService:
    """<summary>Service for managing MCP server configs in cache.</summary>"""

    _INDEX_KEY = "mcp_servers:index"

    def __init__(self, cache: Cache) -> None:
        """<summary>Initialize MCP server config service.</summary>"""
        self._cache = cache

    def _server_key(self, api_key: str, name: str) -> str:
        """<summary>Build cache key for an MCP server scoped to API key.</summary>"""
        return f"mcp_server:{api_key}:{name}"

    def _index_key(self, api_key: str) -> str:
        """<summary>Build cache key for API key's server index.</summary>"""
        return f"mcp_servers:index:{api_key}"

    async def list_servers(self) -> list[McpServerRecord]:
        """<summary>List all MCP servers (legacy, not API-key scoped).</summary>"""
        names = await self._cache.set_members(self._INDEX_KEY)
        if not names:
            return []

        keys = [f"mcp_server:{name}" for name in names]
        raw_servers = await self._cache.get_many_json(keys)
        servers: list[McpServerRecord] = []

        for name, raw in zip(names, raw_servers, strict=True):
            if raw is None:
                await self._cache.remove_from_set(self._INDEX_KEY, name)
                continue
            servers.append(self._map_record(name, raw))

        return servers

    async def list_servers_for_api_key(self, api_key: str) -> list[McpServerRecord]:
        """<summary>List all MCP servers for a specific API key.</summary>"""
        index_key = self._index_key(api_key)
        names = await self._cache.set_members(index_key)
        if not names:
            return []

        keys = [self._server_key(api_key, name) for name in names]
        raw_servers = await self._cache.get_many_json(keys)
        servers: list[McpServerRecord] = []

        for name, raw in zip(names, raw_servers, strict=True):
            if raw is None:
                await self._cache.remove_from_set(index_key, name)
                continue
            servers.append(self._map_record(name, raw))

        return servers

    async def create_server(
        self,
        name: str,
        transport_type: str,
        config: dict[str, object],
    ) -> McpServerRecord | None:
        """<summary>Create a new MCP server config.</summary>"""
        existing = await self.get_server(name)
        if existing is not None:
            return None

        now = datetime.now(UTC).isoformat()
        record = McpServerRecord(
            id=str(uuid4()),
            name=name,
            transport_type=transport_type,
            command=cast("str | None", config.get("command")),
            args=list(cast("list[str]", config.get("args", [])))
            if config.get("args") is not None
            else None,
            url=cast("str | None", config.get("url")),
            headers=cast("dict[str, str] | None", config.get("headers")),
            env=cast("dict[str, str] | None", config.get("env")),
            enabled=bool(config.get("enabled", True)),
            status=str(config.get("status", "active")),
            error=cast("str | None", config.get("error")),
            created_at=now,
            updated_at=None,
            metadata=cast("dict[str, Any] | None", config.get("metadata")),
            resources=list(cast("list[dict[str, Any]]", config.get("resources", [])))
            if config.get("resources")
            else [],
        )

        await self._cache.set_json(f"mcp_server:{name}", record.__dict__)
        await self._cache.add_to_set(self._INDEX_KEY, name)
        return record

    async def get_server(self, name: str) -> McpServerRecord | None:
        """<summary>Get MCP server config by name (legacy, not API-key scoped).</summary>"""
        raw = await self._cache.get_json(f"mcp_server:{name}")
        if raw is None:
            return None
        return self._map_record(name, cast("dict[str, Any]", raw))

    async def update_server(
        self,
        name: str,
        transport_type: str | None,
        config: dict[str, object] | None,
    ) -> McpServerRecord | None:
        """<summary>Update MCP server config.</summary>"""
        existing = await self.get_server(name)
        if existing is None:
            return None

        next_config = config or {}
        record = McpServerRecord(
            id=existing.id,
            name=existing.name,
            transport_type=transport_type or existing.transport_type,
            command=cast("str | None", next_config.get("command", existing.command)),
            args=cast("list[str] | None", next_config.get("args", existing.args)),
            url=cast("str | None", next_config.get("url", existing.url)),
            headers=cast(
                "dict[str, str] | None", next_config.get("headers", existing.headers)
            ),
            env=cast("dict[str, str] | None", next_config.get("env", existing.env)),
            enabled=bool(next_config.get("enabled", existing.enabled)),
            status=str(next_config.get("status", existing.status)),
            error=cast("str | None", next_config.get("error", existing.error)),
            created_at=existing.created_at,
            updated_at=datetime.now(UTC).isoformat(),
            metadata=cast(
                "dict[str, Any] | None", next_config.get("metadata", existing.metadata)
            ),
            resources=cast(
                "list[dict[str, Any]] | None",
                next_config.get("resources", existing.resources),
            ),
        )

        await self._cache.set_json(f"mcp_server:{name}", record.__dict__)
        return record

    async def delete_server(self, name: str) -> bool:
        """<summary>Delete MCP server config (legacy, not API-key scoped).</summary>"""
        await self._cache.remove_from_set(self._INDEX_KEY, name)
        return await self._cache.delete(f"mcp_server:{name}")

    async def create_server_for_api_key(
        self,
        api_key: str,
        name: str,
        transport_type: str,
        config: dict[str, object],
    ) -> McpServerRecord | None:
        """<summary>Create a new MCP server config for specific API key.</summary>"""
        existing = await self.get_server_for_api_key(api_key, name)
        if existing is not None:
            return None

        now = datetime.now(UTC).isoformat()
        record = McpServerRecord(
            id=str(uuid4()),
            name=name,
            transport_type=transport_type,
            command=cast("str | None", config.get("command")),
            args=list(cast("list[str]", config.get("args", [])))
            if config.get("args") is not None
            else None,
            url=cast("str | None", config.get("url")),
            headers=cast("dict[str, str] | None", config.get("headers")),
            env=cast("dict[str, str] | None", config.get("env")),
            enabled=bool(config.get("enabled", True)),
            status=str(config.get("status", "active")),
            error=cast("str | None", config.get("error")),
            created_at=now,
            updated_at=None,
            metadata=cast("dict[str, object] | None", config.get("metadata")),
            resources=list(cast("list[dict[str, object]]", config.get("resources", [])))
            if config.get("resources")
            else [],
        )

        await self._cache.set_json(self._server_key(api_key, name), record.__dict__)
        await self._cache.add_to_set(self._index_key(api_key), name)
        return record

    async def get_server_for_api_key(
        self, api_key: str, name: str
    ) -> McpServerRecord | None:
        """<summary>Get MCP server config by API key and name.</summary>"""
        raw = await self._cache.get_json(self._server_key(api_key, name))
        if raw is None:
            return None
        return self._map_record(name, cast("dict[str, object]", raw))

    async def update_server_for_api_key(
        self,
        api_key: str,
        name: str,
        transport_type: str | None,
        config: dict[str, object] | None,
    ) -> McpServerRecord | None:
        """<summary>Update MCP server config for specific API key.</summary>"""
        existing = await self.get_server_for_api_key(api_key, name)
        if existing is None:
            return None

        next_config = config or {}
        record = McpServerRecord(
            id=existing.id,
            name=existing.name,
            transport_type=transport_type or existing.transport_type,
            command=cast("str | None", next_config.get("command", existing.command)),
            args=cast("list[str] | None", next_config.get("args", existing.args)),
            url=cast("str | None", next_config.get("url", existing.url)),
            headers=cast(
                "dict[str, str] | None", next_config.get("headers", existing.headers)
            ),
            env=cast("dict[str, str] | None", next_config.get("env", existing.env)),
            enabled=bool(next_config.get("enabled", existing.enabled)),
            status=str(next_config.get("status", existing.status)),
            error=cast("str | None", next_config.get("error", existing.error)),
            created_at=existing.created_at,
            updated_at=datetime.now(UTC).isoformat(),
            metadata=cast(
                "dict[str, object] | None",
                next_config.get("metadata", existing.metadata),
            ),
            resources=cast(
                "list[dict[str, object]] | None",
                next_config.get("resources", existing.resources),
            ),
        )

        await self._cache.set_json(self._server_key(api_key, name), record.__dict__)
        return record

    async def delete_server_for_api_key(self, api_key: str, name: str) -> bool:
        """<summary>Delete MCP server config for specific API key.</summary>"""
        await self._cache.remove_from_set(self._index_key(api_key), name)
        return await self._cache.delete(self._server_key(api_key, name))

    def _map_record(self, name: str, raw: dict[str, Any]) -> McpServerRecord:
        """<summary>Map cached data to MCP server record.</summary>"""
        return McpServerRecord(
            id=str(raw.get("id", "")),
            name=str(raw.get("name", name)),
            transport_type=str(raw.get("transport_type", raw.get("type", ""))),
            command=cast("str | None", raw.get("command")),
            args=list(cast("list[str]", raw.get("args", [])))
            if raw.get("args") is not None
            else None,
            url=cast("str | None", raw.get("url")),
            headers=cast("dict[str, str] | None", raw.get("headers")),
            env=cast("dict[str, str] | None", raw.get("env")),
            enabled=bool(raw.get("enabled", True)),
            status=str(raw.get("status", "active")),
            error=cast("str | None", raw.get("error")),
            created_at=str(raw.get("created_at", "")),
            updated_at=cast("str | None", raw.get("updated_at")),
            metadata=cast("dict[str, Any] | None", raw.get("metadata")),
            resources=list(cast("list[dict[str, Any]]", raw.get("resources", [])))
            if raw.get("resources")
            else [],
        )
