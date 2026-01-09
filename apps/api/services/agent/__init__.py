"""Agent service package.

This package contains the AgentService and supporting modules
for interacting with the Claude Agent SDK.
"""

from apps.api.services.agent.handlers import MessageHandler
from apps.api.services.agent.hooks import HookExecutor
from apps.api.services.agent.options import OptionsBuilder
from apps.api.services.agent.service import AgentService
from apps.api.services.agent.types import QueryResponseDict, StreamContext
from apps.api.services.agent.utils import (
    detect_slash_command,
    resolve_env_dict,
    resolve_env_var,
)

__all__ = [
    "AgentService",
    "HookExecutor",
    "MessageHandler",
    "OptionsBuilder",
    "QueryResponseDict",
    "StreamContext",
    "detect_slash_command",
    "resolve_env_dict",
    "resolve_env_var",
]
