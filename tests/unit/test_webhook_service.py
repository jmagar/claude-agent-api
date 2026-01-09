"""Unit tests for WebhookService (User Story 7, T083).

These tests verify the webhook service that handles HTTP callbacks
for hook events (PreToolUse, PostToolUse, Stop, etc.).
"""

from typing import Literal
from unittest.mock import MagicMock, patch

import pytest

from apps.api.schemas.requests.config import HooksConfigSchema, HookWebhookSchema


# Type definitions for webhook payloads
class WebhookPayload:
    """Type-safe webhook payload structure."""

    hook_event: str
    session_id: str
    tool_name: str | None
    tool_input: dict[str, object] | None


class WebhookResponse:
    """Type-safe webhook response structure."""

    decision: Literal["allow", "deny", "ask"]
    reason: str | None
    modified_input: dict[str, object] | None


class TestWebhookServiceCreation:
    """Tests for WebhookService instantiation."""

    def test_webhook_service_can_be_instantiated(self) -> None:
        """Test that WebhookService can be created."""
        from apps.api.services.webhook import WebhookService

        service = WebhookService()
        assert service is not None

    def test_webhook_service_with_custom_http_client(self) -> None:
        """Test WebhookService can use a custom HTTP client."""
        from apps.api.services.webhook import WebhookService

        mock_client = MagicMock()
        service = WebhookService(http_client=mock_client)
        assert service is not None


class TestWebhookCallbackExecution:
    """Tests for webhook callback execution."""

    @pytest.mark.anyio
    async def test_execute_pre_tool_use_callback(self) -> None:
        """Test executing PreToolUse webhook callback."""
        from apps.api.services.webhook import WebhookService

        service = WebhookService()
        hook_config = HookWebhookSchema(
            url="https://example.com/webhook",  # type: ignore[arg-type]
            timeout=30,
        )

        # Mock the HTTP response
        with patch.object(service, "_make_request") as mock_request:
            mock_request.return_value = {"decision": "allow"}

            result = await service.execute_hook(
                hook_event="PreToolUse",
                hook_config=hook_config,
                session_id="test-session-123",
                tool_name="Write",
                tool_input={"file_path": "/test.txt", "content": "test"},
            )

            assert result["decision"] == "allow"
            mock_request.assert_called_once()

    @pytest.mark.anyio
    async def test_execute_post_tool_use_callback(self) -> None:
        """Test executing PostToolUse webhook callback."""
        from apps.api.services.webhook import WebhookService

        service = WebhookService()
        hook_config = HookWebhookSchema(
            url="https://example.com/webhook",  # type: ignore[arg-type]
            timeout=30,
        )

        with patch.object(service, "_make_request") as mock_request:
            mock_request.return_value = {"decision": "allow"}

            result = await service.execute_hook(
                hook_event="PostToolUse",
                hook_config=hook_config,
                session_id="test-session-123",
                tool_name="Write",
                tool_input={"file_path": "/test.txt"},
                tool_result={"success": True},
            )

            assert result["decision"] == "allow"

    @pytest.mark.anyio
    async def test_execute_stop_callback(self) -> None:
        """Test executing Stop webhook callback."""
        from apps.api.services.webhook import WebhookService

        service = WebhookService()
        hook_config = HookWebhookSchema(
            url="https://example.com/webhook",  # type: ignore[arg-type]
            timeout=30,
        )

        with patch.object(service, "_make_request") as mock_request:
            mock_request.return_value = {"acknowledged": True}

            result = await service.execute_hook(
                hook_event="Stop",
                hook_config=hook_config,
                session_id="test-session-123",
            )

            assert result is not None

    @pytest.mark.anyio
    async def test_callback_includes_custom_headers(self) -> None:
        """Test that custom headers are included in webhook request."""
        from apps.api.services.webhook import WebhookService

        service = WebhookService()
        hook_config = HookWebhookSchema(
            url="https://example.com/webhook",  # type: ignore[arg-type]
            headers={
                "Authorization": "Bearer secret-token",
                "X-Custom-Header": "custom-value",
            },
            timeout=30,
        )

        with patch.object(service, "_make_request") as mock_request:
            mock_request.return_value = {"decision": "allow"}

            await service.execute_hook(
                hook_event="PreToolUse",
                hook_config=hook_config,
                session_id="test-session",
                tool_name="Read",
            )

            # Verify headers were passed
            call_kwargs = mock_request.call_args.kwargs
            assert "Authorization" in call_kwargs.get("headers", {})


