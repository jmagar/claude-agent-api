"""Unit tests for HookFacade."""

import pytest

from apps.api.services.agent.hook_facade import HookFacade
from apps.api.services.agent.hooks import HookExecutor
from apps.api.services.webhook import WebhookService


@pytest.mark.anyio
async def test_hook_facade_forwards_pre_tool_use() -> None:
    """Test hook facade delegates pre-tool-use hooks."""
    facade = HookFacade(executor=HookExecutor(WebhookService()))
    result = await facade.execute_pre_tool_use(None, "sid", "Tool")
    assert isinstance(result, dict)
