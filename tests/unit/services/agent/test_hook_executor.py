"""Unit tests for HookExecutor (Priority 3).

Tests webhook hook execution for agent lifecycle events.
"""

from unittest.mock import AsyncMock

import pytest

from apps.api.schemas.requests.config import HooksConfigSchema, HookWebhookSchema
from apps.api.services.agent.hooks import HookExecutor


@pytest.fixture
def mock_webhook_service() -> AsyncMock:
    """Create mock WebhookService.

    Returns:
        AsyncMock instance with execute_hook method.
    """
    service = AsyncMock()
    service.execute_hook = AsyncMock()
    return service


@pytest.fixture
def hook_executor(mock_webhook_service: AsyncMock) -> HookExecutor:
    """Create HookExecutor with mocked webhook service.

    Args:
        mock_webhook_service: Mocked WebhookService.

    Returns:
        HookExecutor instance.
    """
    return HookExecutor(mock_webhook_service)


class TestPreToolUse:
    """Tests for PreToolUse hook execution."""

    @pytest.mark.anyio
    async def test_execute_pre_tool_use_calls_webhook(
        self,
        hook_executor: HookExecutor,
        mock_webhook_service: AsyncMock,
    ) -> None:
        """Test PreToolUse webhook is called with correct payload.

        GREEN: This test verifies webhook execution with proper parameters.
        """
        hooks_config = HooksConfigSchema(
            pre_tool_use=HookWebhookSchema(url="https://example.com/hook")
        )
        mock_webhook_service.execute_hook.return_value = {"decision": "allow"}

        result = await hook_executor.execute_pre_tool_use(
            hooks_config,
            session_id="test-session-123",
            tool_name="Read",
            tool_input={"file_path": "/path/to/file.py"},
        )

        # Verify webhook was called
        mock_webhook_service.execute_hook.assert_called_once_with(
            hook_event="PreToolUse",
            hook_config=hooks_config.pre_tool_use,
            session_id="test-session-123",
            tool_name="Read",
            tool_input={"file_path": "/path/to/file.py"},
        )
        assert result == {"decision": "allow"}

    @pytest.mark.anyio
    async def test_execute_pre_tool_use_returns_allow_when_no_config(
        self,
        hook_executor: HookExecutor,
        mock_webhook_service: AsyncMock,
    ) -> None:
        """Test default allow behavior when no hooks configured.

        GREEN: This test verifies default behavior without configuration.
        """
        result = await hook_executor.execute_pre_tool_use(
            None,
            session_id="test-session-123",
            tool_name="Read",
        )

        # Should not call webhook
        mock_webhook_service.execute_hook.assert_not_called()
        # Should default to allow
        assert result == {"decision": "allow"}


class TestPostToolUse:
    """Tests for PostToolUse hook execution."""

    @pytest.mark.anyio
    async def test_execute_post_tool_use_calls_webhook(
        self,
        hook_executor: HookExecutor,
        mock_webhook_service: AsyncMock,
    ) -> None:
        """Test PostToolUse webhook execution.

        GREEN: This test verifies post-tool webhook is called correctly.
        """
        hooks_config = HooksConfigSchema(
            post_tool_use=HookWebhookSchema(url="https://example.com/post-hook")
        )
        mock_webhook_service.execute_hook.return_value = {"acknowledged": True}

        result = await hook_executor.execute_post_tool_use(
            hooks_config,
            session_id="test-session-456",
            tool_name="Write",
            tool_input={"file_path": "/test.py", "content": "test"},
            tool_result={"success": True},
        )

        # Verify webhook was called with all parameters
        mock_webhook_service.execute_hook.assert_called_once_with(
            hook_event="PostToolUse",
            hook_config=hooks_config.post_tool_use,
            session_id="test-session-456",
            tool_name="Write",
            tool_input={"file_path": "/test.py", "content": "test"},
            tool_result={"success": True},
        )
        assert result == {"acknowledged": True}


class TestStop:
    """Tests for Stop hook execution."""

    @pytest.mark.anyio
    async def test_execute_stop_builds_result_data(
        self,
        hook_executor: HookExecutor,
        mock_webhook_service: AsyncMock,
    ) -> None:
        """Test Stop webhook with result data.

        GREEN: This test verifies stop event with complete result data.
        """
        hooks_config = HooksConfigSchema(
            stop=HookWebhookSchema(url="https://example.com/stop")
        )
        mock_webhook_service.execute_hook.return_value = {"acknowledged": True}

        await hook_executor.execute_stop(
            hooks_config,
            session_id="test-session-789",
            is_error=False,
            duration_ms=1500,
            result="Operation completed successfully",
        )

        # Verify webhook was called with result data
        call_args = mock_webhook_service.execute_hook.call_args
        assert call_args.kwargs["hook_event"] == "Stop"
        assert call_args.kwargs["session_id"] == "test-session-789"

        result_data = call_args.kwargs["result_data"]
        assert result_data["is_error"] is False
        assert result_data["duration_ms"] == 1500
        assert result_data["result"] == "Operation completed successfully"


class TestSubagentStop:
    """Tests for SubagentStop hook execution."""

    @pytest.mark.anyio
    async def test_execute_subagent_stop_includes_subagent_name(
        self,
        hook_executor: HookExecutor,
        mock_webhook_service: AsyncMock,
    ) -> None:
        """Test SubagentStop includes subagent metadata.

        GREEN: This test verifies subagent name is passed correctly.
        """
        hooks_config = HooksConfigSchema(
            subagent_stop=HookWebhookSchema(url="https://example.com/subagent-stop")
        )
        mock_webhook_service.execute_hook.return_value = {"acknowledged": True}

        await hook_executor.execute_subagent_stop(
            hooks_config,
            session_id="test-session-sub",
            subagent_name="code-reviewer",
            is_error=False,
            result="Review complete",
        )

        # Verify subagent name is included
        call_args = mock_webhook_service.execute_hook.call_args
        result_data = call_args.kwargs["result_data"]
        assert result_data["subagent_name"] == "code-reviewer"
        assert result_data["is_error"] is False
        assert result_data["result"] == "Review complete"


class TestUserPromptSubmit:
    """Tests for UserPromptSubmit hook execution."""

    @pytest.mark.anyio
    async def test_execute_user_prompt_submit_passes_prompt(
        self,
        hook_executor: HookExecutor,
        mock_webhook_service: AsyncMock,
    ) -> None:
        """Test UserPromptSubmit passes prompt to webhook.

        GREEN: This test verifies prompt submission hook.
        """
        hooks_config = HooksConfigSchema(
            user_prompt_submit=HookWebhookSchema(
                url="https://example.com/prompt-submit"
            )
        )
        mock_webhook_service.execute_hook.return_value = {"decision": "allow"}

        result = await hook_executor.execute_user_prompt_submit(
            hooks_config,
            session_id="test-session-prompt",
            prompt="List all Python files",
        )

        # Verify prompt is passed in tool_input
        call_args = mock_webhook_service.execute_hook.call_args
        assert call_args.kwargs["hook_event"] == "UserPromptSubmit"
        assert call_args.kwargs["session_id"] == "test-session-prompt"
        assert call_args.kwargs["tool_input"] == {"prompt": "List all Python files"}
        assert result == {"decision": "allow"}
