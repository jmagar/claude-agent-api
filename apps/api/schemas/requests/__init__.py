"""Request schemas package.

Re-exports all request schemas for backward compatibility.
"""

# Config schemas (new module)
from apps.api.schemas.requests.config import (
    AgentDefinitionSchema,
    HooksConfigSchema,
    HookWebhookSchema,
    ImageContentSchema,
    McpServerConfigSchema,
    OutputFormatSchema,
    SandboxSettingsSchema,
    SdkPluginConfigSchema,
)

# QueryRequest (migrated to new module)
from apps.api.schemas.requests.query import QueryRequest

# Session schemas (migrated to new module)
from apps.api.schemas.requests.sessions import (
    AnswerRequest,
    ForkRequest,
    ResumeRequest,
)

# Control schemas (migrated from requests_old.py)
from apps.api.schemas.requests.control import (
    ControlRequest,
    RewindRequest,
)

__all__ = [
    # Config schemas
    "AgentDefinitionSchema",
    # Request schemas (from old module, to be migrated)
    "AnswerRequest",
    "ControlRequest",
    "ForkRequest",
    "HookWebhookSchema",
    "HooksConfigSchema",
    "ImageContentSchema",
    "McpServerConfigSchema",
    "OutputFormatSchema",
    "QueryRequest",
    "ResumeRequest",
    "RewindRequest",
    "SandboxSettingsSchema",
    "SdkPluginConfigSchema",
]
