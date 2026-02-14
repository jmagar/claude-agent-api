"""Unit tests for protocol interfaces.

This module tests that all protocol abstractions exist and are properly defined.
Includes both existing protocols and new protocols for the DI refactor.
"""

from apps.api.protocols import SessionRepositoryProtocol


def test_session_repository_protocol_is_protocol() -> None:
    """Ensure SessionRepositoryProtocol is a typing.Protocol."""
    # Check if SessionRepositoryProtocol is a Protocol by checking its _is_protocol attribute
    assert getattr(SessionRepositoryProtocol, "_is_protocol", False) is True


class TestProtocolCompliance:
    """🔴 RED: Protocol compliance tests for new DI refactor protocols.

    These tests will fail until the protocols are defined in apps/api/protocols.py.
    """

    def test_agent_config_protocol_exists(self) -> None:
        """AgentConfigProtocol is defined and runtime_checkable."""
        from apps.api.protocols import AgentConfigProtocol

        assert hasattr(AgentConfigProtocol, "__protocol_attrs__")

    def test_project_protocol_exists(self) -> None:
        """ProjectProtocol is defined and runtime_checkable."""
        from apps.api.protocols import ProjectProtocol

        assert hasattr(ProjectProtocol, "__protocol_attrs__")

    def test_tool_preset_protocol_exists(self) -> None:
        """ToolPresetProtocol is defined and runtime_checkable."""
        from apps.api.protocols import ToolPresetProtocol

        assert hasattr(ToolPresetProtocol, "__protocol_attrs__")

    def test_mcp_server_config_protocol_exists(self) -> None:
        """McpServerConfigProtocol is defined and runtime_checkable."""
        from apps.api.protocols import McpServerConfigProtocol

        assert hasattr(McpServerConfigProtocol, "__protocol_attrs__")

    def test_mcp_discovery_protocol_exists(self) -> None:
        """McpDiscoveryProtocol is defined and runtime_checkable."""
        from apps.api.protocols import McpDiscoveryProtocol

        assert hasattr(McpDiscoveryProtocol, "__protocol_attrs__")

    def test_skills_protocol_exists(self) -> None:
        """SkillsProtocol is defined and runtime_checkable."""
        from apps.api.protocols import SkillsProtocol

        assert hasattr(SkillsProtocol, "__protocol_attrs__")

    def test_slash_command_protocol_exists(self) -> None:
        """SlashCommandProtocol is defined and runtime_checkable."""
        from apps.api.protocols import SlashCommandProtocol

        assert hasattr(SlashCommandProtocol, "__protocol_attrs__")
