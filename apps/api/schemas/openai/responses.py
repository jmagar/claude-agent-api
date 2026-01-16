"""OpenAI-compatible response TypedDict schemas."""

from typing import Literal, NotRequired, Required, TypedDict


class OpenAIDelta(TypedDict):
    """Delta object for streaming responses."""

    role: NotRequired[Literal["assistant"]]
    content: NotRequired[str]


class OpenAIStreamChoice(TypedDict):
    """Choice object for streaming responses."""

    index: Required[int]
    delta: Required[OpenAIDelta]
    finish_reason: Required[Literal["stop", "length", "error"] | None]


class OpenAIStreamChunk(TypedDict):
    """Streaming chunk response."""

    id: Required[str]
    object: Required[Literal["chat.completion.chunk"]]
    created: Required[int]
    model: Required[str]
    choices: Required[list[OpenAIStreamChoice]]


class OpenAIResponseMessage(TypedDict):
    """Message object for non-streaming responses."""

    role: Required[Literal["assistant"]]
    content: Required[str]


class OpenAIChoice(TypedDict):
    """Choice object for non-streaming responses."""

    index: Required[int]
    message: Required[OpenAIResponseMessage]
    finish_reason: Required[Literal["stop", "length", "error"] | None]


class OpenAIUsage(TypedDict):
    """Token usage statistics."""

    prompt_tokens: Required[int]
    completion_tokens: Required[int]
    total_tokens: Required[int]


class OpenAIChatCompletion(TypedDict):
    """Non-streaming chat completion response."""

    id: Required[str]
    object: Required[Literal["chat.completion"]]
    created: Required[int]
    model: Required[str]
    choices: Required[list[OpenAIChoice]]
    usage: Required[OpenAIUsage]


class OpenAIModelInfo(TypedDict):
    """Model information object."""

    id: Required[str]
    object: Required[Literal["model"]]
    created: Required[int]
    owned_by: Required[str]


class OpenAIModelList(TypedDict):
    """List of available models."""

    object: Required[Literal["list"]]
    data: Required[list[OpenAIModelInfo]]


class OpenAIErrorDetails(TypedDict):
    """Error details object."""

    message: Required[str]
    type: Required[str]
    code: Required[str | None]


class OpenAIError(TypedDict):
    """Error response wrapper."""

    error: Required[OpenAIErrorDetails]