class TestWebhookResponseHandling:
    """Tests for handling webhook responses."""

    @pytest.mark.anyio
    async def test_allow_response_returns_allow(self) -> None:
        """Test handling 'allow' decision from webhook."""
        from apps.api.services.webhook import WebhookService

        service = WebhookService()
        hook_config = HookWebhookSchema(
            url="https://example.com/webhook",  # type: ignore[arg-type]
        )

        with patch.object(service, "_make_request") as mock_request:
            mock_request.return_value = {
                "decision": "allow",
                "reason": "Tool execution approved",
            }

            result = await service.execute_hook(
                hook_event="PreToolUse",
                hook_config=hook_config,
                session_id="session-1",
                tool_name="Write",
            )

            assert result["decision"] == "allow"
            assert result["reason"] == "Tool execution approved"

    @pytest.mark.anyio
    async def test_deny_response_returns_deny(self) -> None:
        """Test handling 'deny' decision from webhook."""
        from apps.api.services.webhook import WebhookService

        service = WebhookService()
        hook_config = HookWebhookSchema(
            url="https://example.com/webhook",  # type: ignore[arg-type]
        )

        with patch.object(service, "_make_request") as mock_request:
            mock_request.return_value = {
                "decision": "deny",
                "reason": "Operation not permitted",
            }

            result = await service.execute_hook(
                hook_event="PreToolUse",
                hook_config=hook_config,
                session_id="session-1",
                tool_name="Bash",
            )

            assert result["decision"] == "deny"
            assert result["reason"] == "Operation not permitted"

    @pytest.mark.anyio
    async def test_ask_response_returns_ask(self) -> None:
        """Test handling 'ask' decision from webhook."""
        from apps.api.services.webhook import WebhookService

        service = WebhookService()
        hook_config = HookWebhookSchema(
            url="https://example.com/webhook",  # type: ignore[arg-type]
        )

        with patch.object(service, "_make_request") as mock_request:
            mock_request.return_value = {
                "decision": "ask",
                "reason": "User confirmation required",
            }

            result = await service.execute_hook(
                hook_event="PreToolUse",
                hook_config=hook_config,
                session_id="session-1",
                tool_name="Write",
            )

            assert result["decision"] == "ask"

    @pytest.mark.anyio
    async def test_modified_input_in_response(self) -> None:
        """Test handling modified_input in webhook response (FR-020)."""
        from apps.api.services.webhook import WebhookService

        service = WebhookService()
        hook_config = HookWebhookSchema(
            url="https://example.com/webhook",  # type: ignore[arg-type]
        )

        with patch.object(service, "_make_request") as mock_request:
            mock_request.return_value = {
                "decision": "allow",
                "modified_input": {
                    "file_path": "/sanitized/path.txt",
                    "content": "sanitized content",
                },
            }

            result = await service.execute_hook(
                hook_event="PreToolUse",
                hook_config=hook_config,
                session_id="session-1",
                tool_name="Write",
                tool_input={"file_path": "/dangerous/path.txt", "content": "original"},
            )

            assert result["decision"] == "allow"
            assert result["modified_input"]["file_path"] == "/sanitized/path.txt"


class TestWebhookTimeoutHandling:
    """Tests for webhook timeout handling."""

    @pytest.mark.anyio
    async def test_timeout_returns_default_allow(self) -> None:
        """Test that timeout defaults to allow (fail-open for PreToolUse)."""
        from apps.api.services.webhook import WebhookService

        service = WebhookService()
        hook_config = HookWebhookSchema(
            url="https://example.com/webhook",  # type: ignore[arg-type]
            timeout=1,  # 1 second timeout
        )

        with patch.object(service, "_make_request") as mock_request:
            mock_request.side_effect = TimeoutError()

            result = await service.execute_hook(
                hook_event="PreToolUse",
                hook_config=hook_config,
                session_id="session-1",
                tool_name="Read",
            )

            # Default behavior on timeout should be configurable
            # For now, we expect it to return allow (fail-open)
            assert result["decision"] == "allow"
            assert "timeout" in result.get("reason", "").lower()

    @pytest.mark.anyio
    async def test_custom_timeout_is_respected(self) -> None:
        """Test that custom timeout value is used."""
        from apps.api.services.webhook import WebhookService

        service = WebhookService()
        hook_config = HookWebhookSchema(
            url="https://example.com/webhook",  # type: ignore[arg-type]
            timeout=60,  # 60 second timeout
        )

        with patch.object(service, "_make_request") as mock_request:
            mock_request.return_value = {"decision": "allow"}

            await service.execute_hook(
                hook_event="PreToolUse",
                hook_config=hook_config,
                session_id="session-1",
                tool_name="Read",
            )

            # Verify timeout was passed to request
            call_kwargs = mock_request.call_args.kwargs
            assert call_kwargs.get("timeout") == 60


