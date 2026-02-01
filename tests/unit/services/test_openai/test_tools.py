"""Unit tests for OpenAI tool calling translation."""

import json


class TestToolTranslator:
    """Tests for ToolTranslator class."""

    def test_translate_tools_to_claude_function_tool(self) -> None:
        """Test translation of OpenAI function tool to Claude format.

        Given: OpenAI tool definition with function type
        When: translate_tools_to_claude is called
        Then: Returns Claude-formatted tool with input_schema
        """
        from apps.api.schemas.openai.requests import (
            OpenAIFunctionModel,
            OpenAIFunctionParametersModel,
            OpenAIToolModel,
        )
        from apps.api.services.openai.tools import ToolTranslator

        # Given
        openai_tools = [
            OpenAIToolModel(
                type="function",
                function=OpenAIFunctionModel(
                    name="get_weather",
                    description="Get weather for a location",
                    parameters=OpenAIFunctionParametersModel(
                        type="object",
                        properties={
                            "location": {"type": "string", "description": "City name"}
                        },
                        required=["location"],
                    ),
                ),
            )
        ]
        translator = ToolTranslator()

        # When
        result = translator.translate_tools_to_claude(openai_tools)

        # Then
        assert len(result) == 1
        assert result[0]["name"] == "get_weather"
        assert result[0]["description"] == "Get weather for a location"
        assert "input_schema" in result[0]
        schema = result[0]["input_schema"]
        assert schema["type"] == "object"  # type: ignore[index]
        assert "location" in schema["properties"]  # type: ignore[index]
        assert schema["required"] == ["location"]  # type: ignore[index]

    def test_translate_tools_to_claude_no_parameters(self) -> None:
        """Test translation of tool without parameters.

        Given: OpenAI tool with no parameters
        When: translate_tools_to_claude is called
        Then: Returns Claude tool with empty input_schema
        """
        from apps.api.schemas.openai.requests import (
            OpenAIFunctionModel,
            OpenAIToolModel,
        )
        from apps.api.services.openai.tools import ToolTranslator

        # Given
        openai_tools = [
            OpenAIToolModel(
                type="function",
                function=OpenAIFunctionModel(
                    name="get_current_time",
                    description="Get the current time",
                    parameters=None,
                ),
            )
        ]
        translator = ToolTranslator()

        # When
        result = translator.translate_tools_to_claude(openai_tools)

        # Then
        assert len(result) == 1
        assert result[0]["name"] == "get_current_time"
        assert result[0]["input_schema"] == {"type": "object", "properties": {}}

    def test_translate_tools_to_claude_multiple_tools(self) -> None:
        """Test translation of multiple tools.

        Given: Multiple OpenAI tool definitions
        When: translate_tools_to_claude is called
        Then: Returns list of Claude-formatted tools
        """
        from apps.api.schemas.openai.requests import (
            OpenAIFunctionModel,
            OpenAIToolModel,
        )
        from apps.api.services.openai.tools import ToolTranslator

        # Given
        openai_tools = [
            OpenAIToolModel(
                type="function",
                function=OpenAIFunctionModel(name="tool1", description="First tool"),
            ),
            OpenAIToolModel(
                type="function",
                function=OpenAIFunctionModel(name="tool2", description="Second tool"),
            ),
        ]
        translator = ToolTranslator()

        # When
        result = translator.translate_tools_to_claude(openai_tools)

        # Then
        assert len(result) == 2
        assert result[0]["name"] == "tool1"
        assert result[1]["name"] == "tool2"

    def test_translate_claude_tool_use_to_openai(self) -> None:
        """Test translation of Claude tool_use block to OpenAI format.

        Given: Claude content blocks with tool_use
        When: translate_claude_tool_use_to_openai is called
        Then: Returns OpenAI tool_calls format
        """
        from apps.api.services.openai.tools import ToolTranslator

        # Given
        content_blocks: list[dict[str, object]] = [
            {"type": "text", "text": "I'll check the weather for you."},
            {
                "type": "tool_use",
                "id": "toolu_01ABC123",
                "name": "get_weather",
                "input": {"location": "San Francisco"},
            },
        ]
        translator = ToolTranslator()

        # When
        result = translator.translate_claude_tool_use_to_openai(content_blocks)

        # Then
        assert len(result) == 1
        assert result[0]["id"] == "toolu_01ABC123"
        assert result[0]["type"] == "function"
        assert result[0]["function"]["name"] == "get_weather"
        assert json.loads(result[0]["function"]["arguments"]) == {
            "location": "San Francisco"
        }

    def test_translate_claude_tool_use_multiple_calls(self) -> None:
        """Test translation of multiple tool_use blocks.

        Given: Claude content with multiple tool_use blocks
        When: translate_claude_tool_use_to_openai is called
        Then: Returns multiple OpenAI tool_calls
        """
        from apps.api.services.openai.tools import ToolTranslator

        # Given
        content_blocks: list[dict[str, object]] = [
            {
                "type": "tool_use",
                "id": "call_1",
                "name": "get_weather",
                "input": {"location": "NYC"},
            },
            {
                "type": "tool_use",
                "id": "call_2",
                "name": "get_weather",
                "input": {"location": "LA"},
            },
        ]
        translator = ToolTranslator()

        # When
        result = translator.translate_claude_tool_use_to_openai(content_blocks)

        # Then
        assert len(result) == 2
        assert result[0]["id"] == "call_1"
        assert result[1]["id"] == "call_2"

    def test_translate_claude_tool_use_ignores_text_blocks(self) -> None:
        """Test that text blocks are ignored during tool_use translation.

        Given: Claude content with only text blocks
        When: translate_claude_tool_use_to_openai is called
        Then: Returns empty list
        """
        from apps.api.services.openai.tools import ToolTranslator

        # Given
        content_blocks: list[dict[str, object]] = [
            {"type": "text", "text": "Hello world"},
        ]
        translator = ToolTranslator()

        # When
        result = translator.translate_claude_tool_use_to_openai(content_blocks)

        # Then
        assert len(result) == 0

    def test_translate_tool_messages_to_claude(self) -> None:
        """Test translation of OpenAI tool messages to Claude tool_result.

        Given: OpenAI messages with role=tool
        When: translate_tool_messages_to_claude is called
        Then: Returns Claude tool_result blocks
        """
        from apps.api.schemas.openai.requests import OpenAIMessage
        from apps.api.services.openai.tools import ToolTranslator

        # Given
        messages = [
            OpenAIMessage(
                role="user",
                content="What's the weather?",
            ),
            OpenAIMessage(
                role="tool",
                tool_call_id="call_123",
                name="get_weather",
                content='{"temperature": 72, "condition": "sunny"}',
            ),
        ]
        translator = ToolTranslator()

        # When
        result = translator.translate_tool_messages_to_claude(messages)

        # Then
        assert len(result) == 1
        assert result[0]["type"] == "tool_result"
        assert result[0]["tool_use_id"] == "call_123"
        assert result[0]["content"] == '{"temperature": 72, "condition": "sunny"}'

    def test_translate_tool_messages_skips_missing_tool_call_id(self) -> None:
        """Test that tool messages without tool_call_id are skipped.

        Given: Tool message missing tool_call_id
        When: translate_tool_messages_to_claude is called
        Then: Returns empty list with warning logged
        """
        from apps.api.schemas.openai.requests import OpenAIMessage
        from apps.api.services.openai.tools import ToolTranslator

        # Given - tool message without tool_call_id
        messages = [
            OpenAIMessage(
                role="tool",
                content="result",
                # missing tool_call_id
            ),
        ]
        translator = ToolTranslator()

        # When
        result = translator.translate_tool_messages_to_claude(messages)

        # Then
        assert len(result) == 0

    def test_has_tool_calls_returns_true(self) -> None:
        """Test has_tool_calls returns True when tool_use present.

        Given: Content blocks with tool_use
        When: has_tool_calls is called
        Then: Returns True
        """
        from apps.api.services.openai.tools import ToolTranslator

        # Given
        content_blocks: list[dict[str, object]] = [
            {"type": "text", "text": "Hello"},
            {"type": "tool_use", "id": "123", "name": "test", "input": {}},
        ]
        translator = ToolTranslator()

        # When
        result = translator.has_tool_calls(content_blocks)

        # Then
        assert result is True

    def test_has_tool_calls_returns_false(self) -> None:
        """Test has_tool_calls returns False when no tool_use.

        Given: Content blocks without tool_use
        When: has_tool_calls is called
        Then: Returns False
        """
        from apps.api.services.openai.tools import ToolTranslator

        # Given
        content_blocks: list[dict[str, object]] = [
            {"type": "text", "text": "Hello"},
        ]
        translator = ToolTranslator()

        # When
        result = translator.has_tool_calls(content_blocks)

        # Then
        assert result is False

    def test_extract_text_content(self) -> None:
        """Test extract_text_content returns concatenated text.

        Given: Content blocks with text and tool_use
        When: extract_text_content is called
        Then: Returns only text content, space-separated
        """
        from apps.api.services.openai.tools import ToolTranslator

        # Given
        content_blocks: list[dict[str, object]] = [
            {"type": "text", "text": "Hello"},
            {"type": "tool_use", "id": "123", "name": "test", "input": {}},
            {"type": "text", "text": "World"},
        ]
        translator = ToolTranslator()

        # When
        result = translator.extract_text_content(content_blocks)

        # Then
        assert result == "Hello World"

    def test_extract_text_content_empty(self) -> None:
        """Test extract_text_content returns empty string when no text.

        Given: Content blocks with only tool_use
        When: extract_text_content is called
        Then: Returns empty string
        """
        from apps.api.services.openai.tools import ToolTranslator

        # Given
        content_blocks: list[dict[str, object]] = [
            {"type": "tool_use", "id": "123", "name": "test", "input": {}},
        ]
        translator = ToolTranslator()

        # When
        result = translator.extract_text_content(content_blocks)

        # Then
        assert result == ""
