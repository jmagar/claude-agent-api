"""OpenAI-compatible API schemas."""

from .requests import ChatCompletionRequest, OpenAIMessage
from .responses import (
    OpenAIChatCompletion,
    OpenAIChoice,
    OpenAIDelta,
    OpenAIError,
    OpenAIErrorDetails,
    OpenAIModelInfo,
    OpenAIModelList,
    OpenAIResponseMessage,
    OpenAIStreamChoice,
    OpenAIStreamChunk,
    OpenAIUsage,
)

__all__ = [
    "ChatCompletionRequest",
    "OpenAIChatCompletion",
    "OpenAIChoice",
    "OpenAIDelta",
    "OpenAIError",
    "OpenAIErrorDetails",
    "OpenAIMessage",
    "OpenAIModelInfo",
    "OpenAIModelList",
    "OpenAIResponseMessage",
    "OpenAIStreamChoice",
    "OpenAIStreamChunk",
    "OpenAIUsage",
]
