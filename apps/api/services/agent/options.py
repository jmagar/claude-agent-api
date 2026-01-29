"""Options builder for Claude Agent SDK.

Extracts options building logic from AgentService for better separation of concerns.
"""

from pathlib import Path
from typing import TYPE_CHECKING, cast

import structlog

if TYPE_CHECKING:
    from claude_agent_sdk import AgentDefinition, ClaudeAgentOptions
    from claude_agent_sdk.types import (
        McpHttpServerConfig,
        McpSdkServerConfig,
        McpSSEServerConfig,
        McpStdioServerConfig,
        SandboxSettings,
        SdkPluginConfig,
        SettingSource,
    )

    from apps.api.schemas.requests.query import QueryRequest

    # Union type for MCP server configs
    McpServerConfig = (
        McpStdioServerConfig
        | McpSSEServerConfig
        | McpHttpServerConfig
        | McpSdkServerConfig
    )

logger = structlog.get_logger(__name__)


class OptionsBuilder:
    """Builds ClaudeAgentOptions from QueryRequest.

    Handles the complex transformation from API request schema to SDK options,
    including conditional building of nested configurations.
    """

    def __init__(self, request: "QueryRequest") -> None:
        """Initialize builder with request.

        Args:
            request: Query request from API.
        """
        self.request = request

    def build(self) -> "ClaudeAgentOptions":
        """Build SDK options from request.

        Returns:
            ClaudeAgentOptions instance.

        Note:
            The SDK has complex nested types that require dynamic construction.
            We use a typed approach with conditional building.
        """
        from claude_agent_sdk import ClaudeAgentOptions

        request = self.request

        # Extract basic options from request
        allowed_tools = request.allowed_tools if request.allowed_tools else None
        disallowed_tools = (
            request.disallowed_tools if request.disallowed_tools else None
        )
        permission_mode = request.permission_mode if request.permission_mode else None
        permission_prompt_tool_name = (
            request.permission_prompt_tool_name
            if request.permission_prompt_tool_name
            else None
        )

        # Session resume configuration
        resume: str | None = None
        fork_session: bool | None = None
        if request.continue_conversation and not request.fork_session:
            resume = None
        elif request.session_id and not request.fork_session:
            resume = request.session_id
        elif request.session_id and request.fork_session:
            resume = request.session_id
            fork_session = True

        # Setting sources for CLAUDE.md loading (T114)
        setting_sources_typed: list[str] | None = None
        if request.setting_sources:
            setting_sources_typed = list(request.setting_sources)
            # Validate that "project" is included for CLAUDE.md loading
            self._validate_setting_sources(setting_sources_typed)

        # Validate Skill tool if present
        self._validate_skill_tool(allowed_tools, request.cwd if request.cwd else None)

        # Build complex configs using helper methods
        mcp_configs = self._build_mcp_configs()
        agent_defs = self._build_agent_defs()
        output_format = self._build_output_format()
        plugins_list = self._build_plugins()
        sandbox_config = self._build_sandbox_config()
        final_system_prompt = self._resolve_system_prompt()

        # DEBUG: Log what MCP configs are being passed to SDK
        logger.debug(
            "Building ClaudeAgentOptions",
            has_mcp_servers=bool(mcp_configs),
            mcp_server_count=len(mcp_configs) if mcp_configs else 0,
            mcp_server_names=list(mcp_configs.keys()) if mcp_configs else [],
            mcp_configs_detail=mcp_configs,
            setting_sources=setting_sources_typed,
        )

        # Note: mcp_servers, agents, plugins, setting_sources, and sandbox are cast
        # because SDK expects specific config types but accepts dict-like structures
        return ClaudeAgentOptions(
            allowed_tools=allowed_tools or [],
            disallowed_tools=disallowed_tools or [],
            permission_mode=permission_mode,
            permission_prompt_tool_name=permission_prompt_tool_name,
            model=request.model if request.model else None,
            max_turns=request.max_turns if request.max_turns else None,
            cwd=request.cwd if request.cwd else None,
            env=request.env or {},
            system_prompt=final_system_prompt,
            enable_file_checkpointing=bool(request.enable_file_checkpointing),
            resume=resume,
            fork_session=fork_session or False,
            mcp_servers=cast("dict[str, McpServerConfig]", mcp_configs or {}),
            agents=cast("dict[str, AgentDefinition] | None", agent_defs),
            output_format=output_format,
            plugins=cast("list[SdkPluginConfig]", plugins_list),
            setting_sources=cast("list[SettingSource] | None", setting_sources_typed),
            sandbox=cast("SandboxSettings | None", sandbox_config),
            include_partial_messages=request.include_partial_messages,
        )

    def _build_mcp_configs(
        self,
    ) -> dict[str, dict[str, str | list[str] | dict[str, str] | None]] | None:
        """Build MCP server configurations from request.

        Returns:
            MCP server configs dict or None.
        """
        if not self.request.mcp_servers:
            return None

        mcp_configs: dict[str, dict[str, str | list[str] | dict[str, str] | None]] = {}
        for name, config in self.request.mcp_servers.items():
            # T140: SEC - Do NOT resolve environment variables from user input
            # This prevents server-side secret leakage through ${VAR} syntax
            mcp_configs[name] = {
                "command": config.command,
                "args": config.args,
                "type": config.type,
                "url": config.url,
                "headers": dict(config.headers) if config.headers else {},
                "env": dict(config.env) if config.env else {},
            }
        return mcp_configs

    def _build_agent_defs(
        self,
    ) -> dict[str, dict[str, str | list[str] | None]] | None:
        """Build agent definitions from request.

        Returns:
            Agent definitions dict or None.
        """
        if not self.request.agents:
            return None

        agent_defs: dict[str, dict[str, str | list[str] | None]] = {}
        for name, agent in self.request.agents.items():
            agent_defs[name] = {
                "description": agent.description,
                "prompt": agent.prompt,
                "tools": agent.tools,
                "model": agent.model,
            }
        return agent_defs

    def _build_output_format(
        self,
    ) -> dict[str, str | dict[str, object] | None] | None:
        """Build output format configuration from request.

        Returns:
            Output format dict or None.
        """
        if not self.request.output_format:
            return None

        return {
            "type": self.request.output_format.type,
            "schema": self.request.output_format.schema_,
        }

    def _build_plugins(self) -> list[dict[str, str | None]]:
        """Build plugins list from request.

        Returns:
            List of plugin config dicts.
        """
        plugins_list: list[dict[str, str | None]] = []
        if self.request.plugins:
            for plugin_config in self.request.plugins:
                if plugin_config.enabled:  # Only include enabled plugins
                    plugins_list.append(
                        {
                            "name": plugin_config.name,
                            "path": plugin_config.path,
                        }
                    )
        return plugins_list

    def _build_sandbox_config(
        self,
    ) -> dict[str, bool | list[str]] | None:
        """Build sandbox configuration from request.

        Returns:
            Sandbox config dict or None.
        """
        if not self.request.sandbox:
            return None

        return {
            "enabled": self.request.sandbox.enabled,
            "allowed_paths": self.request.sandbox.allowed_paths,
            "network_access": self.request.sandbox.network_access,
        }

    def _resolve_system_prompt(self) -> str | None:
        """Resolve system prompt with optional append.

        Combines base system_prompt with system_prompt_append if both provided.

        Returns:
            Resolved system prompt or None.
        """
        system_prompt = (
            self.request.system_prompt if self.request.system_prompt else None
        )

        if self.request.system_prompt_append:
            if system_prompt:
                return f"{system_prompt}\n\n{self.request.system_prompt_append}"
            return self.request.system_prompt_append

        return system_prompt

    def _validate_skill_tool(
        self, allowed_tools: list[str] | None, cwd: str | None
    ) -> None:
        """Validate Skill tool configuration.

        Args:
            allowed_tools: List of allowed tool names
            cwd: Working directory for skill discovery
        """
        if not allowed_tools or "Skill" not in allowed_tools:
            return

        from apps.api.services.skills import SkillsService

        # Check if skills are discoverable
        project_path = Path(cwd) if cwd else Path.cwd()
        skills_service = SkillsService(project_path=project_path)
        discovered_skills = skills_service.discover_skills()

        # Skills will be loaded by SDK if setting_sources includes project/user
        # We just validate that Skill tool is properly configured
        if not discovered_skills:
            # Log warning but don't fail - skills might be in user directory
            logger.warning(
                "skill_tool_enabled_but_no_skills_found",
                project_path=str(project_path),
            )

    def _validate_setting_sources(self, setting_sources: list[str]) -> None:
        """Validate setting_sources configuration.

        Logs a warning if setting_sources is provided but doesn't include "project",
        which is required for loading CLAUDE.md files per SDK documentation.

        Args:
            setting_sources: List of setting source names.
        """
        if "project" not in setting_sources:
            logger.warning(
                "setting_sources_missing_project",
                setting_sources=setting_sources,
                hint="Include 'project' in setting_sources to load CLAUDE.md files",
            )
