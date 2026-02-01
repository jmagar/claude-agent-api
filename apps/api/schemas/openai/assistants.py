"""OpenAI Assistants API TypedDict response schemas.

These schemas define the response types for the Assistants API endpoints,
following OpenAI's API specification with strict type safety (zero Any types).
"""

from typing import Literal, NotRequired, Required, TypedDict

# =============================================================================
# Tool Types for Assistants
# =============================================================================


class OpenAIAssistantCodeInterpreterTool(TypedDict):
    """Code interpreter tool definition."""

    type: Required[Literal["code_interpreter"]]


class OpenAIAssistantFileSearchTool(TypedDict):
    """File search tool definition."""

    type: Required[Literal["file_search"]]


class OpenAIFunctionParameters(TypedDict, total=False):
    """JSON Schema for function parameters."""

    type: str
    properties: dict[str, dict[str, str | list[str] | bool | int]]
    required: list[str]


class OpenAIAssistantFunctionDefinition(TypedDict, total=False):
    """Function definition for assistant function tool."""

    name: Required[str]
    description: str
    parameters: OpenAIFunctionParameters


class OpenAIAssistantFunctionTool(TypedDict):
    """Function tool definition."""

    type: Required[Literal["function"]]
    function: Required[OpenAIAssistantFunctionDefinition]


# Union type for assistant tools
OpenAIAssistantTool = (
    OpenAIAssistantCodeInterpreterTool
    | OpenAIAssistantFileSearchTool
    | OpenAIAssistantFunctionTool
)


# =============================================================================
# Assistant Object
# =============================================================================


class OpenAIAssistant(TypedDict, total=False):
    """OpenAI Assistant object.

    Represents an assistant that can be used to interact with the user
    via the Assistants API (threads, messages, runs).
    """

    id: Required[str]  # asst_xxx format
    object: Required[Literal["assistant"]]
    created_at: Required[int]  # Unix timestamp
    model: Required[str]  # Model identifier
    name: str | None  # Assistant name (optional)
    description: str | None  # Assistant description (optional)
    instructions: str | None  # System instructions (optional)
    tools: Required[list[OpenAIAssistantTool]]
    metadata: Required[dict[str, str]]
    top_p: float | None
    temperature: float | None
    response_format: str | dict[str, str] | None


# =============================================================================
# Thread Object
# =============================================================================


class OpenAIThread(TypedDict, total=False):
    """OpenAI Thread object.

    Represents a conversation thread that contains messages.
    """

    id: Required[str]  # thread_xxx format
    object: Required[Literal["thread"]]
    created_at: Required[int]  # Unix timestamp
    metadata: Required[dict[str, str]]
    tool_resources: dict[str, dict[str, list[str]]] | None


# =============================================================================
# Message Content Types
# =============================================================================


class OpenAITextAnnotation(TypedDict, total=False):
    """Text annotation (file citation or path)."""

    type: Required[Literal["file_citation", "file_path"]]
    text: Required[str]
    start_index: Required[int]
    end_index: Required[int]
    file_citation: dict[str, str]
    file_path: dict[str, str]


class OpenAITextContent(TypedDict):
    """Text content block value."""

    value: Required[str]
    annotations: Required[list[OpenAITextAnnotation]]


class OpenAIMessageTextContent(TypedDict):
    """Text content block in a message."""

    type: Required[Literal["text"]]
    text: Required[OpenAITextContent]


class OpenAIImageFileDetail(TypedDict):
    """Image file reference details."""

    file_id: Required[str]


class OpenAIMessageImageFileContent(TypedDict):
    """Image file content block in a message."""

    type: Required[Literal["image_file"]]
    image_file: Required[OpenAIImageFileDetail]


# Union type for message content
OpenAIMessageContent = OpenAIMessageTextContent | OpenAIMessageImageFileContent


# =============================================================================
# Thread Message Object
# =============================================================================


class OpenAIThreadMessage(TypedDict, total=False):
    """OpenAI Thread Message object.

    Represents a message within a thread.
    """

    id: Required[str]  # msg_xxx format
    object: Required[Literal["thread.message"]]
    created_at: Required[int]  # Unix timestamp
    thread_id: Required[str]
    role: Required[Literal["user", "assistant"]]
    content: Required[list[OpenAIMessageContent]]
    metadata: Required[dict[str, str]]
    # Optional fields for assistant messages
    assistant_id: str | None
    run_id: str | None
    # Attachments (optional)
    attachments: list[dict[str, str | list[dict[str, str]]]] | None


# =============================================================================
# Run Tool Call Types
# =============================================================================


class OpenAIRunFunctionCall(TypedDict):
    """Function call in a run tool call."""

    name: Required[str]
    arguments: Required[str]  # JSON string


class OpenAIRunToolCall(TypedDict):
    """Tool call within a run."""

    id: Required[str]  # call_xxx format
    type: Required[Literal["function"]]
    function: Required[OpenAIRunFunctionCall]


class OpenAISubmitToolOutputs(TypedDict):
    """Tool outputs submission request structure."""

    tool_calls: Required[list[OpenAIRunToolCall]]


