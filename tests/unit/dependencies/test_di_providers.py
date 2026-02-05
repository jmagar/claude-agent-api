"""Unit tests for DI providers (TDD approach).

This module tests that all DI provider functions exist and work correctly.
Phase 2 of the DI refactor plan.
"""

import pytest
from unittest.mock import AsyncMock

from apps.api.adapters.cache import RedisCache

pytestmark = pytest.mark.anyio


class TestDIProviders:
    """🔴 RED → 🟢 GREEN: Provider existence and basic functionality tests."""

    async def test_get_agent_config_service_exists(self) -> None:
        """get_agent_config_service provider exists and is callable."""
        from apps.api.dependencies import get_agent_config_service

        # Provider should be an async function
        assert callable(get_agent_config_service)

    async def test_get_agent_config_service_returns_service(
        self, cache: RedisCache
    ) -> None:
        """Agent config service provider returns correct type."""
        from apps.api.dependencies import get_agent_config_service

        service = await get_agent_config_service(cache)
        assert service is not None
        # Verify it has the expected methods
        assert hasattr(service, "list_agents")
        assert hasattr(service, "create_agent")

    async def test_get_project_service_exists(self) -> None:
        """get_project_service provider exists."""
        from apps.api.dependencies import get_project_service

        assert callable(get_project_service)

    async def test_get_project_service_injects_cache(self, cache: RedisCache) -> None:
        """Project service provider injects cache dependency."""
        from apps.api.dependencies import get_project_service

        service = await get_project_service(cache)
        assert service._cache is cache

    async def test_get_tool_preset_service_exists(self) -> None:
        """get_tool_preset_service provider exists."""
        from apps.api.dependencies import get_tool_preset_service

        assert callable(get_tool_preset_service)

    async def test_get_tool_preset_service_is_per_request(
        self, cache: RedisCache
    ) -> None:
        """Tool preset service creates new instance per request."""
        from apps.api.dependencies import get_tool_preset_service

        service1 = await get_tool_preset_service(cache)
        service2 = await get_tool_preset_service(cache)
        # Different instances (not singleton)
        assert service1 is not service2

    async def test_get_slash_command_service_exists(self) -> None:
        """get_slash_command_service provider exists."""
        from apps.api.dependencies import get_slash_command_service

        assert callable(get_slash_command_service)

    async def test_get_mcp_server_config_service_exists(self) -> None:
        """get_mcp_server_config_service_provider exists."""
        from apps.api.dependencies import get_mcp_server_config_service_provider

        assert callable(get_mcp_server_config_service_provider)

    async def test_get_mcp_discovery_service_exists(self) -> None:
        """get_mcp_discovery_service provider exists."""
        from apps.api.dependencies import get_mcp_discovery_service

        # Synchronous provider (no cache needed)
        assert callable(get_mcp_discovery_service)

    async def test_get_mcp_discovery_service_uses_cwd(self) -> None:
        """MCP discovery service uses current working directory."""
        from pathlib import Path

        from apps.api.dependencies import get_mcp_discovery_service

        service = get_mcp_discovery_service()
        # Verify project_path is Path.cwd()
        assert service.project_path == Path.cwd()


class TestProtocolCompliance:
    """🟢 GREEN: Protocol compliance tests (services implement protocols)."""

    async def test_agent_service_implements_protocol(self, cache: RedisCache) -> None:
        """AgentService (CRUD) implements AgentConfigProtocol."""
        from apps.api.protocols import AgentConfigProtocol
        from apps.api.services.agents import AgentService

        service = AgentService(cache)
        assert isinstance(service, AgentConfigProtocol)

    async def test_project_service_implements_protocol(self, cache: RedisCache) -> None:
        """ProjectService implements ProjectProtocol."""
        from apps.api.protocols import ProjectProtocol
        from apps.api.services.projects import ProjectService

        service = ProjectService(cache)
        assert isinstance(service, ProjectProtocol)

    async def test_tool_preset_service_implements_protocol(
        self, cache: RedisCache
    ) -> None:
        """ToolPresetService implements ToolPresetProtocol."""
        from apps.api.protocols import ToolPresetProtocol
        from apps.api.services.tool_presets import ToolPresetService

        service = ToolPresetService(cache)
        assert isinstance(service, ToolPresetProtocol)

    async def test_slash_command_service_implements_protocol(
        self, cache: RedisCache
    ) -> None:
        """SlashCommandService implements SlashCommandProtocol."""
        from apps.api.protocols import SlashCommandProtocol
        from apps.api.services.slash_commands import SlashCommandService

        service = SlashCommandService(cache)
        assert isinstance(service, SlashCommandProtocol)

    async def test_mcp_server_config_service_implements_protocol(
        self, cache: RedisCache
    ) -> None:
        """McpServerConfigService implements McpServerConfigProtocol."""
        from apps.api.protocols import McpServerConfigProtocol
        from apps.api.services.mcp_server_configs import McpServerConfigService

        service = McpServerConfigService(cache)
        assert isinstance(service, McpServerConfigProtocol)

    async def test_mcp_discovery_service_implements_protocol(self) -> None:
        """McpDiscoveryService implements McpDiscoveryProtocol."""
        from apps.api.protocols import McpDiscoveryProtocol
        from apps.api.services.mcp_discovery import McpDiscoveryService

        service = McpDiscoveryService()
        assert isinstance(service, McpDiscoveryProtocol)

    async def test_skills_service_implements_protocol(self) -> None:
        """SkillsService implements SkillsProtocol."""
        from apps.api.protocols import SkillsProtocol
        from apps.api.services.skills import SkillsService

        service = SkillsService()
        assert isinstance(service, SkillsProtocol)


class TestTypeAliases:
    """🟢 GREEN: Type alias existence tests."""

    def test_agent_config_svc_alias_exists(self) -> None:
        """AgentConfigSvc type alias exists."""
        from apps.api.dependencies import AgentConfigSvc

        # Type alias should be importable
        assert AgentConfigSvc is not None

    def test_project_svc_alias_exists(self) -> None:
        """ProjectSvc type alias exists."""
        from apps.api.dependencies import ProjectSvc

        assert ProjectSvc is not None

    def test_tool_preset_svc_alias_exists(self) -> None:
        """ToolPresetSvc type alias exists."""
        from apps.api.dependencies import ToolPresetSvc

        assert ToolPresetSvc is not None

    def test_slash_command_svc_alias_exists(self) -> None:
        """SlashCommandSvc type alias exists."""
        from apps.api.dependencies import SlashCommandSvc

        assert SlashCommandSvc is not None

    def test_mcp_server_config_svc_alias_exists(self) -> None:
        """McpServerConfigSvc type alias exists."""
        from apps.api.dependencies import McpServerConfigSvc

        assert McpServerConfigSvc is not None

    def test_mcp_discovery_svc_alias_exists(self) -> None:
        """McpDiscoverySvc type alias exists."""
        from apps.api.dependencies import McpDiscoverySvc

        assert McpDiscoverySvc is not None


@pytest.fixture
def cache() -> RedisCache:
    """Mock cache for DI provider tests."""
    mock_cache = AsyncMock(spec=RedisCache)
    return mock_cache
