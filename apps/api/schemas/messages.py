"""SDK message type mappings and utilities."""

from typing import Literal, TypedDict, cast

from pydantic import BaseModel


class ContentBlockDict(TypedDict, total=False):
    """TypedDict for content block data matching ContentBlockSchema fields."""

    type: Literal["text", "thinking", "tool_use", "tool_result"]
    text: str | None
    thinking: str | None
    id: str | None
    name: str | None
    input: dict[str, object] | None
    tool_use_id: str | None
    content: str | list[object] | None
    is_error: bool | None


class SDKTextBlock(BaseModel):
    """SDK TextBlock mapping."""

    type: Literal["text"] = "text"
    text: str


class SDKThinkingBlock(BaseModel):
    """SDK ThinkingBlock mapping."""

    type: Literal["thinking"] = "thinking"
    thinking: str


class SDKToolUseBlock(BaseModel):
    """SDK ToolUseBlock mapping."""

    type: Literal["tool_use"] = "tool_use"
    id: str
    name: str
    input: dict[str, object]


class SDKToolResultBlock(BaseModel):
    """SDK ToolResultBlock mapping."""

    type: Literal["tool_result"] = "tool_result"
    tool_use_id: str
    content: str | list[object]
    is_error: bool = False


# Type for SDK content blocks
SDKContentBlock = SDKTextBlock | SDKThinkingBlock | SDKToolUseBlock | SDKToolResultBlock


class SDKUsageData(BaseModel):
    """SDK usage data mapping."""

    input_tokens: int
    output_tokens: int
    cache_read_input_tokens: int = 0
    cache_creation_input_tokens: int = 0


def map_sdk_content_block(block: dict[str, object]) -> ContentBlockDict:
    """Map SDK content block to API schema.

    Args:
        block: SDK content block dict.

    Returns:
        API content block dict with proper types.
    """
    block_type = block.get("type", "text")

    if block_type == "text":
        text_val = block.get("text", "")
        return ContentBlockDict(
            type="text",
            text=text_val if isinstance(text_val, str) else "",
        )
    elif block_type == "thinking":
        thinking_val = block.get("thinking", "")
        return ContentBlockDict(
            type="thinking",
            thinking=thinking_val if isinstance(thinking_val, str) else "",
        )
    elif block_type == "tool_use":
        id_val = block.get("id")
        name_val = block.get("name")
        input_val = block.get("input", {})
        # Cast dict to proper type for ty
        typed_input: dict[str, object] | None = (
            cast("dict[str, object]", input_val) if isinstance(input_val, dict) else {}
        )
        return ContentBlockDict(
            type="tool_use",
            id=id_val if isinstance(id_val, str) else None,
            name=name_val if isinstance(name_val, str) else None,
            input=typed_input,
        )
    elif block_type == "tool_result":
        tool_use_id_val = block.get("tool_use_id")
        content_val = block.get("content")
        is_error_val = block.get("is_error", False)
        # Handle content which can be str or list[object] - cast list for ty
        typed_content: str | list[object] | None
        if isinstance(content_val, str):
            typed_content = content_val
        elif isinstance(content_val, list):
            typed_content = cast("list[object]", content_val)
        else:
            typed_content = None
        return ContentBlockDict(
            type="tool_result",
            tool_use_id=tool_use_id_val if isinstance(tool_use_id_val, str) else None,
            content=typed_content,
            is_error=is_error_val if isinstance(is_error_val, bool) else False,
        )
    else:
        # Unknown block type, default to text
        return ContentBlockDict(type="text")


def _to_int(value: object) -> int:
    """Safely convert object to int."""
    if isinstance(value, int):
        return value
    if isinstance(value, (float, str)):
        return int(value)
    return 0


def map_sdk_usage(usage: dict[str, object] | None) -> dict[str, int] | None:
    """Map SDK usage data to API schema.

    Args:
        usage: SDK usage dict.

    Returns:
        API usage dict or None.
    """
    if usage is None:
        return None

    return {
        "input_tokens": _to_int(usage.get("input_tokens", 0)),
        "output_tokens": _to_int(usage.get("output_tokens", 0)),
        "cache_read_input_tokens": _to_int(usage.get("cache_read_input_tokens", 0)),
        "cache_creation_input_tokens": _to_int(
            usage.get("cache_creation_input_tokens", 0)
        ),
    }


def is_ask_user_question(block: dict[str, object]) -> bool:
    """Check if content block is an AskUserQuestion tool use.

    Args:
        block: Content block dict.

    Returns:
        True if block is AskUserQuestion.
    """
    return block.get("type") == "tool_use" and block.get("name") == "AskUserQuestion"


def extract_question_from_block(block: dict[str, object]) -> str | None:
    """Extract question text from AskUserQuestion block.

    Args:
        block: Content block dict.

    Returns:
        Question text or None.
    """
    if not is_ask_user_question(block):
        return None

    tool_input = block.get("input", {})
    if isinstance(tool_input, dict):
        question = cast("dict[str, object]", tool_input).get("question")
        if isinstance(question, str):
            return question
    return None
