"""OpenAI-compatible tool calling schemas.

This module defines TypedDict schemas for OpenAI function/tool calling,
including request parameters (tools, tool_choice) and response structures
(tool_calls, tool messages).
"""

from typing import Literal, NotRequired, Required, TypedDict


# =============================================================================
# Tool Definition Schemas (Request)
# =============================================================================


class OpenAIFunctionParameters(TypedDict, total=False):
    """JSON Schema for function parameters.

    This follows JSON Schema spec with OpenAI-specific conventions.
    """

    type: Required[Literal["object"]]
    properties: dict[str, dict[str, object]]
    required: list[str]
    additionalProperties: bool  # Must be False for strict mode


class OpenAIFunctionDefinition(TypedDict):
    """Function definition within a tool.

    Defines the function name, description, and parameter schema.
    """

    name: Required[str]
    description: NotRequired[str]
    parameters: NotRequired[OpenAIFunctionParameters]
    strict: NotRequired[bool]  # Enable strict mode for schema compliance


class OpenAITool(TypedDict):
    """Tool definition for chat completion requests.

    OpenAI uses a wrapper object with type="function" for tools.
    """

    type: Required[Literal["function"]]
    function: Required[OpenAIFunctionDefinition]


class OpenAIToolChoiceFunction(TypedDict):
    """Specific function to force when using tool_choice object."""

    name: Required[str]


class OpenAIToolChoiceObject(TypedDict):
    """Object form of tool_choice to force a specific function."""

    type: Required[Literal["function"]]
    function: Required[OpenAIToolChoiceFunction]


# tool_choice can be string ("auto", "none", "required") or object
OpenAIToolChoice = Literal["auto", "none", "required"] | OpenAIToolChoiceObject


# =============================================================================
# Tool Call Schemas (Response)
# =============================================================================


class OpenAIFunctionCall(TypedDict):
    """Function call details in a tool_call.

    Note: arguments is a JSON string that must be parsed.
    """

    name: Required[str]
    arguments: Required[str]  # JSON string, NOT parsed object


class OpenAIToolCall(TypedDict):
    """Tool call in assistant response.

    Represents a single function the model wants to invoke.
    """

    id: Required[str]  # Format: call_*
    type: Required[Literal["function"]]
    function: Required[OpenAIFunctionCall]


# =============================================================================
# Tool Result Message Schema (Request for follow-up)
# =============================================================================


class OpenAIToolResultMessage(TypedDict):
    """Tool result message to send back after execution.

    This is a message with role="tool" containing the function result.
    """

    role: Required[Literal["tool"]]
    tool_call_id: Required[str]  # Must match id from tool_call
    name: NotRequired[str]  # Function name (recommended)
    content: Required[str]  # Result as string (typically JSON)


# =============================================================================
# Streaming Tool Call Schemas
# =============================================================================


class OpenAIFunctionCallDelta(TypedDict, total=False):
    """Delta for function call in streaming.

    During streaming, name appears first, then arguments accumulate.
    """

    name: str
    arguments: str


class OpenAIToolCallDelta(TypedDict):
    """Tool call delta in streaming response.

    The index field identifies which tool_call this delta belongs to.
    """

    index: Required[int]
    id: NotRequired[str]  # Only in first chunk for this index
    type: NotRequired[Literal["function"]]  # Only in first chunk
    function: NotRequired[OpenAIFunctionCallDelta]


# =============================================================================
# Extended Response Message with Tool Calls
# =============================================================================


class OpenAIResponseMessageWithTools(TypedDict):
    """Assistant message that may contain tool calls.

    When tool_calls is present, content is typically null.
    """

    role: Required[Literal["assistant"]]
    content: Required[str | None]
    tool_calls: NotRequired[list[OpenAIToolCall]]


class OpenAIChoiceWithTools(TypedDict):
    """Choice object that may contain tool calls.

    finish_reason is "tool_calls" when model requests tool execution.
    """

    index: Required[int]
    message: Required[OpenAIResponseMessageWithTools]
    finish_reason: Required[Literal["stop", "length", "tool_calls", "error"] | None]


# =============================================================================
# Extended Delta with Tool Calls (Streaming)
# =============================================================================


class OpenAIDeltaWithTools(TypedDict, total=False):
    """Delta object for streaming that may include tool calls."""

    role: Literal["assistant"]
    content: str
    tool_calls: list[OpenAIToolCallDelta]


class OpenAIStreamChoiceWithTools(TypedDict):
    """Streaming choice that may contain tool call deltas."""

    index: Required[int]
    delta: Required[OpenAIDeltaWithTools]
    finish_reason: Required[Literal["stop", "length", "tool_calls", "error"] | None]
