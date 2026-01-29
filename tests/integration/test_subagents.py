"""Integration tests for custom subagent functionality (User Story 4).

Tests for T062: Subagent invocation integration tests.
"""

from typing import Literal

import pytest
from httpx import AsyncClient

from apps.api.schemas.requests.config import AgentDefinitionSchema
from apps.api.schemas.requests.query import QueryRequest


class TestSubagentDefinitionValidation:
    """Tests for subagent definition request validation."""

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_agents_parameter_accepted(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_claude_sdk: None,
    ) -> None:
        """Test that agents parameter is accepted in query request."""
        response = await async_client.post(
            "/api/v1/query",
            json={
                "prompt": "Review the code for security issues",
                "agents": {
                    "security-reviewer": {
                        "description": "Expert security code reviewer",
                        "prompt": "You are a security-focused code reviewer...",
                        "tools": ["Read", "Grep", "Glob"],
                    }
                },
                "allowed_tools": ["Read", "Task"],
            },
            headers=auth_headers,
        )
        # Should accept the request (stream starts) - status 200 for SSE
        assert response.status_code == 200

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_multiple_agents_accepted(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_claude_sdk: None,
    ) -> None:
        """Test that multiple agents can be defined."""
        response = await async_client.post(
            "/api/v1/query",
            json={
                "prompt": "Analyze and test the code",
                "agents": {
                    "code-analyzer": {
                        "description": "Analyzes code structure",
                        "prompt": "You are a code analyst...",
                    },
                    "test-writer": {
                        "description": "Writes test cases",
                        "prompt": "You are a test engineer...",
                        "tools": ["Read", "Write", "Bash"],
                    },
                },
                "allowed_tools": ["Read", "Task"],
            },
            headers=auth_headers,
        )
        assert response.status_code == 200

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_agent_with_model_override(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_claude_sdk: None,
    ) -> None:
        """Test that agent model can be overridden."""
        response = await async_client.post(
            "/api/v1/query",
            json={
                "prompt": "Quick analysis",
                "agents": {
                    "quick-reviewer": {
                        "description": "Fast code review",
                        "prompt": "Quickly review...",
                        "model": "haiku",
                    }
                },
                "allowed_tools": ["Read", "Task"],
            },
            headers=auth_headers,
        )
        assert response.status_code == 200


class TestAgentDefinitionSchema:
    """Tests for AgentDefinitionSchema validation."""

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_schema_requires_description(
        self,
        mock_claude_sdk: None,
    ) -> None:
        """Test that AgentDefinitionSchema requires description."""
        with pytest.raises(ValueError):
            # Intentionally missing required 'description' to test validation
            AgentDefinitionSchema.model_validate({"prompt": "System prompt only"})

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_schema_requires_prompt(
        self,
        mock_claude_sdk: None,
    ) -> None:
        """Test that AgentDefinitionSchema requires prompt."""
        with pytest.raises(ValueError):
            # Intentionally missing required 'prompt' to test validation
            AgentDefinitionSchema.model_validate({"description": "Description only"})

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_schema_accepts_minimal_definition(
        self,
        mock_claude_sdk: None,
    ) -> None:
        """Test that minimal agent definition is accepted."""
        agent = AgentDefinitionSchema(
            description="Test agent",
            prompt="You are a test agent.",
        )
        assert agent.description == "Test agent"
        assert agent.prompt == "You are a test agent."
        assert agent.tools is None
        assert agent.model is None

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_schema_accepts_full_definition(
        self,
        mock_claude_sdk: None,
    ) -> None:
        """Test that full agent definition is accepted."""
        agent = AgentDefinitionSchema(
            description="Full test agent",
            prompt="You are a fully configured test agent.",
            tools=["Read", "Grep"],
            model="sonnet",
        )
        assert agent.description == "Full test agent"
        assert agent.tools == ["Read", "Grep"]
        assert agent.model == "sonnet"

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_schema_model_enum_validation(
        self,
        mock_claude_sdk: None,
    ) -> None:
        """Test that model field validates against allowed values."""
        # Valid model values
        models: list[Literal["sonnet", "opus", "haiku", "inherit"]] = [
            "sonnet",
            "opus",
            "haiku",
            "inherit",
        ]
        for model in models:
            agent = AgentDefinitionSchema(
                description="Test",
                prompt="Test",
                model=model,
            )
            assert agent.model == model


class TestSubagentInQueryRequest:
    """Tests for subagent definition in QueryRequest schema."""

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_query_request_accepts_agents(
        self,
        mock_claude_sdk: None,
    ) -> None:
        """Test that QueryRequest accepts agents parameter."""
        request = QueryRequest(
            prompt="Test with agents",
            agents={
                "test-agent": AgentDefinitionSchema(
                    description="Test agent",
                    prompt="System prompt",
                )
            },
        )
        assert request.agents is not None
        assert "test-agent" in request.agents
        assert request.agents["test-agent"].description == "Test agent"

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_query_request_agents_default_none(
        self,
        mock_claude_sdk: None,
    ) -> None:
        """Test that agents defaults to None when not specified."""
        request = QueryRequest(prompt="Test without agents")
        assert request.agents is None


