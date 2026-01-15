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
    OpenAIStreamChunk,
    OpenAIStreamChoice,
    OpenAIUsage,
)

__all__ = [
    "ChatCompletionRequest",
    "OpenAIMessage",
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
