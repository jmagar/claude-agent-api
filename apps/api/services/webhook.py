"""Webhook service for executing HTTP callbacks for hook events.

This module provides the WebhookService that handles HTTP callbacks
for agent lifecycle hooks (PreToolUse, PostToolUse, Stop, etc.).
"""

import asyncio
import re
from typing import Literal

import httpx
import structlog

from apps.api.schemas.requests.config import HooksConfigSchema, HookWebhookSchema

logger = structlog.get_logger()


# Type definitions for webhook payloads and responses
HookEventType = Literal[
    "PreToolUse",
    "PostToolUse",
    "Stop",
    "SubagentStop",
    "UserPromptSubmit",
    "PreCompact",
    "Notification",
]

DecisionType = Literal["allow", "deny", "ask"]


class WebhookPayload:
    """Type-safe structure for webhook request payloads."""

    hook_event: HookEventType
    session_id: str
    tool_name: str | None
    tool_input: dict[str, object] | None
    tool_result: dict[str, object] | None
    result_data: dict[str, object] | None


class WebhookResponseData:
    """Type-safe structure for webhook responses."""

    decision: DecisionType
    reason: str | None
    modified_input: dict[str, object] | None


class WebhookHttpError(Exception):
    """Exception for HTTP errors from webhook calls."""

    def __init__(self, status_code: int, message: str) -> None:
        """Initialize WebhookHttpError.

        Args:
            status_code: HTTP status code from the response.
            message: Error message describing the failure.
        """
        self.status_code = status_code
        self.message = message
        super().__init__(f"HTTP {status_code}: {message}")


