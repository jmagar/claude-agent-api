"""Custom exception classes for the API.

Re-exports all exception classes for backward compatibility.
Import from this module or submodules as needed.
"""

from apps.api.exceptions.agent import (
    AgentError,
    HookError,
    ToolNotAllowedError,
)
from apps.api.exceptions.assistant import AssistantNotFoundError
from apps.api.exceptions.auth import (
    AuthenticationError,
    RateLimitError,
)
from apps.api.exceptions.base import APIError
from apps.api.exceptions.checkpoint import (
    CheckpointNotFoundError,
    InvalidCheckpointError,
)
from apps.api.exceptions.infra import (
    CacheError,
    DatabaseError,
    RequestTimeoutError,
    ServiceUnavailableError,
)
from apps.api.exceptions.mcp import McpShareNotFoundError
from apps.api.exceptions.session import (
    SessionCompletedError,
    SessionLockedError,
    SessionNotFoundError,
)
from apps.api.exceptions.tool_presets import ToolPresetNotFoundError
from apps.api.exceptions.validation import (
    StructuredOutputValidationError,
    ValidationError,
)

__all__ = [
    "APIError",
    "AgentError",
    "AssistantNotFoundError",
    "AuthenticationError",
    "CacheError",
    "CheckpointNotFoundError",
    "DatabaseError",
    "HookError",
    "InvalidCheckpointError",
    "McpShareNotFoundError",
    "RateLimitError",
    "RequestTimeoutError",
    "ServiceUnavailableError",
    "SessionCompletedError",
    "SessionLockedError",
    "SessionNotFoundError",
    "StructuredOutputValidationError",
    "ToolNotAllowedError",
    "ToolPresetNotFoundError",
    "ValidationError",
]
