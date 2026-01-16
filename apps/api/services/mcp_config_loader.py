"""Application-level MCP server configuration loader.

Loads server-side MCP server configuration from .mcp-server-config.json
in the project root directory.
"""

import json
import os
import re
from pathlib import Path
from typing import cast

import structlog

logger = structlog.get_logger(__name__)

# Pattern to match environment variable placeholders like ${VAR_NAME}
ENV_VAR_PATTERN = re.compile(r"\$\{([A-Z_][A-Z0-9_]*)\}")

# JSON field name for MCP servers section
MCP_SERVERS_FIELD = "mcpServers"


class McpConfigLoader:
    """Service for loading application-level MCP server configuration."""

    def __init__(self, project_path: Path | str | None = None) -> None:
        """Initialize MCP config loader.

        Args:
            project_path: Path to project root (defaults to cwd).
        """
        self.project_path = Path(project_path) if project_path else Path.cwd()
        # Cache for loaded config (single instance per loader)
        self._cached_config: dict[str, object] | None = None

    def load_application_config(self) -> dict[str, object]:
        """Load application-level MCP server configuration.

        Reads .mcp-server-config.json from project root and returns the
        mcpServers section. If file is missing or invalid, returns empty dict
        and logs a warning.

        Results are cached per loader instance to avoid repeated file I/O.

        Returns:
            Dict mapping server name to server configuration dict.
            Empty dict if file missing or invalid.
        """
        # Return cached config if available
        if self._cached_config is not None:
            logger.debug(
                "application_mcp_config_cached",
                server_count=len(self._cached_config),
            )
            return self._cached_config

        config_path = self.project_path / ".mcp-server-config.json"

        # Handle missing file
        if not config_path.exists():
            logger.debug(
                "application_mcp_config_not_found",
                path=str(config_path),
            )
            self._cached_config = {}
            return self._cached_config

        # Load and parse config file
        mcp_servers = self._load_and_parse_file(config_path)
        self._cached_config = mcp_servers
        return self._cached_config

    def _load_and_parse_file(self, config_path: Path) -> dict[str, object]:
        """Load and parse MCP configuration file.

        Args:
            config_path: Path to the configuration JSON file.

        Returns:
            Parsed mcpServers section, or empty dict on error.
        """
        try:
            content = config_path.read_text(encoding="utf-8")
            config = json.loads(content)

            # Extract and validate mcpServers section
            mcp_servers = config.get(MCP_SERVERS_FIELD, {})

            if not self._validate_config_structure(mcp_servers, config_path):
                return {}

            logger.info(
                "application_mcp_config_loaded",
                path=str(config_path),
                server_count=len(mcp_servers),
                servers=list(mcp_servers.keys()),
            )

            return mcp_servers

        except OSError as e:
            # File read errors (permissions, I/O issues)
            logger.warning(
                "application_mcp_config_read_failed",
                path=str(config_path),
                error=str(e),
                error_type=type(e).__name__,
            )
            return {}

        except json.JSONDecodeError as e:
            # JSON parsing errors (malformed JSON)
            logger.warning(
                "application_mcp_config_parse_failed",
                path=str(config_path),
                error=str(e),
                line=e.lineno,
                column=e.colno,
            )
            return {}

    def _validate_config_structure(
        self, mcp_servers: object, config_path: Path
    ) -> bool:
        """Validate that mcpServers section has correct structure.

        Args:
            mcp_servers: The extracted mcpServers value to validate.
            config_path: Path to config file (for logging).

        Returns:
            True if valid (is a dict), False otherwise.
        """
        if not isinstance(mcp_servers, dict):
            logger.warning(
                "application_mcp_config_invalid",
                path=str(config_path),
                reason="mcpServers_not_dict",
                actual_type=type(mcp_servers).__name__,
            )
            return False
        return True

    def resolve_env_vars(self, config: dict[str, object]) -> dict[str, object]:
        """Resolve environment variable placeholders in configuration.

        Recursively processes the configuration dict and replaces placeholders
        like ${VAR_NAME} with actual environment variable values. If a variable
        is not found in the environment, the placeholder is left as-is and a
        warning is logged.

        Environment variable names must match pattern: ${[A-Z_][A-Z0-9_]*}
        (uppercase letters, underscores, numbers, cannot start with digit).

        Args:
            config: Configuration dict that may contain ${VAR} placeholders.

        Returns:
            Configuration dict with environment variables resolved.

        Example:
            >>> loader = McpConfigLoader()
            >>> config = {"token": "${GITHUB_TOKEN}", "count": 42}
            >>> loader.resolve_env_vars(config)
            {"token": "ghp_actual_token_value", "count": 42}
        """
        resolved = self._resolve_value(config)
        # Type checker needs explicit cast since _resolve_value returns object
        return cast("dict[str, object]", resolved)

    def _resolve_value(self, value: object) -> object:
        """Recursively resolve environment variables in a value.

        Handles different value types:
        - str: Searches for ${VAR} patterns and replaces with env values
        - dict: Recursively processes all values
        - list: Recursively processes all items
        - other: Returns unchanged (int, bool, None, etc.)

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
            # Primitive types (int, bool, None) pass through unchanged
            return value

    def _resolve_string(self, text: str) -> str:
        """Resolve environment variables in a string.

        Replaces all occurrences of ${VAR_NAME} with environment variable values.
        Multiple placeholders in one string are all resolved. If a variable is
        not found, the placeholder is left unchanged and a warning is logged.

        Args:
            text: String that may contain ${VAR} placeholders.

        Returns:
            String with environment variables replaced.

        Example:
            >>> # With GITHUB_TOKEN=secret in environment
            >>> loader._resolve_string("Bearer ${GITHUB_TOKEN}")
            "Bearer secret"
        """

        def replace_var(match: re.Match[str]) -> str:
            """Replace a single environment variable placeholder.

            Args:
                match: Regex match object for ${VAR_NAME} pattern.

            Returns:
                Environment variable value or original placeholder if not found.
            """
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

    def merge_configs(
        self,
        application_config: dict[str, object],
        api_key_config: dict[str, object],
        request_config: dict[str, object] | None,
    ) -> dict[str, object]:
        """Merge three-tier MCP server configuration with precedence rules.

        Implements three-tier merge with precedence (lowest to highest):
        Application (file) < API-Key (database) < Request (API call)

        **Precedence Rules:**
        1. Request config (if provided) COMPLETELY REPLACES all server-side configs
        2. API-key config merges with application config (api-key wins conflicts)
        3. Empty request dict {} explicitly opts out (disables all servers)
        4. Null request uses server-side configs (application + api-key merge)

        **Replacement Semantics:**
        Same-name servers from higher tier replace lower tier completely
        (NOT deep merge - entire server config is replaced).

        Args:
            application_config: Application-level config from .mcp-server-config.json.
            api_key_config: API-key-level config from Redis database.
            request_config: Request-level config from API request (optional).
                - None = use server-side configs
                - {} = explicit opt-out (no servers)
                - {...} = use only request config (ignore server-side)

        Returns:
            Merged configuration dict mapping server name to server config.

        Example:
            >>> loader = McpConfigLoader()
            >>> app = {"github": {"command": "mcp-github"}}
            >>> key = {"slack": {"url": "http://slack"}}
            >>> req = None  # Use server-side
            >>> loader.merge_configs(app, key, req)
            {"github": {"command": "mcp-github"}, "slack": {"url": "http://slack"}}
            >>> req = {"custom": {"command": "mcp-custom"}}  # Replaces all
            >>> loader.merge_configs(app, key, req)
            {"custom": {"command": "mcp-custom"}}
        """
        # Handle explicit opt-out: empty dict means "disable all MCP servers"
        if self._is_opt_out(request_config):
            return {}

        # Request config present (non-empty): completely replaces server-side configs
        # This is the HIGHEST precedence tier
        if request_config is not None:
            logger.debug(
                "mcp_config_request_override",
                request_count=len(request_config),
            )
            return dict(request_config)

        # No request config: merge server-side tiers
        # Precedence: application (base) < api_key (override)
        merged = {**application_config, **api_key_config}

        logger.debug(
            "mcp_config_merged",
            application_count=len(application_config),
            api_key_count=len(api_key_config),
            merged_count=len(merged),
        )

        return merged

    def _is_opt_out(self, request_config: dict[str, object] | None) -> bool:
        """Check if request config is an explicit opt-out.

        Args:
            request_config: Request-level config (optional).

        Returns:
            True if empty dict (opt-out), False otherwise.
        """
        if request_config is not None and len(request_config) == 0:
            logger.debug(
                "mcp_config_opt_out",
                reason="request_empty_dict",
            )
            return True
        return False
