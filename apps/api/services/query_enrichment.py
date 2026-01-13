"""Query enrichment service for auto-injecting MCP servers and skills.

Discovers MCP servers and skills from filesystem:
- MCP servers: ~/.claude.json, .mcp.json, .claude/mcp.json
- Skills: .claude/skills/*.md
"""

from pathlib import Path

import structlog

from apps.api.schemas.requests.config import McpServerConfigSchema
from apps.api.schemas.requests.query import QueryRequest
from apps.api.services.mcp_discovery import McpDiscoveryService, McpServerInfo
from apps.api.services.skills import SkillInfo, SkillsService

logger = structlog.get_logger(__name__)


class QueryEnrichmentService:
    """Service to enrich query requests with configured MCP servers and skills.

    This service auto-injects enabled MCP servers and skills from the filesystem
    into query requests, allowing users to configure them once and have them
    automatically available in all agent sessions.

    Configuration sources:
    - MCP servers: ~/.claude.json (global), .mcp.json, .claude/mcp.json (project)
    - Skills: .claude/skills/*.md with YAML frontmatter
    """

    def __init__(
        self,
        project_path: Path | str | None = None,
        disabled_mcp_servers: list[str] | None = None,
    ) -> None:
        """Initialize enrichment service.

        Args:
            project_path: Path to project root (defaults to cwd).
            disabled_mcp_servers: List of MCP server names to exclude.
        """
        self._project_path = Path(project_path) if project_path else Path.cwd()
        self._disabled_mcp_servers = disabled_mcp_servers or []
        self._mcp_discovery = McpDiscoveryService(project_path=self._project_path)
        self._skills_service = SkillsService(project_path=self._project_path)

    def enrich_query(self, query: QueryRequest) -> QueryRequest:
        """Enrich a query request with configured MCP servers and skills.

        Merges filesystem-configured MCP servers with any servers specified
        in the request. Request-specified servers take precedence in case
        of name conflicts.

        Args:
            query: Original query request.

        Returns:
            Enriched query request with auto-injected configs.
        """
        # Load configured MCP servers from filesystem
        configured_mcp = self._load_mcp_servers()

        # Merge MCP servers (request takes precedence)
        merged_mcp = self._merge_mcp_servers(query, configured_mcp)

        # Only create a new query if we have configs to add
        if merged_mcp and merged_mcp != query.mcp_servers:
            # Create a copy with merged MCP servers
            # Use model_copy to preserve all other fields
            enriched = query.model_copy(update={"mcp_servers": merged_mcp})
            logger.debug(
                "query_enriched",
                mcp_servers_added=len(merged_mcp) - len(query.mcp_servers or {}),
                total_mcp_servers=len(merged_mcp),
            )
            return enriched

        return query

    def _load_mcp_servers(self) -> dict[str, McpServerConfigSchema]:
        """Load enabled MCP servers from filesystem configs.

        Returns:
            Dict mapping server name to config schema.
        """
        try:
            servers = self._mcp_discovery.get_enabled_servers(
                disabled_servers=self._disabled_mcp_servers
            )
            result: dict[str, McpServerConfigSchema] = {}

            for name, server in servers.items():
                config = self._convert_mcp_info_to_schema(server)
                if config:
                    result[name] = config

            logger.debug(
                "mcp_servers_loaded_from_filesystem",
                count=len(result),
                servers=list(result.keys()),
            )
            return result

        except Exception as e:
            logger.warning(
                "mcp_servers_load_failed",
                error=str(e),
                error_type=type(e).__name__,
            )
            return {}

    def _convert_mcp_info_to_schema(
        self, info: McpServerInfo
    ) -> McpServerConfigSchema | None:
        """Convert McpServerInfo to McpServerConfigSchema.

        Args:
            info: MCP server info from discovery.

        Returns:
            Schema for query request, or None if invalid.
        """
        try:
            # Get type and validate it's a valid literal
            server_type = info.get("type", "stdio")
            if server_type not in ("stdio", "sse", "http"):
                server_type = "stdio"

            return McpServerConfigSchema(
                command=info.get("command"),
                args=info.get("args", []),
                type=server_type,
                url=info.get("url"),
                headers=info.get("headers", {}),
                env=info.get("env", {}),
            )
        except Exception as e:
            logger.warning(
                "mcp_server_schema_conversion_failed",
                server=info.get("name"),
                error=str(e),
            )
            return None

    def _merge_mcp_servers(
        self,
        query: QueryRequest,
        configured: dict[str, McpServerConfigSchema],
    ) -> dict[str, McpServerConfigSchema] | None:
        """Merge configured MCP servers with request servers.

        Request-specified servers take precedence over configured ones.

        Args:
            query: Original query request.
            configured: Filesystem-configured MCP servers.

        Returns:
            Merged MCP servers dict, or None if empty.
        """
        if not configured and not query.mcp_servers:
            return None

        # Start with configured servers
        merged = dict(configured)

        # Override with request-specified servers
        if query.mcp_servers:
            merged.update(query.mcp_servers)

        return merged if merged else None

    def get_available_skills(self) -> list[SkillInfo]:
        """Get all available skills from filesystem.

        Returns:
            List of skill info dicts.
        """
        return self._skills_service.discover_skills()

    def get_available_mcp_servers(self) -> dict[str, McpServerInfo]:
        """Get all available MCP servers from filesystem.

        Returns:
            Dict mapping server name to config.
        """
        return self._mcp_discovery.get_enabled_servers(
            disabled_servers=self._disabled_mcp_servers
        )
