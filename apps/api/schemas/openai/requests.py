"""OpenAI-compatible request Pydantic schemas."""

from typing import Any, Literal

from pydantic import BaseModel, Field


class OpenAIFunctionParametersModel(BaseModel):
    """JSON Schema for function parameters (Pydantic version for validation)."""

    type: Literal["object"] = "object"
    properties: dict[str, dict[str, Any]] = Field(default_factory=dict)
    required: list[str] = Field(default_factory=list)
    additionalProperties: bool = True  # noqa: N815 - matches OpenAI spec


class OpenAIFunctionModel(BaseModel):
    """Function definition within a tool (Pydantic version)."""

    name: str = Field(..., min_length=1)
    description: str | None = None
    parameters: OpenAIFunctionParametersModel | None = None
    strict: bool | None = None


class OpenAIToolModel(BaseModel):
    """Tool definition for chat completion requests (Pydantic version)."""

    type: Literal["function"] = "function"
    function: OpenAIFunctionModel


class OpenAIToolChoiceFunctionModel(BaseModel):
    """Specific function to force."""

    name: str


class OpenAIToolChoiceObjectModel(BaseModel):
    """Object form of tool_choice."""

    type: Literal["function"] = "function"
    function: OpenAIToolChoiceFunctionModel


class OpenAIToolCallModel(BaseModel):
    """Tool call for assistant messages in conversation history."""

    id: str
    type: Literal["function"] = "function"
    function: "OpenAIFunctionCallModel"


class OpenAIFunctionCallModel(BaseModel):
    """Function call details."""

    name: str
    arguments: str  # JSON string


class OpenAIMessage(BaseModel):
    """Message object for chat completion requests.

    Supports system, user, assistant (with optional tool_calls), and tool messages.
    """

    role: Literal["system", "user", "assistant", "tool"]
    content: str | None = None
    # For assistant messages with tool calls
    tool_calls: list[OpenAIToolCallModel] | None = None
    # For tool result messages
    tool_call_id: str | None = None
    name: str | None = None  # Function name for tool results


class ChatCompletionRequest(BaseModel):
    """Chat completion request schema.

    Validates incoming OpenAI-compatible chat completion requests.
    """

    model: str = Field(..., min_length=1)
    messages: list[OpenAIMessage] = Field(..., min_length=1)
    temperature: float | None = Field(default=None, ge=0, le=2)
    max_tokens: int | None = None
    top_p: float | None = None
    stop: list[str] | str | None = None
    stream: bool = False
    user: str | None = None
    # Tool calling parameters
    tools: list[OpenAIToolModel] | None = None
    tool_choice: Literal["auto", "none", "required"] | OpenAIToolChoiceObjectModel | None = None
    parallel_tool_calls: bool = True