class TestWebhookErrorHandling:
    """Tests for webhook error handling."""

    @pytest.mark.anyio
    async def test_connection_error_returns_default(self) -> None:
        """Test handling connection errors to webhook."""
        from apps.api.services.webhook import WebhookService

        service = WebhookService()
        hook_config = HookWebhookSchema(
            url="https://example.com/webhook",  # type: ignore[arg-type]
        )

        with patch.object(service, "_make_request") as mock_request:
            mock_request.side_effect = ConnectionError("Connection refused")

            result = await service.execute_hook(
                hook_event="PreToolUse",
                hook_config=hook_config,
                session_id="session-1",
                tool_name="Read",
            )

            # Should return allow on connection error (fail-open)
            assert result["decision"] == "allow"
            assert "error" in result.get("reason", "").lower()

    @pytest.mark.anyio
    async def test_invalid_json_response_returns_default(self) -> None:
        """Test handling invalid JSON responses from webhook."""
        from apps.api.services.webhook import WebhookService

        service = WebhookService()
        hook_config = HookWebhookSchema(
            url="https://example.com/webhook",  # type: ignore[arg-type]
        )

        with patch.object(service, "_make_request") as mock_request:
            mock_request.side_effect = ValueError("Invalid JSON")

            result = await service.execute_hook(
                hook_event="PreToolUse",
                hook_config=hook_config,
                session_id="session-1",
                tool_name="Read",
            )

            assert result["decision"] == "allow"

    @pytest.mark.anyio
    async def test_http_error_status_returns_default(self) -> None:
        """Test handling HTTP error status codes from webhook."""
        from apps.api.services.webhook import WebhookHttpError, WebhookService

        service = WebhookService()
        hook_config = HookWebhookSchema(
            url="https://example.com/webhook",  # type: ignore[arg-type]
        )

        with patch.object(service, "_make_request") as mock_request:
            mock_request.side_effect = WebhookHttpError(500, "Internal Server Error")

            result = await service.execute_hook(
                hook_event="PreToolUse",
                hook_config=hook_config,
                session_id="session-1",
                tool_name="Read",
            )

            assert result["decision"] == "allow"


class TestMatcherFiltering:
    """Tests for tool name matcher filtering (T088)."""

    @pytest.mark.anyio
    async def test_matcher_allows_matching_tool(self) -> None:
        """Test that matcher allows tools that match the pattern."""
        from apps.api.services.webhook import WebhookService

        service = WebhookService()
        hook_config = HookWebhookSchema(
            url="https://example.com/webhook",  # type: ignore[arg-type]
            matcher="Write|Edit",
        )

        # Should execute hook for matching tool
        should_execute = service.should_execute_hook(
            hook_config=hook_config,
            tool_name="Write",
        )
        assert should_execute is True

        should_execute = service.should_execute_hook(
            hook_config=hook_config,
            tool_name="Edit",
        )
        assert should_execute is True

    @pytest.mark.anyio
    async def test_matcher_blocks_non_matching_tool(self) -> None:
        """Test that matcher blocks tools that don't match the pattern."""
        from apps.api.services.webhook import WebhookService

        service = WebhookService()
        hook_config = HookWebhookSchema(
            url="https://example.com/webhook",  # type: ignore[arg-type]
            matcher="Write|Edit",
        )

        should_execute = service.should_execute_hook(
            hook_config=hook_config,
            tool_name="Read",
        )
        assert should_execute is False

        should_execute = service.should_execute_hook(
            hook_config=hook_config,
            tool_name="Bash",
        )
        assert should_execute is False

    @pytest.mark.anyio
    async def test_none_matcher_matches_all(self) -> None:
        """Test that None matcher matches all tools."""
        from apps.api.services.webhook import WebhookService

        service = WebhookService()
        hook_config = HookWebhookSchema(
            url="https://example.com/webhook",  # type: ignore[arg-type]
            matcher=None,
        )

        for tool_name in ["Read", "Write", "Edit", "Bash", "mcp__server__tool"]:
            should_execute = service.should_execute_hook(
                hook_config=hook_config,
                tool_name=tool_name,
            )
            assert should_execute is True

    @pytest.mark.anyio
    async def test_regex_matcher_patterns(self) -> None:
        """Test various regex matcher patterns."""
        from apps.api.services.webhook import WebhookService

        service = WebhookService()

        # Pattern for MCP tools
        hook_config = HookWebhookSchema(
            url="https://example.com/webhook",  # type: ignore[arg-type]
            matcher="mcp__.*",
        )

        should_execute = service.should_execute_hook(
            hook_config=hook_config,
            tool_name="mcp__server__tool",
        )
        assert should_execute is True

        should_execute = service.should_execute_hook(
            hook_config=hook_config,
            tool_name="Read",
        )
        assert should_execute is False


