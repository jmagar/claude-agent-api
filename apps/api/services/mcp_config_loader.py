"""Application-level MCP server configuration loader.

Loads server-side MCP server configuration from .mcp-server-config.json
in the project root directory.
"""

import json
import os
import re
from pathlib import Path

import structlog

logger = structlog.get_logger(__name__)

# Pattern to match environment variable placeholders like ${VAR_NAME}
ENV_VAR_PATTERN = re.compile(r"\$\{([A-Z_][A-Z0-9_]*)\}")


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

    def resolve_env_vars(self, config: dict[str, object]) -> dict[str, object]:
        """Resolve environment variable placeholders in configuration.

        Recursively processes the configuration dict and replaces placeholders
        like ${VAR_NAME} with actual environment variable values. If a variable
        is not found in the environment, the placeholder is left as-is and a
        warning is logged.

        Args:
            config: Configuration dict that may contain ${VAR} placeholders.

        Returns:
            Configuration dict with environment variables resolved.
        """
        return self._resolve_value(config)  # type: ignore[return-value]

    def _resolve_value(self, value: object) -> object:
        """Recursively resolve environment variables in a value.

        Args:
            value: Any value that might contain env var placeholders.

        Returns:
            Value with placeholders resolved.
        """
        if isinstance(value, str):
            return self._resolve_string(value)
        elif isinstance(value, dict):
            return {k: self._resolve_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._resolve_value(item) for item in value]
        else:
            return value

    def _resolve_string(self, text: str) -> str:
        """Resolve environment variables in a string.

        Args:
            text: String that may contain ${VAR} placeholders.

        Returns:
            String with environment variables replaced.
        """

        def replace_var(match: re.Match[str]) -> str:
            var_name = match.group(1)
            env_value = os.environ.get(var_name)

            if env_value is None:
                logger.warning(
                    "env_var_not_found",
                    var_name=var_name,
                    placeholder=match.group(0),
                )
                return match.group(0)  # Return original placeholder

            logger.debug(
                "env_var_resolved",
                var_name=var_name,
            )
            return env_value

        return ENV_VAR_PATTERN.sub(replace_var, text)
