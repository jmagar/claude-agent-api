"""<summary>Facade for forwarding hook execution requests.</summary>"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from apps.api.schemas.requests.config import HooksConfigSchema
    from apps.api.services.agent.hooks import HookExecutor


class HookFacade:
    """<summary>Forward hook execution to a HookExecutor.</summary>"""

    def __init__(self, executor: "HookExecutor") -> None:
        """<summary>Initialize the facade.</summary>"""
        self._executor = executor

    async def execute_pre_tool_use(
        self,
        hooks_config: "HooksConfigSchema | None",
        session_id: str,
        tool_name: str,
        tool_input: dict[str, object] | None = None,
    ) -> dict[str, object]:
        """<summary>Forward PreToolUse hook.</summary>"""
        return await self._executor.execute_pre_tool_use(
            hooks_config,
            session_id,
            tool_name,
            tool_input,
        )

    async def execute_post_tool_use(
        self,
        hooks_config: "HooksConfigSchema | None",
        session_id: str,
        tool_name: str,
        tool_input: dict[str, object] | None = None,
        tool_result: dict[str, object] | None = None,
    ) -> dict[str, object]:
        """<summary>Forward PostToolUse hook.</summary>"""
        return await self._executor.execute_post_tool_use(
            hooks_config,
            session_id,
            tool_name,
            tool_input,
            tool_result,
        )

    async def execute_stop(
        self,
        hooks_config: "HooksConfigSchema | None",
        session_id: str,
        is_error: bool = False,
        duration_ms: int = 0,
        result: str | None = None,
    ) -> dict[str, object]:
        """<summary>Forward Stop hook.</summary>"""
        return await self._executor.execute_stop(
            hooks_config,
            session_id,
            is_error,
            duration_ms,
            result,
        )

    async def execute_subagent_stop(
        self,
        hooks_config: "HooksConfigSchema | None",
        session_id: str,
        subagent_name: str,
        is_error: bool = False,
        result: str | None = None,
    ) -> dict[str, object]:
        """<summary>Forward SubagentStop hook.</summary>"""
        return await self._executor.execute_subagent_stop(
            hooks_config,
            session_id,
            subagent_name,
            is_error,
            result,
        )

    async def execute_user_prompt_submit(
        self,
        hooks_config: "HooksConfigSchema | None",
        session_id: str,
        prompt: str,
    ) -> dict[str, object]:
        """<summary>Forward UserPromptSubmit hook.</summary>"""
        return await self._executor.execute_user_prompt_submit(
            hooks_config,
            session_id,
            prompt,
        )
