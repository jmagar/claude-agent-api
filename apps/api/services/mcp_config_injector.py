"""MCP configuration injector service.

Coordinates loading and merging of MCP server configurations from three tiers:
1. Application-level (from .mcp-server-config.json file)
2. API-key-level (from Redis database)
3. Request-level (from QueryRequest.mcp_servers field)

Enriches QueryRequest with merged server-side MCP configurations.
"""

from collections.abc import Sequence
from typing import cast

import structlog

from apps.api.schemas.requests.config import McpServerConfigSchema
from apps.api.schemas.requests.query import QueryRequest
from apps.api.services.mcp_config_loader import McpConfigLoader
from apps.api.services.mcp_config_validator import ConfigValidator
from apps.api.services.mcp_server_configs import McpServerConfigService, McpServerRecord

logger = structlog.get_logger(__name__)


class McpConfigInjector:
    """Service for injecting server-side MCP configuration into requests."""

    def __init__(
        self,
        config_loader: McpConfigLoader,
        config_service: McpServerConfigService,
        validator: ConfigValidator | None = None,
    ) -> None:
        """Initialize MCP config injector.

        Args:
            config_loader: Loader for application-level config files.
            config_service: Service for API-key-scoped config storage.
            validator: Optional validator for security checks and credential sanitization.
        """
        self.config_loader = config_loader
        self.config_service = config_service
        self.validator = validator

    async def inject(self, request: QueryRequest, api_key: str) -> QueryRequest:
        """Inject server-side MCP configuration into request.

        Loads and merges MCP server configurations from three tiers:
        - Application-level (file): .mcp-server-config.json
        - API-key-level (database): Redis storage
        - Request-level (existing): request.mcp_servers field

        Precedence: Application < API-Key < Request (lowest to highest).

        Special handling for opt-out:
        - If request.mcp_servers == {} (empty dict), returns unchanged (explicit opt-out).
        - If request.mcp_servers is None, merges application + API-key configs.
        - If request.mcp_servers has values, merges all three tiers.

        Graceful degradation:
        - If any error occurs during injection, logs error and returns original request.
        - This ensures MCP config issues don't block query execution.

        Args:
            request: Query request to enrich with server-side MCP configs.
            api_key: API key for scoped configuration lookup.

        Returns:
            Enriched query request with merged MCP server configurations,
            or original request if injection fails.
        """
        # Handle explicit opt-out (empty dict means "no MCP servers")
        if request.mcp_servers is not None and len(request.mcp_servers) == 0:
            logger.debug(
                "mcp_config_inject_skipped",
                reason="explicit_opt_out",
                api_key_prefix=api_key[:8] if len(api_key) >= 8 else api_key,
            )
            return request

        try:
            # Load application-level config from file
            app_config_raw = self.config_loader.load_application_config()
            app_config_resolved = self.config_loader.resolve_env_vars(app_config_raw)

            # Load API-key-level config from database
            api_key_records = await self.config_service.list_servers_for_api_key(
                api_key
            )
            api_key_config = cast(
                "dict[str, object]", self._records_to_config_dict(api_key_records)
            )

            # Convert request mcp_servers to dict format for merging
            request_config_raw = (
                self._schemas_to_config_dict(request.mcp_servers)
                if request.mcp_servers
                else None
            )
            request_config = (
                cast("dict[str, object]", request_config_raw)
                if request_config_raw is not None
                else None
            )

            # Merge configs with correct precedence
            merged_config = self.config_loader.merge_configs(
                application_config=app_config_resolved,
                api_key_config=api_key_config,
                request_config=request_config,
            )

            # Convert merged config back to Pydantic models
            merged_schemas = self._config_dict_to_schemas(merged_config)

            # Sanitize merged config for safe logging (if validator available)
            sanitized_config = (
                self.validator.sanitize_credentials(merged_config)
                if self.validator
                else merged_config
            )

            logger.info(
                "mcp_config_injected",
                api_key_prefix=api_key[:8] if len(api_key) >= 8 else api_key,
                application_count=len(app_config_resolved),
                api_key_count=len(api_key_config),
                request_count=len(request_config) if request_config else 0,
                merged_count=len(merged_schemas),
                server_names=list(merged_schemas.keys()),
                merged_config=sanitized_config,
            )

            # Build allowed_tools patterns for MCP servers
            # Pattern: mcp__<server-name>__* allows all tools from the server
            mcp_tool_patterns = [f"mcp__{name}__*" for name in merged_schemas.keys()]

            # Merge with existing allowed_tools (preserve user-specified tools)
            existing_allowed = list(request.allowed_tools) if request.allowed_tools else []
            updated_allowed_tools = existing_allowed + mcp_tool_patterns

            logger.info(
                "mcp_tools_added_to_allowed",
                mcp_tool_patterns=mcp_tool_patterns,
                existing_allowed_count=len(existing_allowed),
                updated_allowed_count=len(updated_allowed_tools),
            )

            # Create enriched request with merged MCP servers and updated allowed_tools
            return request.model_copy(
                update={
                    "mcp_servers": merged_schemas,
                    "allowed_tools": updated_allowed_tools,
                }
            )

        except Exception as e:
            # Graceful degradation: log error and return original request
            # This ensures MCP config issues don't block query execution
            logger.error(
                "mcp_config_injection_failed",
                error=str(e),
                error_type=type(e).__name__,
                api_key_prefix=api_key[:8] if len(api_key) >= 8 else api_key,
                exc_info=True,
            )
            return request

    def _records_to_config_dict(
        self, records: Sequence[McpServerRecord]
    ) -> dict[str, dict[str, object]]:
        """Convert McpServerRecord list to config dict format.

        Args:
            records: List of McpServerRecord from database.

        Returns:
            Dict mapping server name to server config dict.
        """
        config_dict: dict[str, dict[str, object]] = {}

        for record in records:
            # Skip disabled servers
            if not record.enabled:
                continue

            server_config: dict[str, object] = {
                "type": record.transport_type,
            }

            # Add stdio transport fields
            if record.command:
                server_config["command"] = record.command
            if record.args:
                server_config["args"] = record.args

            # Add remote transport fields
            if record.url:
                server_config["url"] = record.url
            if record.headers:
                server_config["headers"] = record.headers

            # Add environment
            if record.env:
                server_config["env"] = record.env

            config_dict[record.name] = server_config

        return config_dict

    def _schemas_to_config_dict(
        self, schemas: dict[str, McpServerConfigSchema]
    ) -> dict[str, dict[str, object]]:
        """Convert Pydantic schemas to config dict format.

        Args:
            schemas: Dict mapping server name to McpServerConfigSchema.

        Returns:
            Dict mapping server name to server config dict.
        """
        config_dict: dict[str, dict[str, object]] = {}

        for name, schema in schemas.items():
            config_dict[name] = cast(
                "dict[str, object]", schema.model_dump(exclude_defaults=False)
            )

        return config_dict

    def _config_dict_to_schemas(
        self, config: dict[str, object]
    ) -> dict[str, McpServerConfigSchema]:
        """Convert config dict to Pydantic schemas.

        Args:
            config: Dict mapping server name to server config dict.

        Returns:
            Dict mapping server name to McpServerConfigSchema.
        """
        schemas: dict[str, McpServerConfigSchema] = {}

        for name, server_config in config.items():
            if not isinstance(server_config, dict):
                logger.warning(
                    "mcp_config_invalid_server",
                    server_name=name,
                    reason="not_dict",
                )
                continue

            try:
                schemas[name] = McpServerConfigSchema.model_validate(server_config)
            except Exception as e:
                logger.warning(
                    "mcp_config_validation_failed",
                    server_name=name,
                    error=str(e),
                    error_type=type(e).__name__,
                )
                continue

        return schemas
