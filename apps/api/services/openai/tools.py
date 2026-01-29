"""Tool calling translation between OpenAI and Claude formats.

This module handles bidirectional translation of:
- Tool definitions (OpenAI tools[] -> Claude format)
- Tool calls in responses (Claude tool_use -> OpenAI tool_calls)
- Tool results in requests (OpenAI tool messages -> Claude tool_result)
"""

import json
import uuid
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from apps.api.schemas.openai.requests import (
        OpenAIMessage,
        OpenAIToolModel,
    )
    from apps.api.schemas.openai.responses import (
        OpenAIToolCallResponse,
    )

logger = structlog.get_logger(__name__)


class ToolTranslator:
    """Translates tool definitions and calls between OpenAI and Claude formats."""

    def translate_tools_to_claude(
        self, openai_tools: list["OpenAIToolModel"]
    ) -> list[dict[str, object]]:
        """Convert OpenAI tool definitions to Claude format.

        OpenAI format:
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "...",
                    "parameters": {...}
                }
            }

        Claude format:
            {
                "name": "get_weather",
                "description": "...",
                "input_schema": {...}
            }

        Args:
            openai_tools: List of OpenAI tool definitions

        Returns:
            List of Claude tool definitions
        """
        claude_tools: list[dict[str, object]] = []

        for tool in openai_tools:
            if tool.type != "function":
                logger.warning(
                    "Skipping non-function tool",
                    tool_type=tool.type,
                )
                continue

            func = tool.function
            claude_tool: dict[str, object] = {
                "name": func.name,
            }

            if func.description:
                claude_tool["description"] = func.description

            if func.parameters:
                # Translate parameters -> input_schema
                claude_tool["input_schema"] = {
                    "type": func.parameters.type,
                    "properties": func.parameters.properties,
                }
                if func.parameters.required:
                    claude_tool["input_schema"]["required"] = func.parameters.required
                if not func.parameters.additionalProperties:
                    claude_tool["input_schema"]["additionalProperties"] = False
            else:
                # Default empty schema
                claude_tool["input_schema"] = {
                    "type": "object",
                    "properties": {},
                }

            claude_tools.append(claude_tool)

        logger.debug(
            "Translated tools to Claude format",
            openai_count=len(openai_tools),
            claude_count=len(claude_tools),
        )

        return claude_tools

    def translate_claude_tool_use_to_openai(
        self, content_blocks: list[dict[str, object]]
    ) -> list["OpenAIToolCallResponse"]:
        """Extract tool_use blocks from Claude response and convert to OpenAI format.

        Claude format (in content array):
            {
                "type": "tool_use",
                "id": "toolu_01A09q90qw90lq917835lq9",
                "name": "get_weather",
                "input": {"location": "San Francisco"}
            }

        OpenAI format:
            {
                "id": "call_abc123",
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "arguments": "{\"location\": \"San Francisco\"}"
                }
            }

        Args:
            content_blocks: List of content blocks from Claude response

        Returns:
            List of OpenAI tool call objects
        """
        from apps.api.schemas.openai.responses import (
            OpenAIFunctionCallResponse,
            OpenAIToolCallResponse,
        )

        tool_calls: list[OpenAIToolCallResponse] = []

        for block in content_blocks:
            if block.get("type") != "tool_use":
                continue

            tool_id = str(block.get("id", f"call_{uuid.uuid4().hex[:24]}"))
            name = str(block.get("name", ""))
            input_data = block.get("input", {})

            # Convert Claude's parsed input to JSON string for OpenAI
            if isinstance(input_data, dict):
                arguments = json.dumps(input_data)
            else:
                arguments = str(input_data)

            function_call: OpenAIFunctionCallResponse = {
                "name": name,
                "arguments": arguments,
            }

            tool_call: OpenAIToolCallResponse = {
                "id": tool_id,
                "type": "function",
                "function": function_call,
            }

            tool_calls.append(tool_call)

        logger.debug(
            "Translated tool_use to OpenAI format",
            tool_count=len(tool_calls),
        )

        return tool_calls

    def translate_tool_messages_to_claude(
        self, messages: list["OpenAIMessage"]
    ) -> list[dict[str, object]]:
        """Extract tool result messages and convert to Claude tool_result format.

        OpenAI format (separate messages):
            {
                "role": "tool",
                "tool_call_id": "call_abc123",
                "name": "get_weather",
                "content": "{\"temperature\": 72}"
            }

        Claude format (in user message content array):
            {
                "type": "tool_result",
                "tool_use_id": "call_abc123",
                "content": "{\"temperature\": 72}"
            }

        Args:
            messages: List of OpenAI messages

        Returns:
            List of Claude tool_result blocks
        """
        tool_results: list[dict[str, object]] = []

        for msg in messages:
            if msg.role != "tool":
                continue

            if not msg.tool_call_id:
                logger.warning("Tool message missing tool_call_id")
                continue

            tool_result: dict[str, object] = {
                "type": "tool_result",
                "tool_use_id": msg.tool_call_id,
                "content": msg.content or "",
            }

            tool_results.append(tool_result)

        logger.debug(
            "Translated tool messages to Claude format",
            result_count=len(tool_results),
        )

        return tool_results

    def has_tool_calls(self, content_blocks: list[dict[str, object]]) -> bool:
        """Check if content blocks contain any tool_use blocks.

        Args:
            content_blocks: List of content blocks from Claude response

        Returns:
            True if any tool_use blocks are present
        """
        return any(block.get("type") == "tool_use" for block in content_blocks)

    def extract_text_content(self, content_blocks: list[dict[str, object]]) -> str:
        """Extract text content from content blocks, excluding tool_use.

        Args:
            content_blocks: List of content blocks

        Returns:
            Concatenated text content
        """
        text_parts: list[str] = []
        for block in content_blocks:
            if block.get("type") == "text":
                text = block.get("text", "")
                if text:
                    text_parts.append(str(text))
        return " ".join(text_parts)
