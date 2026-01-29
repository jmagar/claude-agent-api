"""Unit tests for HookFacade."""

from typing import cast
from unittest.mock import AsyncMock

import pytest

from apps.api.services.agent.hook_facade import HookFacade
from apps.api.services.agent.hooks import HookExecutor
from apps.api.services.webhook import WebhookService


@pytest.mark.anyio
async def test_hook_facade_forwards_pre_tool_use() -> None:
    """Test hook facade delegates pre-tool-use hooks."""
    mock_webhook_service = AsyncMock(spec=WebhookService)
    mock_executor = AsyncMock(spec=HookExecutor)
    mock_executor._webhook_service = mock_webhook_service
    mock_executor.execute_pre_tool_use.return_value = {"decision": "allow"}

    facade = HookFacade(executor=cast("HookExecutor", mock_executor))
    result = await facade.execute_pre_tool_use(None, "sid", "Tool")

    mock_executor.execute_pre_tool_use.assert_called_once_with(
        None,
        "sid",
        "Tool",
        None,
    )
    assert result == {"decision": "allow"}