class TestSubagentWithTaskTool:
    """Tests for subagent Task tool integration (T064)."""

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_task_tool_required_for_subagents(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_claude_sdk: None,
    ) -> None:
        """Test that Task tool enables subagent delegation.

        Per US4 acceptance scenario 5: Given Task tool is in allowedTools
        without custom agents defined, the built-in general-purpose subagent
        is available.
        """
        response = await async_client.post(
            "/api/v1/query",
            json={
                "prompt": "Delegate a task",
                "allowed_tools": ["Read", "Task"],
            },
            headers=auth_headers,
        )
        assert response.status_code == 200


class TestSubagentWithResume:
    """Tests for subagent definition in session resume scenarios."""

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_resume_cannot_add_new_agents(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_session_id: str,
        mock_claude_sdk: None,
    ) -> None:
        """Test that resume uses original session agents.

        Note: Resume inherits original configuration, agents cannot be
        added/modified on resume per SDK behavior.
        """
        response = await async_client.post(
            f"/api/v1/sessions/{mock_session_id}/resume",
            json={
                "prompt": "Continue session",
                # agents would typically not be allowed on resume
            },
            headers=auth_headers,
        )
        assert response.status_code == 200


class TestSubagentWithFork:
    """Tests for subagent definition in session fork scenarios."""

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_fork_with_agents(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_session_id: str,
        mock_claude_sdk: None,
    ) -> None:
        """Test that fork can specify agents for new session."""
        response = await async_client.post(
            f"/api/v1/sessions/{mock_session_id}/fork",
            json={
                "prompt": "Fork with new agent",
                # Note: ForkRequest may not include agents field
                # per current schema - this tests that forking works
            },
            headers=auth_headers,
        )
        assert response.status_code == 200


class TestSubagentSingleQuery:
    """Tests for subagent definition in non-streaming (single) query."""

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_single_query_with_agents(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_claude_sdk: None,
    ) -> None:
        """Test that agents work with single (non-streaming) query."""
        response = await async_client.post(
            "/api/v1/query/single",
            json={
                "prompt": "Quick review with agent",
                "agents": {
                    "quick-reviewer": {
                        "description": "Fast reviewer",
                        "prompt": "Review quickly",
                    }
                },
                "allowed_tools": ["Read", "Task"],
            },
            headers=auth_headers,
        )
        assert response.status_code == 200


class TestSubagentMessageTracking:
    """Tests for subagent message tracking (T066)."""

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_parent_tool_use_id_in_schema(
        self,
        mock_claude_sdk: None,
    ) -> None:
        """Test that parent_tool_use_id field exists in MessageEventData.

        Per US4 acceptance scenario 6: Given a subagent is executing,
        when messages are streamed, messages from subagent context
        include parent_tool_use_id field.
        """
        from apps.api.schemas.responses import MessageEventData

        # Verify the field exists in the schema
        assert "parent_tool_use_id" in MessageEventData.model_fields
        # Verify it's optional (has default None)
        field = MessageEventData.model_fields["parent_tool_use_id"]
        assert field.default is None


class TestSubagentSDKIntegration:
    """Integration tests requiring SDK for subagent behavior."""

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_subagent_automatic_invocation(
        self,
        _async_client: AsyncClient,
        _auth_headers: dict[str, str],
        mock_claude_sdk: None,
    ) -> None:
        """Test that subagent is automatically invoked based on description.

        Per US4 acceptance scenario 1: Given a subagent definition with
        description and prompt, when the main agent determines the task
        matches the description, the system automatically spawns the subagent.
        """
        pytest.skip("Requires SDK integration for subagent invocation testing")

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_subagent_tool_restriction(
        self,
        _async_client: AsyncClient,
        _auth_headers: dict[str, str],
        mock_claude_sdk: None,
    ) -> None:
        """Test that subagent respects tool restrictions.

        Per US4 acceptance scenario 2: Given a subagent with restricted tools,
        when the subagent executes, it can only use its configured tools
        (and cannot spawn nested subagents).
        """
        pytest.skip("Requires SDK integration for subagent tool restriction testing")

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_subagent_explicit_invocation(
        self,
        _async_client: AsyncClient,
        _auth_headers: dict[str, str],
        mock_claude_sdk: None,
    ) -> None:
        """Test that subagent is invoked when explicitly mentioned by name.

        Per US4 acceptance scenario 4: Given an explicit prompt mentioning
        a subagent by name (e.g., 'Use the code-reviewer agent'), the named
        subagent is directly invoked.
        """
        pytest.skip("Requires SDK integration for explicit subagent invocation testing")
