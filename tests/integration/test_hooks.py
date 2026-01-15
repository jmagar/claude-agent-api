"""Integration tests for webhook hooks functionality (User Story 7).

These tests verify the HTTP webhook hook system that allows intercepting
agent execution at key points (PreToolUse, PostToolUse, Stop, etc.).
"""

from typing import cast

import pytest
from httpx import AsyncClient
from pydantic import HttpUrl

from apps.api.schemas.requests.config import HooksConfigSchema, HookWebhookSchema
from apps.api.schemas.requests.query import QueryRequest


def _http_url(value: str) -> HttpUrl:
    return cast("HttpUrl", value)


class TestHooksConfigValidation:
    """Tests for hooks configuration in query requests."""

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_query_with_pre_tool_use_hook_accepted(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_claude_sdk: None,
    ) -> None:
        """Test that PreToolUse hook configuration is accepted."""
        response = await async_client.post(
            "/api/v1/query",
            json={
                "prompt": "List files",
                "hooks": {
                    "PreToolUse": {
                        "url": "https://example.com/webhooks/pre-tool",
                        "timeout": 30,
                    }
                },
            },
            headers=auth_headers,
        )
        # Should accept the request (stream starts) - status 200 for SSE
        assert response.status_code == 200

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_query_with_post_tool_use_hook_accepted(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_claude_sdk: None,
    ) -> None:
        """Test that PostToolUse hook configuration is accepted."""
        response = await async_client.post(
            "/api/v1/query",
            json={
                "prompt": "List files",
                "hooks": {
                    "PostToolUse": {
                        "url": "https://example.com/webhooks/post-tool",
                        "timeout": 30,
                    }
                },
            },
            headers=auth_headers,
        )
        assert response.status_code == 200

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_query_with_stop_hook_accepted(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_claude_sdk: None,
    ) -> None:
        """Test that Stop hook configuration is accepted."""
        response = await async_client.post(
            "/api/v1/query",
            json={
                "prompt": "List files",
                "hooks": {
                    "Stop": {
                        "url": "https://example.com/webhooks/stop",
                        "timeout": 30,
                    }
                },
            },
            headers=auth_headers,
        )
        assert response.status_code == 200

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_query_with_subagent_stop_hook_accepted(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_claude_sdk: None,
    ) -> None:
        """Test that SubagentStop hook configuration is accepted."""
        response = await async_client.post(
            "/api/v1/query",
            json={
                "prompt": "List files",
                "hooks": {
                    "SubagentStop": {
                        "url": "https://example.com/webhooks/subagent-stop",
                        "timeout": 30,
                    }
                },
            },
            headers=auth_headers,
        )
        assert response.status_code == 200

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_query_with_user_prompt_submit_hook_accepted(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_claude_sdk: None,
    ) -> None:
        """Test that UserPromptSubmit hook configuration is accepted."""
        response = await async_client.post(
            "/api/v1/query",
            json={
                "prompt": "List files",
                "hooks": {
                    "UserPromptSubmit": {
                        "url": "https://example.com/webhooks/prompt-submit",
                        "timeout": 30,
                    }
                },
            },
            headers=auth_headers,
        )
        assert response.status_code == 200

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_query_with_multiple_hooks_accepted(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_claude_sdk: None,
    ) -> None:
        """Test that multiple hooks can be configured together."""
        response = await async_client.post(
            "/api/v1/query",
            json={
                "prompt": "List files",
                "hooks": {
                    "PreToolUse": {
                        "url": "https://example.com/webhooks/pre-tool",
                        "timeout": 30,
                    },
                    "PostToolUse": {
                        "url": "https://example.com/webhooks/post-tool",
                        "timeout": 30,
                    },
                    "Stop": {
                        "url": "https://example.com/webhooks/stop",
                        "timeout": 30,
                    },
                },
            },
            headers=auth_headers,
        )
        assert response.status_code == 200

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_query_with_hook_headers_accepted(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_claude_sdk: None,
    ) -> None:
        """Test that hooks with custom headers are accepted."""
        response = await async_client.post(
            "/api/v1/query",
            json={
                "prompt": "List files",
                "hooks": {
                    "PreToolUse": {
                        "url": "https://example.com/webhooks/pre-tool",
                        "headers": {
                            "Authorization": "Bearer secret-token",
                            "X-Custom-Header": "custom-value",
                        },
                        "timeout": 30,
                    }
                },
            },
            headers=auth_headers,
        )
        assert response.status_code == 200

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_query_with_hook_matcher_accepted(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_claude_sdk: None,
    ) -> None:
        """Test that hooks with matcher regex patterns are accepted."""
        response = await async_client.post(
            "/api/v1/query",
            json={
                "prompt": "List files",
                "hooks": {
                    "PreToolUse": {
                        "url": "https://example.com/webhooks/pre-tool",
                        "timeout": 30,
                        "matcher": "Write|Edit|Bash",
                    }
                },
            },
            headers=auth_headers,
        )
        assert response.status_code == 200


