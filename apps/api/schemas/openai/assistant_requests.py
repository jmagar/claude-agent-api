"""OpenAI Assistants API Pydantic request schemas.

These schemas validate incoming requests for the Assistants API endpoints,
following OpenAI's API specification with strict type safety.
"""

from typing import Literal, TypedDict

from pydantic import BaseModel, Field


# =============================================================================
# Tool Types for Requests (TypedDict for flexibility)
# =============================================================================


class AssistantToolCodeInterpreter(TypedDict):
    """Code interpreter tool definition for requests."""

    type: Literal["code_interpreter"]


class AssistantToolFileSearch(TypedDict, total=False):
    """File search tool definition for requests."""

    type: Literal["file_search"]


class FunctionParameters(TypedDict, total=False):
    """JSON Schema for function parameters."""

    type: str
    properties: dict[str, dict[str, str | list[str] | bool | int]]
    required: list[str]


class FunctionDefinition(TypedDict, total=False):
    """Function definition for tool."""

    name: str
    description: str
    parameters: FunctionParameters


class AssistantToolFunction(TypedDict):
    """Function tool definition for requests."""

    type: Literal["function"]
    function: FunctionDefinition


# Union type for tools in requests
AssistantToolRequest = (
    AssistantToolCodeInterpreter | AssistantToolFileSearch | AssistantToolFunction
)


# =============================================================================
# Message Types for Requests
# =============================================================================


class ThreadMessageRequest(TypedDict, total=False):
    """Message to include in thread creation."""

    role: Literal["user", "assistant"]
    content: str
    metadata: dict[str, str]
    attachments: list[dict[str, str | list[dict[str, str]]]]


class ThreadRequest(TypedDict, total=False):
    """Thread configuration for combined create-and-run."""

    messages: list[ThreadMessageRequest]
    metadata: dict[str, str]


# =============================================================================
# Tool Output Types
# =============================================================================


class ToolOutput(TypedDict, total=False):
    """Tool output for submit_tool_outputs."""

    tool_call_id: str
    output: str


# =============================================================================
# Assistant Requests
# =============================================================================


class CreateAssistantRequest(BaseModel):
    """Request to create a new assistant.

    Validates the incoming request for POST /v1/assistants.
    """

    model: str = Field(..., min_length=1, description="Model to use for the assistant")
    name: str | None = Field(default=None, max_length=256, description="Assistant name")
    description: str | None = Field(
        default=None, max_length=512, description="Assistant description"
    )
    instructions: str | None = Field(
        default=None, max_length=256000, description="System instructions"
    )
    tools: list[AssistantToolRequest] = Field(
        default_factory=list, max_length=128, description="Tools available to the assistant"
    )
    metadata: dict[str, str] = Field(
        default_factory=dict, description="Metadata key-value pairs"
    )
    temperature: float | None = Field(default=None, ge=0, le=2, description="Sampling temperature")
    top_p: float | None = Field(default=None, ge=0, le=1, description="Nucleus sampling parameter")
    response_format: str | dict[str, str] | None = Field(
        default=None, description="Response format (auto or json_object)"
    )


class ModifyAssistantRequest(BaseModel):
    """Request to modify an existing assistant.

    Validates the incoming request for POST /v1/assistants/{assistant_id}.
    All fields are optional for partial updates.
    """

    model: str | None = Field(default=None, min_length=1, description="Model to use")
    name: str | None = Field(default=None, max_length=256, description="Assistant name")
    description: str | None = Field(default=None, max_length=512, description="Description")
    instructions: str | None = Field(default=None, max_length=256000, description="Instructions")
    tools: list[AssistantToolRequest] | None = Field(default=None, description="Tools")
    metadata: dict[str, str] | None = Field(default=None, description="Metadata")
    temperature: float | None = Field(default=None, ge=0, le=2)
    top_p: float | None = Field(default=None, ge=0, le=1)
    response_format: str | dict[str, str] | None = Field(default=None)


# =============================================================================
# Thread Requests
# =============================================================================


class CreateThreadRequest(BaseModel):
    """Request to create a new thread.

    Validates the incoming request for POST /v1/threads.
    """

    messages: list[ThreadMessageRequest] | None = Field(
        default=None, description="Initial messages for the thread"
    )
    metadata: dict[str, str] | None = Field(
        default=None, description="Metadata key-value pairs"
    )


