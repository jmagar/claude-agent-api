"""Integration tests for SDK error handling."""

from typing import Any, cast
from unittest.mock import patch

import pytest

from apps.api.exceptions import AgentError
from apps.api.schemas.requests.query import QueryRequest
from apps.api.services.agent import AgentService


@pytest.mark.integration
class TestSDKErrorHandling:
    """Tests for SDK-specific error handling in AgentService."""

    @pytest.mark.anyio
    async def test_cli_not_found_error_handling(self) -> None:
        """Test handling when Claude CLI is not installed."""
        from apps.api.services.agent.types import StreamContext
        from apps.api.services.commands import CommandsService

        service = AgentService()
        request = QueryRequest(prompt="test")
        ctx = StreamContext(
            session_id="test-session",
            model="sonnet",
            start_time=0.0,
        )

        # Mock ClaudeSDKClient to raise CLINotFoundError
        # SDK is imported inside _execute_query, so patch at import location
        with patch("claude_agent_sdk.ClaudeSDKClient") as mock_sdk_client:
            # Import error class from SDK
            from claude_agent_sdk import CLINotFoundError

            mock_sdk_client.side_effect = CLINotFoundError(
                "Claude Code CLI not found in PATH"
            )

            # Should raise AgentError with helpful message
            with pytest.raises(AgentError) as exc_info:
                from pathlib import Path

                commands_service = CommandsService(project_path=Path.cwd())
                async for _ in service._execute_query(request, ctx, commands_service):
                    pass

            # Error message is now sanitized for security (no installation details exposed)
            assert "Claude Code CLI is not installed" in str(exc_info.value)
            # Detailed error is logged but not exposed to client for security

    @pytest.mark.anyio
    async def test_cli_connection_error_handling(self) -> None:
        """Test handling when connection to Claude Code fails."""
        from apps.api.services.agent.types import StreamContext
        from apps.api.services.commands import CommandsService

        service = AgentService()
        request = QueryRequest(prompt="test")
        ctx = StreamContext(
            session_id="test-session",
            model="sonnet",
            start_time=0.0,
        )

        with patch("claude_agent_sdk.ClaudeSDKClient") as mock_sdk_client:
            from claude_agent_sdk import CLIConnectionError

            mock_sdk_client.side_effect = CLIConnectionError(
                "Failed to connect to Claude Code"
            )

            with pytest.raises(AgentError) as exc_info:
                from pathlib import Path

                commands_service = CommandsService(project_path=Path.cwd())
                async for _ in service._execute_query(request, ctx, commands_service):
                    pass

            assert "Connection to Claude Code failed" in str(exc_info.value)

    @pytest.mark.anyio
    async def test_process_error_handling(self) -> None:
        """Test handling when Claude Code process fails."""
        from apps.api.services.agent.types import StreamContext
        from apps.api.services.commands import CommandsService

        service = AgentService()
        request = QueryRequest(prompt="test")
        ctx = StreamContext(
            session_id="test-session",
            model="sonnet",
            start_time=0.0,
        )

        with patch("claude_agent_sdk.ClaudeSDKClient") as mock_sdk_client:
            from claude_agent_sdk import ProcessError

            # Create a ProcessError with exit_code and stderr attributes
            error = ProcessError("Process exited with code 1")
            error.exit_code = 1
            error.stderr = "Fatal error occurred"

            mock_sdk_client.side_effect = error

            with pytest.raises(AgentError) as exc_info:
                from pathlib import Path

                commands_service = CommandsService(project_path=Path.cwd())
                async for _ in service._execute_query(request, ctx, commands_service):
                    pass

            assert "Process failed" in str(exc_info.value)

    @pytest.mark.anyio
    async def test_json_decode_error_handling(self) -> None:
        """Test handling when SDK response parsing fails."""
        from apps.api.services.agent.types import StreamContext
        from apps.api.services.commands import CommandsService

        service = AgentService()
        request = QueryRequest(prompt="test")
        ctx = StreamContext(
            session_id="test-session",
            model="sonnet",
            start_time=0.0,
        )

        with patch("claude_agent_sdk.ClaudeSDKClient") as mock_sdk_client:
            from claude_agent_sdk import CLIJSONDecodeError

            # Create error with line attribute
            try:
                # Try with both arguments
                error = CLIJSONDecodeError(
                    "Failed to parse JSON", Exception("original error")
                )
            except TypeError:
                # Fall back to single argument
                error = cast("Any", CLIJSONDecodeError)("Failed to parse JSON")
            error.line = '{"incomplete": '

            mock_sdk_client.side_effect = error

            with pytest.raises(AgentError) as exc_info:
                from pathlib import Path

                commands_service = CommandsService(project_path=Path.cwd())
                async for _ in service._execute_query(request, ctx, commands_service):
                    pass

            assert "SDK response parsing failed" in str(exc_info.value)

    @pytest.mark.anyio
    async def test_generic_sdk_error_handling(self) -> None:
        """Test handling of generic ClaudeSDKError."""
        from apps.api.services.agent.types import StreamContext
        from apps.api.services.commands import CommandsService

        service = AgentService()
        request = QueryRequest(prompt="test")
        ctx = StreamContext(
            session_id="test-session",
            model="sonnet",
            start_time=0.0,
        )

        with patch("claude_agent_sdk.ClaudeSDKClient") as mock_sdk_client:
            from claude_agent_sdk import ClaudeSDKError

            mock_sdk_client.side_effect = ClaudeSDKError("Generic SDK error")

            with pytest.raises(AgentError) as exc_info:
                from pathlib import Path

                commands_service = CommandsService(project_path=Path.cwd())
                async for _ in service._execute_query(request, ctx, commands_service):
                    pass

            assert "SDK error" in str(exc_info.value)

    @pytest.mark.anyio
    async def test_error_context_marked_as_error(self) -> None:
        """Test that context is_error flag is set when errors occur."""
        from apps.api.services.agent.types import StreamContext
        from apps.api.services.commands import CommandsService

        service = AgentService()
        request = QueryRequest(prompt="test")
        ctx = StreamContext(
            session_id="test-session",
            model="sonnet",
            start_time=0.0,
        )

        with patch("claude_agent_sdk.ClaudeSDKClient") as mock_sdk_client:
            from claude_agent_sdk import CLINotFoundError

            mock_sdk_client.side_effect = CLINotFoundError("CLI not found")

            with pytest.raises(AgentError):
                from pathlib import Path

                commands_service = CommandsService(project_path=Path.cwd())
                async for _ in service._execute_query(request, ctx, commands_service):
                    pass

            # Context should be marked as error
            assert ctx.is_error is True
