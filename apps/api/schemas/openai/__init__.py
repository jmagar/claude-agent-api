"""OpenAI-compatible API schemas."""

from .responses import (
    OpenAIChatCompletion,
    OpenAIChoice,
    OpenAIDelta,
    OpenAIError,
    OpenAIErrorDetails,
    OpenAIModelInfo,
    OpenAIModelList,
    OpenAIResponseMessage,
    OpenAIStreamChunk,
    OpenAIStreamChoice,
    OpenAIUsage,
)

__all__ = [
    "OpenAIChatCompletion",
    "OpenAIChoice",
    "OpenAIDelta",
    "OpenAIError",
    "OpenAIErrorDetails",
    "OpenAIModelInfo",
    "OpenAIModelList",
    "OpenAIResponseMessage",
    "OpenAIStreamChunk",
    "OpenAIStreamChoice",
    "OpenAIUsage",
]