class TestHooksConfigSchemaValidation:
    """Tests for HooksConfigSchema validation."""

    def test_hooks_config_with_valid_pre_tool_use(self) -> None:
        """Test creating HooksConfigSchema with valid PreToolUse hook."""
        config = HooksConfigSchema(
            PreToolUse=HookWebhookSchema(
                url=_http_url("https://example.com/hook"),
                timeout=30,
            )
        )
        assert config.pre_tool_use is not None
        # HttpUrl may or may not add trailing slash - check that base URL is present
        assert "example.com/hook" in str(config.pre_tool_use.url)

    def test_hooks_config_with_all_hook_types(self) -> None:
        """Test creating HooksConfigSchema with all hook types."""
        config = HooksConfigSchema(
            PreToolUse=HookWebhookSchema(url=_http_url("https://example.com/pre")),
            PostToolUse=HookWebhookSchema(url=_http_url("https://example.com/post")),
            Stop=HookWebhookSchema(url=_http_url("https://example.com/stop")),
            SubagentStop=HookWebhookSchema(
                url=_http_url("https://example.com/subagent")
            ),
            UserPromptSubmit=HookWebhookSchema(
                url=_http_url("https://example.com/prompt")
            ),
        )
        assert config.pre_tool_use is not None
        assert config.post_tool_use is not None
        assert config.stop is not None
        assert config.subagent_stop is not None
        assert config.user_prompt_submit is not None

    def test_hook_webhook_schema_default_timeout(self) -> None:
        """Test that HookWebhookSchema has default timeout of 30."""
        hook = HookWebhookSchema(url=_http_url("https://example.com/hook"))
        assert hook.timeout == 30

    def test_hook_webhook_schema_timeout_bounds(self) -> None:
        """Test timeout validation bounds (1-300)."""
        # Valid lower bound
        hook = HookWebhookSchema(
            url=_http_url("https://example.com/hook"),
            timeout=1,
        )
        assert hook.timeout == 1

        # Valid upper bound
        hook = HookWebhookSchema(
            url=_http_url("https://example.com/hook"),
            timeout=300,
        )
        assert hook.timeout == 300

        # Below lower bound
        with pytest.raises(ValueError):
            HookWebhookSchema(
                url=_http_url("https://example.com/hook"),
                timeout=0,
            )

        # Above upper bound
        with pytest.raises(ValueError):
            HookWebhookSchema(
                url=_http_url("https://example.com/hook"),
                timeout=301,
            )

    def test_hook_webhook_schema_requires_valid_url(self) -> None:
        """Test that HookWebhookSchema requires a valid URL."""
        with pytest.raises(ValueError):
            HookWebhookSchema(url=_http_url("not-a-valid-url"))

    def test_hook_webhook_schema_with_matcher_regex(self) -> None:
        """Test HookWebhookSchema with matcher regex pattern."""
        hook = HookWebhookSchema(
            url=_http_url("https://example.com/hook"),
            matcher="Write|Edit|Bash",
        )
        assert hook.matcher == "Write|Edit|Bash"

    def test_hooks_in_query_request(self) -> None:
        """Test that hooks can be included in QueryRequest."""
        request = QueryRequest(
            prompt="Test prompt",
            hooks=HooksConfigSchema(
                PreToolUse=HookWebhookSchema(
                    url=_http_url("https://example.com/hook"),
                    timeout=30,
                )
            ),
        )
        assert request.hooks is not None
        assert request.hooks.pre_tool_use is not None