class OpenAIRequiredAction(TypedDict):
    """Required action for a run (when tools need to be called)."""

    type: Required[Literal["submit_tool_outputs"]]
    submit_tool_outputs: Required[OpenAISubmitToolOutputs]


class OpenAIRunError(TypedDict):
    """Error details for a failed run."""

    code: Required[str]
    message: Required[str]


class OpenAIRunUsage(TypedDict):
    """Token usage for a run."""

    prompt_tokens: Required[int]
    completion_tokens: Required[int]
    total_tokens: Required[int]


# =============================================================================
# Run Object
# =============================================================================


class OpenAIRun(TypedDict, total=False):
    """OpenAI Run object.

    Represents an execution of an assistant on a thread.
    """

    id: Required[str]  # run_xxx format
    object: Required[Literal["thread.run"]]
    created_at: Required[int]  # Unix timestamp
    thread_id: Required[str]
    assistant_id: Required[str]
    status: Required[
        Literal[
            "queued",
            "in_progress",
            "requires_action",
            "cancelling",
            "cancelled",
            "failed",
            "completed",
            "expired",
        ]
    ]
    model: Required[str]
    instructions: str | None
    tools: Required[list[OpenAIAssistantTool]]
    metadata: Required[dict[str, str]]
    # Optional fields based on status
    required_action: OpenAIRequiredAction | None
    last_error: OpenAIRunError | None
    usage: OpenAIRunUsage | None
    started_at: int | None
    expires_at: int | None
    cancelled_at: int | None
    failed_at: int | None
    completed_at: int | None
    max_prompt_tokens: int | None
    max_completion_tokens: int | None
    truncation_strategy: dict[str, str | int] | None
    response_format: str | dict[str, str] | None
    tool_choice: str | dict[str, str | dict[str, str]] | None
    parallel_tool_calls: bool


# =============================================================================
# Run Step Types
# =============================================================================


class OpenAIMessageCreationDetails(TypedDict):
    """Details for message creation step."""

    message_id: Required[str]


class OpenAIMessageCreationStepDetails(TypedDict):
    """Step details for message creation."""

    type: Required[Literal["message_creation"]]
    message_creation: Required[OpenAIMessageCreationDetails]


class OpenAIToolCallFunctionOutput(TypedDict, total=False):
    """Function output in tool call step."""

    name: Required[str]
    arguments: Required[str]
    output: str | None


class OpenAIToolCallStepItem(TypedDict):
    """Individual tool call in a step."""

    id: Required[str]
    type: Required[Literal["function", "code_interpreter", "file_search"]]
    function: NotRequired[OpenAIToolCallFunctionOutput]


class OpenAIToolCallsStepDetails(TypedDict):
    """Step details for tool calls."""

    type: Required[Literal["tool_calls"]]
    tool_calls: Required[list[OpenAIToolCallStepItem]]


# Union type for step details
OpenAIRunStepDetails = OpenAIMessageCreationStepDetails | OpenAIToolCallsStepDetails


class OpenAIRunStep(TypedDict, total=False):
    """OpenAI Run Step object.

    Represents a step in the execution of a run.
    """

    id: Required[str]  # step_xxx format
    object: Required[Literal["thread.run.step"]]
    created_at: Required[int]  # Unix timestamp
    run_id: Required[str]
    assistant_id: Required[str]
    thread_id: Required[str]
    type: Required[Literal["message_creation", "tool_calls"]]
    status: Required[
        Literal["in_progress", "cancelled", "failed", "completed", "expired"]
    ]
    step_details: Required[OpenAIRunStepDetails]
    # Optional fields based on status
    last_error: OpenAIRunError | None
    usage: OpenAIRunUsage | None
    expired_at: int | None
    cancelled_at: int | None
    failed_at: int | None
    completed_at: int | None


# =============================================================================
# Paginated List Types
# =============================================================================


class OpenAIAssistantList(TypedDict):
    """Paginated list of assistants."""

    object: Required[Literal["list"]]
    data: Required[list[OpenAIAssistant]]
    first_id: Required[str | None]
    last_id: Required[str | None]
    has_more: Required[bool]


class OpenAIThreadMessageList(TypedDict):
    """Paginated list of thread messages."""

    object: Required[Literal["list"]]
    data: Required[list[OpenAIThreadMessage]]
    first_id: Required[str | None]
    last_id: Required[str | None]
    has_more: Required[bool]


class OpenAIRunList(TypedDict):
    """Paginated list of runs."""

    object: Required[Literal["list"]]
    data: Required[list[OpenAIRun]]
    first_id: Required[str | None]
    last_id: Required[str | None]
    has_more: Required[bool]


class OpenAIRunStepList(TypedDict):
    """Paginated list of run steps."""

    object: Required[Literal["list"]]
    data: Required[list[OpenAIRunStep]]
    first_id: Required[str | None]
    last_id: Required[str | None]
    has_more: Required[bool]


# =============================================================================
# Deletion Status
# =============================================================================


class OpenAIDeletionStatus(TypedDict):
    """Deletion confirmation response."""

    id: Required[str]
    object: Required[
        Literal[
            "assistant.deleted",
            "thread.deleted",
            "thread.message.deleted",
        ]
    ]
    deleted: Required[bool]
