"""OpenAI-compatible response TypedDict schemas."""

from typing import Literal, Required, TypedDict

# =============================================================================
# Tool Call Response Types
# =============================================================================


class OpenAIFunctionCallResponse(TypedDict):
    """Function call details in a tool_call response."""

    name: Required[str]
    arguments: Required[str]  # JSON string


class OpenAIToolCallResponse(TypedDict):
    """Tool call in assistant response."""

    id: Required[str]
    type: Required[Literal["function"]]
    function: Required[OpenAIFunctionCallResponse]


# =============================================================================
# Streaming Delta Types
# =============================================================================


class OpenAIFunctionCallDelta(TypedDict, total=False):
    """Delta for function call in streaming."""

    name: str
    arguments: str


class OpenAIToolCallDelta(TypedDict, total=False):
    """Tool call delta in streaming response."""

    index: Required[int]
    id: str
    type: Literal["function"]
    function: OpenAIFunctionCallDelta


class OpenAIDelta(TypedDict, total=False):
    """Delta object for streaming responses."""

    role: Literal["assistant"]
    content: str
    tool_calls: list[OpenAIToolCallDelta]


class OpenAIStreamChoice(TypedDict):
    """Choice object for streaming responses."""

    index: Required[int]
    delta: Required[OpenAIDelta]
    finish_reason: Required[Literal["stop", "length", "tool_calls", "error"] | None]


class OpenAIStreamChunk(TypedDict):
    """Streaming chunk response."""

    id: Required[str]
    object: Required[Literal["chat.completion.chunk"]]
    created: Required[int]
    model: Required[str]
    choices: Required[list[OpenAIStreamChoice]]


# =============================================================================
# Non-Streaming Response Types
# =============================================================================


class OpenAIResponseMessage(TypedDict, total=False):
    """Message object for non-streaming responses."""

    role: Required[Literal["assistant"]]
    content: str | None
    tool_calls: list[OpenAIToolCallResponse]


class OpenAIChoice(TypedDict):
    """Choice object for non-streaming responses."""

    index: Required[int]
    message: Required[OpenAIResponseMessage]
    finish_reason: Required[Literal["stop", "length", "tool_calls", "error"] | None]


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