class WebhookService:
    """Service for executing webhook callbacks for hook events.

    This service handles HTTP POST requests to webhook URLs configured
    for various hook events (PreToolUse, PostToolUse, Stop, etc.).
    It manages timeouts, error handling, and response processing.
    """

    def __init__(
        self,
        http_client: httpx.AsyncClient | None = None,
        default_timeout: float = 30.0,
    ) -> None:
        """Initialize WebhookService.

        Args:
            http_client: Optional custom HTTP client for making requests.
                         If not provided, a new client will be created per request.
            default_timeout: Default timeout in seconds for webhook requests.
        """
        self._http_client = http_client
        self._default_timeout = default_timeout
        self._logger = logger.bind(service="webhook")

    async def execute_hook(
        self,
        hook_event: HookEventType,
        hook_config: HookWebhookSchema,
        session_id: str,
        tool_name: str | None = None,
        tool_input: dict[str, object] | None = None,
        tool_result: dict[str, object] | None = None,
        result_data: dict[str, object] | None = None,
    ) -> dict[str, object]:
        """Execute a webhook callback for a hook event.

        Args:
            hook_event: Type of hook event (PreToolUse, PostToolUse, etc.).
            hook_config: Webhook configuration with URL, headers, timeout.
            session_id: ID of the current session.
            tool_name: Name of the tool being used (for tool-related hooks).
            tool_input: Input parameters for the tool (for PreToolUse).
            tool_result: Result from tool execution (for PostToolUse).
            result_data: Result data (for Stop hook).

        Returns:
            Dictionary containing the webhook response with 'decision' field.
            On error/timeout, returns default allow response.
        """
        # Check if hook should be executed based on matcher
        if tool_name and not self.should_execute_hook(hook_config, tool_name):
            return {"decision": "allow", "reason": "Tool did not match hook filter"}

        # Build the webhook payload
        payload = self._build_payload(
            hook_event=hook_event,
            session_id=session_id,
            tool_name=tool_name,
            tool_input=tool_input,
            tool_result=tool_result,
            result_data=result_data,
        )

        try:
            response = await self._make_request(
                url=str(hook_config.url),
                json=payload,
                headers=hook_config.headers,
                timeout=hook_config.timeout,
            )
            return response
        except TimeoutError:
            self._logger.warning(
                "webhook_timeout",
                hook_event=hook_event,
                url=str(hook_config.url),
                timeout=hook_config.timeout,
            )
            return {
                "decision": "allow",
                "reason": f"Webhook timeout after {hook_config.timeout}s",
            }
        except (ConnectionError, httpx.RequestError) as e:
            self._logger.warning(
                "webhook_connection_error",
                hook_event=hook_event,
                url=str(hook_config.url),
                error=str(e),
            )
            return {
                "decision": "allow",
                "reason": f"Webhook connection error: {e!s}",
            }
        except WebhookHttpError as e:
            self._logger.warning(
                "webhook_http_error",
                hook_event=hook_event,
                url=str(hook_config.url),
                status_code=e.status_code,
                error=e.message,
            )
            return {
                "decision": "allow",
                "reason": f"Webhook HTTP error: {e.message}",
            }
        except ValueError as e:
            self._logger.warning(
                "webhook_json_error",
                hook_event=hook_event,
                url=str(hook_config.url),
                error=str(e),
            )
            return {
                "decision": "allow",
                "reason": f"Invalid JSON response: {e!s}",
            }

    def should_execute_hook(
        self,
        hook_config: HookWebhookSchema,
        tool_name: str,
    ) -> bool:
        """Check if hook should be executed based on matcher pattern.

        Args:
            hook_config: Webhook configuration with optional matcher.
            tool_name: Name of the tool to check against matcher.

        Returns:
            True if hook should be executed, False otherwise.
        """
        if hook_config.matcher is None:
            # No matcher means match all tools
            return True

        try:
            pattern = re.compile(hook_config.matcher)
            return pattern.match(tool_name) is not None
        except re.error as e:
            self._logger.warning(
                "invalid_matcher_regex",
                matcher=hook_config.matcher,
                error=str(e),
            )
            # On invalid regex, default to matching (safer)
            return True

    def get_hook_for_event(
        self,
        hooks_config: HooksConfigSchema,
        event_type: HookEventType,
    ) -> HookWebhookSchema | None:
        """Get the hook configuration for a specific event type.

        Args:
            hooks_config: Complete hooks configuration.
            event_type: Type of hook event to get configuration for.

        Returns:
            HookWebhookSchema for the event, or None if not configured.
        """
        event_map: dict[HookEventType, HookWebhookSchema | None] = {
            "PreToolUse": hooks_config.pre_tool_use,
            "PostToolUse": hooks_config.post_tool_use,
            "Stop": hooks_config.stop,
            "SubagentStop": hooks_config.subagent_stop,
            "UserPromptSubmit": hooks_config.user_prompt_submit,
            "PreCompact": hooks_config.pre_compact,
            "Notification": hooks_config.notification,
        }
        return event_map.get(event_type)

    def _build_payload(
        self,
        hook_event: HookEventType,
        session_id: str,
        tool_name: str | None = None,
        tool_input: dict[str, object] | None = None,
        tool_result: dict[str, object] | None = None,
        result_data: dict[str, object] | None = None,
    ) -> dict[str, object]:
        """Build the webhook request payload.

        Args:
            hook_event: Type of hook event.
            session_id: ID of the current session.
            tool_name: Name of the tool (if applicable).
            tool_input: Tool input parameters (if applicable).
            tool_result: Tool execution result (if applicable).
            result_data: Session result data (if applicable).

        Returns:
            Dictionary payload for the webhook request.
        """
        payload: dict[str, object] = {
            "hook_event": hook_event,
            "session_id": session_id,
        }

        if tool_name is not None:
            payload["tool_name"] = tool_name

        if tool_input is not None:
            payload["tool_input"] = tool_input

        if tool_result is not None:
            payload["tool_result"] = tool_result

        if result_data is not None:
            payload["result_data"] = result_data

        return payload

    async def _make_request(
        self,
        url: str,
        json: dict[str, object],
        headers: dict[str, str],
        timeout: int,
    ) -> dict[str, object]:
        """Make HTTP POST request to webhook URL.

        Args:
            url: Webhook URL to call.
            json: JSON payload to send.
            headers: HTTP headers to include.
            timeout: Request timeout in seconds.

        Returns:
            Parsed JSON response from webhook.

        Raises:
            asyncio.TimeoutError: If request times out.
            ConnectionError: If connection fails.
            WebhookHttpError: If HTTP status indicates error.
            ValueError: If response is not valid JSON.
        """
        request_headers = {
            "Content-Type": "application/json",
            **headers,
        }

        if self._http_client:
            # Use provided client
            response = await asyncio.wait_for(
                self._http_client.post(
                    url,
                    json=json,
                    headers=request_headers,
                ),
                timeout=timeout,
            )
        else:
            # Create a new client for this request
            async with httpx.AsyncClient() as client:
                response = await asyncio.wait_for(
                    client.post(
                        url,
                        json=json,
                        headers=request_headers,
                    ),
                    timeout=timeout,
                )

        if response.status_code >= 400:
            raise WebhookHttpError(response.status_code, response.text)

        try:
            return response.json()  # type: ignore[no-any-return]
        except ValueError as e:
            raise ValueError(f"Invalid JSON response: {e}") from e


# Factory function for dependency injection
def create_webhook_service(
    http_client: httpx.AsyncClient | None = None,
) -> WebhookService:
    """Create a WebhookService instance.

    Args:
        http_client: Optional HTTP client for making requests.

    Returns:
        Configured WebhookService instance.
    """
    return WebhookService(http_client=http_client)
