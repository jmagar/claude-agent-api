"""SDK message type mappings and utilities."""

from typing import Literal

from pydantic import BaseModel


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


def map_sdk_content_block(block: dict[str, object]) -> dict[str, object]:
    """Map SDK content block to API schema.

    Args:
        block: SDK content block dict.

    Returns:
        API content block dict.
    """
    block_type = block.get("type", "text")

    if block_type == "text":
        return {
            "type": "text",
            "text": block.get("text", ""),
        }
    elif block_type == "thinking":
        return {
            "type": "thinking",
            "thinking": block.get("thinking", ""),
        }
    elif block_type == "tool_use":
        return {
            "type": "tool_use",
            "id": block.get("id"),
            "name": block.get("name"),
            "input": block.get("input", {}),
        }
    elif block_type == "tool_result":
        return {
            "type": "tool_result",
            "tool_use_id": block.get("tool_use_id"),
            "content": block.get("content"),
            "is_error": block.get("is_error", False),
        }
    else:
        # Unknown block type, return as-is
        return block


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
        question = tool_input.get("question")
        if isinstance(question, str):
            return question
    return None
