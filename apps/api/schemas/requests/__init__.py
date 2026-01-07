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

# Re-export from old location for now (will be migrated in later tasks)
from apps.api.schemas.requests_old import (
    AnswerRequest,
    ControlRequest,
    ForkRequest,
    QueryRequest,
    ResumeRequest,
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
