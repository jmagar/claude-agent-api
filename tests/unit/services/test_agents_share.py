"""Unit tests for agent share functionality with type safety."""

import pytest

from apps.api.protocols import SharedAgent
from apps.api.services.agents import AgentService


@pytest.mark.unit
@pytest.mark.anyio
class TestAgentShare:
    """Tests for agent sharing with protocol type safety."""

    async def test_share_agent_returns_shared_agent_protocol(
        self, mock_cache: object
    ) -> None:
        """Test that share_agent returns object satisfying SharedAgent protocol."""
        service = AgentService(cache=mock_cache)

        # Create an agent first
        agent = await service.create_agent(
            name="Test Agent",
            description="Test description",
            prompt="Test prompt",
            tools=["Read", "Write"],
            model="sonnet",
        )

        # Share the agent
        shared = await service.share_agent(agent.id, "https://example.com/share/123")

        # Verify protocol compliance
        assert shared is not None
        assert isinstance(shared, SharedAgent)
        assert shared.share_token is not None
        assert isinstance(shared.share_token, str)
        assert len(shared.share_token) > 0
        assert shared.share_url is not None
        assert shared.share_url == "https://example.com/share/123"

    async def test_share_agent_generates_unique_tokens(
        self, mock_cache: object
    ) -> None:
        """Test that sharing generates unique tokens for each agent."""
        service = AgentService(cache=mock_cache)

        # Create two agents
        agent1 = await service.create_agent(
            name="Agent 1",
            description="First agent",
            prompt="Prompt 1",
            tools=None,
            model=None,
        )
        agent2 = await service.create_agent(
            name="Agent 2",
            description="Second agent",
            prompt="Prompt 2",
            tools=None,
            model=None,
        )

        # Share both agents
        shared1 = await service.share_agent(agent1.id, "https://example.com/share/1")
        shared2 = await service.share_agent(agent2.id, "https://example.com/share/2")

        # Tokens should be different
        assert shared1 is not None
        assert shared2 is not None
        assert shared1.share_token != shared2.share_token

    async def test_share_agent_returns_none_for_nonexistent(
        self, mock_cache: object
    ) -> None:
        """Test that share_agent returns None for non-existent agent."""
        service = AgentService(cache=mock_cache)

        result = await service.share_agent(
            "nonexistent-id", "https://example.com/share/404"
        )

        assert result is None

    async def test_share_agent_protocol_attributes_accessible_without_hasattr(
        self, mock_cache: object
    ) -> None:
        """Test that SharedAgent protocol attributes are directly accessible."""
        service = AgentService(cache=mock_cache)

        agent = await service.create_agent(
            name="Test",
            description="Test",
            prompt="Test",
            tools=None,
            model=None,
        )

        shared = await service.share_agent(agent.id, "https://example.com/share/test")

        # This should work without hasattr() checks or casting
        assert shared is not None
        # Direct attribute access - no hasattr() needed
        share_token: str = shared.share_token
        share_url: str | None = shared.share_url

        assert isinstance(share_token, str)
        assert isinstance(share_url, (str, type(None)))
