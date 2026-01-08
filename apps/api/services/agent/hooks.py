"""Webhook hook execution for agent service."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from apps.api.schemas.requests import HooksConfigSchema
    from apps.api.services.webhook import WebhookService


class HookExecutor:
    """Executes webhook-based hooks for agent lifecycle events."""

    def __init__(self, webhook_service: "WebhookService") -> None:
        """Initialize hook executor.

        Args:
            webhook_service: WebhookService instance for executing HTTP webhooks.
        """
        self._webhook_service = webhook_service

    async def execute_pre_tool_use(
        self,
        hooks_config: "HooksConfigSchema | None",
        session_id: str,
        tool_name: str,
        tool_input: dict[str, object] | None = None,
    ) -> dict[str, object]:
        """Execute PreToolUse webhook hook if configured.

        Args:
            hooks_config: Hooks configuration from request.
            session_id: Current session ID.
            tool_name: Name of tool being executed.
            tool_input: Tool input parameters.

        Returns:
            Webhook response with decision (allow/deny/ask).
        """
        if not hooks_config or not hooks_config.pre_tool_use:
            return {"decision": "allow"}

        return await self._webhook_service.execute_hook(
            hook_event="PreToolUse",
            hook_config=hooks_config.pre_tool_use,
            session_id=session_id,
            tool_name=tool_name,
            tool_input=tool_input,
        )

    async def execute_post_tool_use(
        self,
        hooks_config: "HooksConfigSchema | None",
        session_id: str,
        tool_name: str,
        tool_input: dict[str, object] | None = None,
        tool_result: dict[str, object] | None = None,
    ) -> dict[str, object]:
        """Execute PostToolUse webhook hook if configured.

        Args:
            hooks_config: Hooks configuration from request.
            session_id: Current session ID.
            tool_name: Name of tool that was executed.
            tool_input: Tool input parameters.
            tool_result: Result from tool execution.

        Returns:
            Webhook response.
        """
        if not hooks_config or not hooks_config.post_tool_use:
            return {"acknowledged": True}

        return await self._webhook_service.execute_hook(
            hook_event="PostToolUse",
            hook_config=hooks_config.post_tool_use,
            session_id=session_id,
            tool_name=tool_name,
            tool_input=tool_input,
            tool_result=tool_result,
        )

    async def execute_stop(
        self,
        hooks_config: "HooksConfigSchema | None",
        session_id: str,
        is_error: bool = False,
        duration_ms: int = 0,
        result: str | None = None,
    ) -> dict[str, object]:
        """Execute Stop webhook hook if configured.

        Args:
            hooks_config: Hooks configuration from request.
            session_id: Current session ID.
            is_error: Whether session ended with error.
            duration_ms: Session duration in milliseconds.
            result: Final result text.

        Returns:
            Webhook response.
        """
        if not hooks_config or not hooks_config.stop:
            return {"acknowledged": True}

        result_data: dict[str, object] = {
            "is_error": is_error,
            "duration_ms": duration_ms,
        }
        if result:
            result_data["result"] = result

        return await self._webhook_service.execute_hook(
            hook_event="Stop",
            hook_config=hooks_config.stop,
            session_id=session_id,
            result_data=result_data,
        )

    async def execute_subagent_stop(
        self,
        hooks_config: "HooksConfigSchema | None",
        session_id: str,
        subagent_name: str,
        is_error: bool = False,
        result: str | None = None,
    ) -> dict[str, object]:
        """Execute SubagentStop webhook hook if configured.

        Args:
            hooks_config: Hooks configuration from request.
            session_id: Current session ID.
            subagent_name: Name of subagent that stopped.
            is_error: Whether subagent ended with error.
            result: Subagent result.

        Returns:
            Webhook response.
        """
        if not hooks_config or not hooks_config.subagent_stop:
            return {"acknowledged": True}

        result_data: dict[str, object] = {
            "subagent_name": subagent_name,
            "is_error": is_error,
        }
        if result:
            result_data["result"] = result

        return await self._webhook_service.execute_hook(
            hook_event="SubagentStop",
            hook_config=hooks_config.subagent_stop,
            session_id=session_id,
            result_data=result_data,
        )

    async def execute_user_prompt_submit(
        self,
        hooks_config: "HooksConfigSchema | None",
        session_id: str,
        prompt: str,
    ) -> dict[str, object]:
        """Execute UserPromptSubmit webhook hook if configured.

        Args:
            hooks_config: Hooks configuration from request.
            session_id: Current session ID.
            prompt: User prompt being submitted.

        Returns:
            Webhook response with potential modified prompt.
        """
        if not hooks_config or not hooks_config.user_prompt_submit:
            return {"decision": "allow"}

        return await self._webhook_service.execute_hook(
            hook_event="UserPromptSubmit",
            hook_config=hooks_config.user_prompt_submit,
            session_id=session_id,
            tool_input={"prompt": prompt},
        )
