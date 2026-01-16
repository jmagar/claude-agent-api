"""Filesystem-based MCP server discovery service.

Discovers MCP servers from:
1. Global config: ~/.claude.json (mcpServers section)
2. Project config: .claude/mcp.json or .mcp.json in project directory
"""

import json
from pathlib import Path
from typing import Any, Literal, TypedDict, cast

import structlog

logger = structlog.get_logger(__name__)


class McpServerInfo(TypedDict, total=False):
    """MCP server configuration from filesystem."""

    name: str
    type: Literal["stdio", "sse", "http"]
    command: str | None
    args: list[str]
    url: str | None
    headers: dict[str, str]
    env: dict[str, str]


class McpDiscoveryService:
    """Service for discovering MCP servers from filesystem configs."""

    def __init__(
        self,
        project_path: Path | str | None = None,
        home_path: Path | str | None = None,
    ) -> None:
        """Initialize MCP discovery service.

        Args:
            project_path: Path to project root (defaults to cwd).
            home_path: Path to home directory (defaults to ~).
        """
        self.project_path = Path(project_path) if project_path else Path.cwd()
        self.home_path = Path(home_path) if home_path else Path.home()

    def discover_servers(self) -> dict[str, McpServerInfo]:
        """Discover all MCP servers from config files.

        Order of precedence (later overrides earlier):
        1. Global ~/.claude.json mcpServers
        2. Project .mcp.json
        3. Project .claude/mcp.json

        Returns:
            Dict mapping server name to config.
        """
        servers: dict[str, McpServerInfo] = {}

        # Load global config
        global_servers = self._load_global_config()
        servers.update(global_servers)

        # Load project configs (override global)
        project_servers = self._load_project_config()
        servers.update(project_servers)

        logger.debug(
            "mcp_servers_discovered",
            global_count=len(global_servers),
            project_count=len(project_servers),
            total_count=len(servers),
            servers=list(servers.keys()),
        )

        return servers

    def _load_global_config(self) -> dict[str, McpServerInfo]:
        """Load MCP servers from global ~/.claude.json.

        Returns:
            Dict mapping server name to config.
        """
        global_config_path = self.home_path / ".claude.json"

        if not global_config_path.exists():
            return {}

        try:
            content = global_config_path.read_text()
            config = json.loads(content)
            raw_servers = config.get("mcpServers", {})

            return self._parse_servers(raw_servers, str(global_config_path))

        except (OSError, json.JSONDecodeError) as e:
            logger.warning(
                "global_mcp_config_load_failed",
                path=str(global_config_path),
                error=str(e),
                error_type=type(e).__name__,
            )
            return {}

    def _load_project_config(self) -> dict[str, McpServerInfo]:
        """Load MCP servers from project config files.

        Checks:
        1. .mcp.json in project root
        2. .claude/mcp.json in project root

        Returns:
            Dict mapping server name to config.
        """
        servers: dict[str, McpServerInfo] = {}

        # Check .mcp.json first
        mcp_json = self.project_path / ".mcp.json"
        if mcp_json.exists():
            project_servers = self._load_mcp_json(mcp_json)
            servers.update(project_servers)

        # Then .claude/mcp.json (overrides .mcp.json)
        claude_mcp_json = self.project_path / ".claude" / "mcp.json"
        if claude_mcp_json.exists():
            claude_servers = self._load_mcp_json(claude_mcp_json)
            servers.update(claude_servers)

        return servers

    def _load_mcp_json(self, path: Path) -> dict[str, McpServerInfo]:
        """Load MCP servers from an mcp.json file.

        Supports both formats:
        1. Direct dict: {"server-name": {...config...}}
        2. Wrapped: {"mcpServers": {"server-name": {...config...}}}

        Args:
            path: Path to mcp.json file.

        Returns:
            Dict mapping server name to config.
        """
        try:
            content = path.read_text()
            config = json.loads(content)

            # Handle wrapped format
            raw_servers = config.get("mcpServers", config)

            return self._parse_servers(raw_servers, str(path))

        except (OSError, json.JSONDecodeError) as e:
            logger.warning(
                "project_mcp_config_load_failed",
                path=str(path),
                error=str(e),
                error_type=type(e).__name__,
            )
            return {}

    def _parse_servers(
        self,
        raw_servers: dict[str, object],
        source: str,
    ) -> dict[str, McpServerInfo]:
        """Parse raw server configs into typed McpServerInfo.

        Args:
            raw_servers: Raw server configs from JSON.
            source: Source file path for logging.

        Returns:
            Dict mapping server name to parsed config.
        """
        servers: dict[str, McpServerInfo] = {}

        for name, raw_config in raw_servers.items():
            if not isinstance(raw_config, dict):
                logger.warning(
                    "mcp_server_config_invalid",
                    server=name,
                    source=source,
                    reason="config_not_dict",
                )
                continue

            try:
                # Cast after isinstance check for type safety
                config = cast("dict[str, Any]", raw_config)

                server_type_raw = config.get("type", "stdio")
                server_type = str(server_type_raw) if server_type_raw else "stdio"
                if server_type not in ("stdio", "sse", "http"):
                    server_type = "stdio"

                command_raw = config.get("command")
                command = str(command_raw) if command_raw else None

                args_raw = config.get("args", [])
                args: list[str] = (
                    [str(a) for a in args_raw] if isinstance(args_raw, list) else []
                )

                url_raw = config.get("url")
                url = str(url_raw) if url_raw else None

                headers_raw = config.get("headers", {})
                headers: dict[str, str] = (
                    {str(k): str(v) for k, v in headers_raw.items()}
                    if isinstance(headers_raw, dict)
                    else {}
                )

                env_raw = config.get("env", {})
                env: dict[str, str] = (
                    {str(k): str(v) for k, v in env_raw.items()}
                    if isinstance(env_raw, dict)
                    else {}
                )

                server: McpServerInfo = {
                    "name": name,
                    "type": server_type,  # type: ignore[typeddict-item]
                    "command": command,
                    "args": args,
                    "url": url,
                    "headers": headers,
                    "env": env,
                }

                servers[name] = server

            except (TypeError, ValueError) as e:
                logger.warning(
                    "mcp_server_parse_failed",
                    server=name,
                    source=source,
                    error=str(e),
                )
                continue

        return servers

    def get_enabled_servers(
        self,
        disabled_servers: list[str] | None = None,
    ) -> dict[str, McpServerInfo]:
        """Get all enabled MCP servers.

        Args:
            disabled_servers: List of server names to exclude.

        Returns:
            Dict mapping server name to config (excluding disabled).
        """
        all_servers = self.discover_servers()
        disabled = set(disabled_servers or [])

        return {
            name: server for name, server in all_servers.items() if name not in disabled
        }