class TestWebhookPayloadFormat:
    """Tests for webhook payload formatting."""

    @pytest.mark.anyio
    async def test_pre_tool_use_payload_format(self) -> None:
        """Test PreToolUse webhook payload format."""
        from apps.api.services.webhook import WebhookService

        service = WebhookService()
        hook_config = HookWebhookSchema(
            url="https://example.com/webhook",  # type: ignore[arg-type]
        )

        with patch.object(service, "_make_request") as mock_request:
            mock_request.return_value = {"decision": "allow"}

            await service.execute_hook(
                hook_event="PreToolUse",
                hook_config=hook_config,
                session_id="session-123",
                tool_name="Write",
                tool_input={"file_path": "/test.txt", "content": "hello"},
            )

            # Verify payload format
            call_args = mock_request.call_args
            payload = call_args.kwargs.get("json") or call_args.args[1]

            assert payload["hook_event"] == "PreToolUse"
            assert payload["session_id"] == "session-123"
            assert payload["tool_name"] == "Write"
            assert payload["tool_input"]["file_path"] == "/test.txt"

    @pytest.mark.anyio
    async def test_stop_payload_format(self) -> None:
        """Test Stop webhook payload format."""
        from apps.api.services.webhook import WebhookService

        service = WebhookService()
        hook_config = HookWebhookSchema(
            url="https://example.com/webhook",  # type: ignore[arg-type]
        )

        with patch.object(service, "_make_request") as mock_request:
            mock_request.return_value = {"acknowledged": True}

            await service.execute_hook(
                hook_event="Stop",
                hook_config=hook_config,
                session_id="session-123",
                result_data={"is_error": False, "duration_ms": 5000},
            )

            call_args = mock_request.call_args
            payload = call_args.kwargs.get("json") or call_args.args[1]

            assert payload["hook_event"] == "Stop"
            assert payload["session_id"] == "session-123"


class TestHooksConfigIntegration:
    """Integration tests for HooksConfig with WebhookService."""

    @pytest.mark.anyio
    async def test_execute_hooks_from_config(self) -> None:
        """Test executing hooks from a HooksConfigSchema."""
        from apps.api.services.webhook import WebhookService

        service = WebhookService()
        hooks_config = HooksConfigSchema(
            PreToolUse=HookWebhookSchema(
                url="https://example.com/pre",  # type: ignore[arg-type]
            ),
            PostToolUse=HookWebhookSchema(
                url="https://example.com/post",  # type: ignore[arg-type]
            ),
        )

        with patch.object(service, "_make_request") as mock_request:
            mock_request.return_value = {"decision": "allow"}

            # Should find and execute PreToolUse hook
            if hooks_config.pre_tool_use:
                result = await service.execute_hook(
                    hook_event="PreToolUse",
                    hook_config=hooks_config.pre_tool_use,
                    session_id="session-1",
                    tool_name="Write",
                )
                assert result["decision"] == "allow"

    def test_get_hook_for_event(self) -> None:
        """Test getting hook configuration for specific event."""
        from apps.api.services.webhook import WebhookService

        service = WebhookService()
        hooks_config = HooksConfigSchema(
            PreToolUse=HookWebhookSchema(
                url="https://example.com/pre",  # type: ignore[arg-type]
            ),
            Stop=HookWebhookSchema(
                url="https://example.com/stop",  # type: ignore[arg-type]
            ),
        )

        pre_hook = service.get_hook_for_event(hooks_config, "PreToolUse")
        assert pre_hook is not None
        assert "pre" in str(pre_hook.url)

        post_hook = service.get_hook_for_event(hooks_config, "PostToolUse")
        assert post_hook is None

        stop_hook = service.get_hook_for_event(hooks_config, "Stop")
        assert stop_hook is not None