class ModifyThreadRequest(BaseModel):
    """Request to modify an existing thread.

    Validates the incoming request for POST /v1/threads/{thread_id}.
    """

    metadata: dict[str, str] | None = Field(
        default=None, description="Metadata key-value pairs"
    )


# =============================================================================
# Message Requests
# =============================================================================


class CreateMessageRequest(BaseModel):
    """Request to create a new message in a thread.

    Validates the incoming request for POST /v1/threads/{thread_id}/messages.
    """

    role: Literal["user", "assistant"] = Field(
        ..., description="Role of the message author"
    )
    content: str = Field(..., min_length=1, description="Message content")
    attachments: list[dict[str, str | list[dict[str, str]]]] | None = Field(
        default=None, description="File attachments"
    )
    metadata: dict[str, str] | None = Field(
        default=None, description="Metadata key-value pairs"
    )


class ModifyMessageRequest(BaseModel):
    """Request to modify an existing message.

    Validates the incoming request for POST /v1/threads/{thread_id}/messages/{message_id}.
    """

    metadata: dict[str, str] | None = Field(
        default=None, description="Metadata key-value pairs"
    )


# =============================================================================
# Run Requests
# =============================================================================


class CreateRunRequest(BaseModel):
    """Request to create a new run on a thread.

    Validates the incoming request for POST /v1/threads/{thread_id}/runs.
    """

    assistant_id: str = Field(..., min_length=1, description="Assistant ID to use")
    model: str | None = Field(default=None, description="Model override")
    instructions: str | None = Field(
        default=None, max_length=256000, description="Instructions override"
    )
    additional_instructions: str | None = Field(
        default=None, description="Additional instructions to append"
    )
    additional_messages: list[ThreadMessageRequest] | None = Field(
        default=None, description="Additional messages to add before the run"
    )
    tools: list[AssistantToolRequest] | None = Field(
        default=None, description="Tools override"
    )
    metadata: dict[str, str] | None = Field(default=None, description="Run metadata")
    stream: bool = Field(default=False, description="Enable streaming")
    max_prompt_tokens: int | None = Field(default=None, description="Max prompt tokens")
    max_completion_tokens: int | None = Field(default=None, description="Max completion tokens")
    truncation_strategy: dict[str, str | int] | None = Field(
        default=None, description="Message truncation strategy"
    )
    tool_choice: str | dict[str, str | dict[str, str]] | None = Field(
        default=None, description="Tool selection mode"
    )
    parallel_tool_calls: bool | None = Field(
        default=None, description="Enable parallel tool calls"
    )
    response_format: str | dict[str, str] | None = Field(
        default=None, description="Response format"
    )


class ModifyRunRequest(BaseModel):
    """Request to modify an existing run.

    Validates the incoming request for POST /v1/threads/{thread_id}/runs/{run_id}.
    """

    metadata: dict[str, str] | None = Field(
        default=None, description="Metadata key-value pairs"
    )


class SubmitToolOutputsRequest(BaseModel):
    """Request to submit tool outputs for a run.

    Validates the incoming request for POST /v1/threads/{thread_id}/runs/{run_id}/submit_tool_outputs.
    """

    tool_outputs: list[ToolOutput] = Field(
        ..., min_length=1, description="Tool outputs to submit"
    )
    stream: bool = Field(default=False, description="Enable streaming for continued run")


# =============================================================================
# Combined Thread and Run Request
# =============================================================================


class CreateThreadAndRunRequest(BaseModel):
    """Request to create a thread and run in one call.

    Validates the incoming request for POST /v1/threads/runs.
    """

    assistant_id: str = Field(..., min_length=1, description="Assistant ID to use")
    thread: ThreadRequest | None = Field(
        default=None, description="Thread configuration with optional messages"
    )
    model: str | None = Field(default=None, description="Model override")
    instructions: str | None = Field(default=None, description="Instructions override")
    tools: list[AssistantToolRequest] | None = Field(default=None, description="Tools override")
    metadata: dict[str, str] | None = Field(default=None, description="Run metadata")
    stream: bool = Field(default=False, description="Enable streaming")
    max_prompt_tokens: int | None = Field(default=None, description="Max prompt tokens")
    max_completion_tokens: int | None = Field(default=None, description="Max completion tokens")
    truncation_strategy: dict[str, str | int] | None = Field(default=None)
    tool_choice: str | dict[str, str | dict[str, str]] | None = Field(default=None)
    parallel_tool_calls: bool | None = Field(default=None)
    response_format: str | dict[str, str] | None = Field(default=None)
