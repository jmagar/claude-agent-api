"""Application-level MCP server configuration loader.

Loads server-side MCP server configuration from .mcp-server-config.json
in the project root directory.
"""

import json
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class McpConfigLoader:
    """Service for loading application-level MCP server configuration."""

    def __init__(self, project_path: Path | str | None = None) -> None:
        """Initialize MCP config loader.

        Args:
            project_path: Path to project root (defaults to cwd).
        """
        self.project_path = Path(project_path) if project_path else Path.cwd()

    def load_application_config(self) -> dict[str, object]:
        """Load application-level MCP server configuration.

        Reads .mcp-server-config.json from project root and returns the
        mcpServers section. If file is missing or invalid, returns empty dict
        and logs a warning.

        Returns:
            Dict mapping server name to server configuration dict.
            Empty dict if file missing or invalid.
        """
        config_path = self.project_path / ".mcp-server-config.json"

        if not config_path.exists():
            logger.debug(
                "application_mcp_config_not_found",
                path=str(config_path),
            )
            return {}

        try:
            content = config_path.read_text()
            config = json.loads(content)

            # Extract mcpServers section
            mcp_servers = config.get("mcpServers", {})

            if not isinstance(mcp_servers, dict):
                logger.warning(
                    "application_mcp_config_invalid",
                    path=str(config_path),
                    reason="mcpServers_not_dict",
                )
                return {}

            logger.info(
                "application_mcp_config_loaded",
                path=str(config_path),
                server_count=len(mcp_servers),
                servers=list(mcp_servers.keys()),
            )

            return mcp_servers

        except (OSError, json.JSONDecodeError) as e:
            logger.warning(
                "application_mcp_config_load_failed",
                path=str(config_path),
                error=str(e),
                error_type=type(e).__name__,
            )
            return {}
