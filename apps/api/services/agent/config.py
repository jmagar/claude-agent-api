"""Configuration for AgentService dependencies."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from apps.api.protocols import Cache
    from apps.api.services.checkpoint import CheckpointService
    from apps.api.services.mcp_config_injector import McpConfigInjector
    from apps.api.services.memory import MemoryService
    from apps.api.services.webhook import WebhookService


@dataclass
class AgentServiceConfig:
    """Configuration for AgentService optional dependencies.

    This config object groups optional dependencies to reduce constructor
    parameter count and improve maintainability.
    """

    webhook_service: "WebhookService | None" = None
    checkpoint_service: "CheckpointService | None" = None
    cache: "Cache | None" = None
    mcp_config_injector: "McpConfigInjector | None" = None
    memory_service: "MemoryService | None" = None