class TestResumeWithHooks:
    """Tests for hooks in session resume requests."""

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_resume_with_hooks_accepted(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_session_id: str,
        mock_claude_sdk: None,
    ) -> None:
        """Test that hooks can be provided when resuming a session."""
        response = await async_client.post(
            f"/api/v1/sessions/{mock_session_id}/resume",
            json={
                "prompt": "Continue with hooks",
                "hooks": {
                    "PreToolUse": {
                        "url": "https://example.com/webhooks/pre-tool",
                        "timeout": 30,
                    }
                },
            },
            headers=auth_headers,
        )
        # Should accept the resume request with hooks
        assert response.status_code == 200

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_resume_with_hooks_override(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_session_id: str,
        mock_claude_sdk: None,
    ) -> None:
        """Test that hooks can override previous session hooks."""
        response = await async_client.post(
            f"/api/v1/sessions/{mock_session_id}/resume",
            json={
                "prompt": "Continue with different hooks",
                "hooks": {
                    "PreToolUse": {
                        "url": "https://new-webhook.example.com/hook",
                        "timeout": 60,
                    }
                },
            },
            headers=auth_headers,
        )
        assert response.status_code == 200


class TestForkWithHooks:
    """Tests for hooks in session fork requests."""

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_fork_with_hooks_accepted(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_session_id: str,
        mock_claude_sdk: None,
    ) -> None:
        """Test that hooks can be provided when forking a session."""
        response = await async_client.post(
            f"/api/v1/sessions/{mock_session_id}/fork",
            json={
                "prompt": "Fork with hooks",
                "hooks": {
                    "PreToolUse": {
                        "url": "https://example.com/webhooks/pre-tool",
                        "timeout": 30,
                    },
                    "Stop": {
                        "url": "https://example.com/webhooks/stop",
                        "timeout": 30,
                    },
                },
            },
            headers=auth_headers,
        )
        # Should accept the fork request with hooks
        assert response.status_code == 200


class TestHookInvalidConfigurations:
    """Tests for invalid hook configurations that should be rejected."""

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_invalid_hook_url_rejected(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_claude_sdk: None,
    ) -> None:
        """Test that invalid webhook URLs are rejected."""
        response = await async_client.post(
            "/api/v1/query",
            json={
                "prompt": "List files",
                "hooks": {
                    "PreToolUse": {
                        "url": "not-a-valid-url",
                        "timeout": 30,
                    }
                },
            },
            headers=auth_headers,
        )
        assert response.status_code == 422

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_timeout_below_minimum_rejected(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_claude_sdk: None,
    ) -> None:
        """Test that timeout below 1 second is rejected."""
        response = await async_client.post(
            "/api/v1/query",
            json={
                "prompt": "List files",
                "hooks": {
                    "PreToolUse": {
                        "url": "https://example.com/hook",
                        "timeout": 0,
                    }
                },
            },
            headers=auth_headers,
        )
        assert response.status_code == 422

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_timeout_above_maximum_rejected(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_claude_sdk: None,
    ) -> None:
        """Test that timeout above 300 seconds is rejected."""
        response = await async_client.post(
            "/api/v1/query",
            json={
                "prompt": "List files",
                "hooks": {
                    "PreToolUse": {
                        "url": "https://example.com/hook",
                        "timeout": 301,
                    }
                },
            },
            headers=auth_headers,
        )
        assert response.status_code == 422

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_invalid_hook_type_is_ignored(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_claude_sdk: None,
    ) -> None:
        """Test that invalid hook types are ignored by Pydantic."""
        response = await async_client.post(
            "/api/v1/query",
            json={
                "prompt": "List files",
                "hooks": {
                    "InvalidHookType": {
                        "url": "https://example.com/hook",
                        "timeout": 30,
                    }
                },
            },
            headers=auth_headers,
        )
        # Pydantic ignores unknown fields by default
        assert response.status_code == 200
