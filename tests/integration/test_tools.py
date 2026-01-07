"""Integration tests for tool configuration functionality (User Story 3).

Tests for T056: Tool restriction integration tests.
"""

import pytest
from httpx import AsyncClient

from apps.api.schemas.requests import QueryRequest


class TestToolRestrictionValidation:
    """Tests for tool restriction request validation."""

    @pytest.mark.anyio
    async def test_allowed_tools_parameter_accepted(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that allowed_tools parameter is accepted in query request."""
        response = await async_client.post(
            "/api/v1/query",
            json={
                "prompt": "List files",
                "allowed_tools": ["Read", "Glob"],
            },
            headers=auth_headers,
        )
        # Should accept the request (stream starts) - status 200 for SSE
        assert response.status_code == 200

    @pytest.mark.anyio
    async def test_disallowed_tools_parameter_accepted(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that disallowed_tools parameter is accepted in query request."""
        response = await async_client.post(
            "/api/v1/query",
            json={
                "prompt": "List files",
                "disallowed_tools": ["Bash", "Write"],
            },
            headers=auth_headers,
        )
        assert response.status_code == 200

    @pytest.mark.anyio
    async def test_allowed_and_disallowed_tools_together(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that both allowed_tools and disallowed_tools can be specified.

        Note: The same tool cannot appear in both lists - they must be disjoint.
        """
        response = await async_client.post(
            "/api/v1/query",
            json={
                "prompt": "List files",
                "allowed_tools": ["Read", "Glob", "Grep"],
                "disallowed_tools": ["Bash", "Write"],
            },
            headers=auth_headers,
        )
        assert response.status_code == 200

    @pytest.mark.anyio
    async def test_conflicting_tools_rejected(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that conflicting tools (same tool in both lists) are rejected."""
        response = await async_client.post(
            "/api/v1/query",
            json={
                "prompt": "List files",
                "allowed_tools": ["Read", "Glob", "Bash"],
                "disallowed_tools": ["Bash"],
            },
            headers=auth_headers,
        )
        # Should be rejected due to Bash appearing in both lists
        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_empty_allowed_tools_list_accepted(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that empty allowed_tools list is accepted."""
        response = await async_client.post(
            "/api/v1/query",
            json={
                "prompt": "List files",
                "allowed_tools": [],
            },
            headers=auth_headers,
        )
        assert response.status_code == 200


class TestToolRestrictionSchema:
    """Tests for tool restriction in QueryRequest schema."""

    @pytest.mark.anyio
    async def test_schema_accepts_allowed_tools(self) -> None:
        """Test that QueryRequest schema accepts allowed_tools."""
        request = QueryRequest(
            prompt="Test prompt",
            allowed_tools=["Read", "Write", "Edit"],
        )
        assert request.allowed_tools == ["Read", "Write", "Edit"]

    @pytest.mark.anyio
    async def test_schema_accepts_disallowed_tools(self) -> None:
        """Test that QueryRequest schema accepts disallowed_tools."""
        request = QueryRequest(
            prompt="Test prompt",
            disallowed_tools=["Bash"],
        )
        assert request.disallowed_tools == ["Bash"]

    @pytest.mark.anyio
    async def test_schema_defaults_to_empty_lists(self) -> None:
        """Test that tools default to empty lists when not specified."""
        request = QueryRequest(prompt="Test prompt")
        assert request.allowed_tools == []
        assert request.disallowed_tools == []


class TestToolRestrictionWithResume:
    """Tests for tool restriction in session resume scenarios."""

    @pytest.mark.anyio
    async def test_resume_with_tool_override(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_session_id: str,
    ) -> None:
        """Test that tools can be overridden when resuming session."""
        response = await async_client.post(
            f"/api/v1/sessions/{mock_session_id}/resume",
            json={
                "prompt": "Continue with different tools",
                "allowed_tools": ["Read"],
            },
            headers=auth_headers,
        )
        assert response.status_code == 200

    @pytest.mark.anyio
    async def test_resume_inherits_tools_when_not_specified(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_session_id: str,
    ) -> None:
        """Test that tools are inherited when not specified in resume."""
        response = await async_client.post(
            f"/api/v1/sessions/{mock_session_id}/resume",
            json={
                "prompt": "Continue without specifying tools",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200


class TestToolRestrictionWithFork:
    """Tests for tool restriction in session fork scenarios."""

    @pytest.mark.anyio
    async def test_fork_with_tool_override(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_session_id: str,
    ) -> None:
        """Test that tools can be overridden when forking session."""
        response = await async_client.post(
            f"/api/v1/sessions/{mock_session_id}/fork",
            json={
                "prompt": "Fork with different tools",
                "allowed_tools": ["Read", "Glob"],
                "disallowed_tools": ["Bash"],
            },
            headers=auth_headers,
        )
        assert response.status_code == 200


class TestToolRestrictionSingleQuery:
    """Tests for tool restriction in non-streaming (single) query."""

    @pytest.mark.anyio
    async def test_single_query_with_allowed_tools(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that allowed_tools works with single (non-streaming) query."""
        response = await async_client.post(
            "/api/v1/query/single",
            json={
                "prompt": "List files",
                "allowed_tools": ["Read", "Glob"],
            },
            headers=auth_headers,
        )
        assert response.status_code == 200

    @pytest.mark.anyio
    async def test_single_query_with_disallowed_tools(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that disallowed_tools works with single query."""
        response = await async_client.post(
            "/api/v1/query/single",
            json={
                "prompt": "List files",
                "disallowed_tools": ["Write", "Edit"],
            },
            headers=auth_headers,
        )
        assert response.status_code == 200


class TestBuiltInToolsValidation:
    """Tests for built-in tools constant validation (T060)."""

    @pytest.mark.anyio
    async def test_builtin_tools_defined(self) -> None:
        """Test that BUILT_IN_TOOLS constant is defined in types module."""
        from apps.api.types import BUILT_IN_TOOLS

        # Verify it's a collection
        assert isinstance(BUILT_IN_TOOLS, (list, tuple, set, frozenset))
        # Verify it contains expected tools per US3 acceptance criteria
        expected_tools = {
            "Read",
            "Write",
            "Edit",
            "Bash",
            "Glob",
            "Grep",
            "Task",
        }
        for tool in expected_tools:
            assert tool in BUILT_IN_TOOLS, f"Expected {tool} in BUILT_IN_TOOLS"


class TestToolRestrictionSDKIntegration:
    """Integration tests requiring SDK for tool restriction behavior."""

    @pytest.mark.anyio
    async def test_agent_respects_allowed_tools(
        self,
        _async_client: AsyncClient,
        _auth_headers: dict[str, str],
    ) -> None:
        """Test that agent only uses permitted tools.

        Per US3 acceptance scenario 1: Given a list of allowed tools,
        when the agent attempts to use an unlisted tool, the system blocks it.
        """
        pytest.skip("Requires SDK integration for full tool restriction testing")

    @pytest.mark.anyio
    async def test_agent_respects_disallowed_tools(
        self,
        _async_client: AsyncClient,
        _auth_headers: dict[str, str],
    ) -> None:
        """Test that agent cannot use disallowed tools.

        Per US3 acceptance scenario 2: Given read-only tools configured,
        when the agent is asked to modify a file, it reports it cannot.
        """
        pytest.skip("Requires SDK integration for full tool restriction testing")
