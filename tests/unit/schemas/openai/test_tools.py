"""Unit tests for OpenAI tool calling TypedDict schemas.

This module tests all tool-related schemas in apps/api/schemas/openai/tools.py,
including request parameters (tools, tool_choice) and response structures
(tool_calls, tool messages).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, get_type_hints

if TYPE_CHECKING:
    from apps.api.schemas.openai.tools import (
        OpenAIDeltaWithTools,
        OpenAIFunctionCall,
        OpenAIFunctionCallDelta,
        OpenAIFunctionDefinition,
        OpenAIFunctionParameters,
        OpenAIResponseMessageWithTools,
        OpenAIStreamChoiceWithTools,
        OpenAITool,
        OpenAIToolCall,
        OpenAIToolCallDelta,
        OpenAIToolChoice,
        OpenAIToolChoiceFunction,
        OpenAIToolResultMessage,
    )


class TestOpenAIFunctionParameters:
    """Tests for OpenAIFunctionParameters TypedDict."""

    def test_can_import_schema(self) -> None:
        """Schema can be imported from the module."""
        from apps.api.schemas.openai.tools import OpenAIFunctionParameters

        assert OpenAIFunctionParameters is not None

    def test_has_required_fields(self) -> None:
        """Schema has all required fields with correct types."""
        from apps.api.schemas.openai.tools import OpenAIFunctionParameters

        hints = get_type_hints(OpenAIFunctionParameters)
        assert "type" in hints
        assert "properties" in hints
        assert "required" in hints
        assert "additionalProperties" in hints

    def test_can_create_valid_parameters(self) -> None:
        """Can create valid function parameters dict."""

        params: OpenAIFunctionParameters = {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "City name"},
                "units": {"type": "string", "enum": ["celsius", "fahrenheit"]},
            },
            "required": ["location"],
        }
        assert params["type"] == "object"
        assert "location" in params["properties"]
        assert params["required"] == ["location"]

    def test_can_create_strict_mode_parameters(self) -> None:
        """Can create parameters with strict mode enabled."""

        params: OpenAIFunctionParameters = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
            "additionalProperties": False,
        }
        assert params["additionalProperties"] is False

    def test_can_create_empty_parameters(self) -> None:
        """Can create parameters with no properties."""

        params: OpenAIFunctionParameters = {
            "type": "object",
            "properties": {},
            "required": [],
        }
        assert params["properties"] == {}
        assert params["required"] == []


class TestOpenAIFunctionDefinition:
    """Tests for OpenAIFunctionDefinition TypedDict."""

    def test_can_import_schema(self) -> None:
        """Schema can be imported from the module."""
        from apps.api.schemas.openai.tools import OpenAIFunctionDefinition

        assert OpenAIFunctionDefinition is not None

    def test_has_required_fields(self) -> None:
        """Schema has all required fields with correct types."""
        from apps.api.schemas.openai.tools import OpenAIFunctionDefinition

        hints = get_type_hints(OpenAIFunctionDefinition)
        assert "name" in hints
        assert "description" in hints
        assert "parameters" in hints
        assert "strict" in hints

    def test_can_create_minimal_definition(self) -> None:
        """Can create function definition with only name."""

        func_def: OpenAIFunctionDefinition = {"name": "get_weather"}
        assert func_def["name"] == "get_weather"

    def test_can_create_full_definition(self) -> None:
        """Can create function definition with all fields."""

        func_def: OpenAIFunctionDefinition = {
            "name": "get_weather",
            "description": "Get current weather for a location",
            "parameters": {
                "type": "object",
                "properties": {"location": {"type": "string"}},
                "required": ["location"],
            },
            "strict": True,
        }
        assert func_def["name"] == "get_weather"
        assert func_def["description"] == "Get current weather for a location"
        assert func_def["strict"] is True

    def test_can_create_definition_without_parameters(self) -> None:
        """Can create function definition without parameters schema."""

        func_def: OpenAIFunctionDefinition = {
            "name": "no_params_function",
            "description": "Function with no parameters",
        }
        assert "parameters" not in func_def


class TestOpenAITool:
    """Tests for OpenAITool TypedDict."""

    def test_can_import_schema(self) -> None:
        """Schema can be imported from the module."""
        from apps.api.schemas.openai.tools import OpenAITool

        assert OpenAITool is not None

    def test_has_required_fields(self) -> None:
        """Schema has all required fields with correct types."""
        from apps.api.schemas.openai.tools import OpenAITool

        hints = get_type_hints(OpenAITool)
        assert "type" in hints
        assert "function" in hints

    def test_can_create_valid_tool(self) -> None:
        """Can create valid tool definition."""

        tool: OpenAITool = {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get weather data",
                "parameters": {
                    "type": "object",
                    "properties": {"location": {"type": "string"}},
                    "required": ["location"],
                },
            },
        }
        assert tool["type"] == "function"
        assert tool["function"]["name"] == "get_weather"

    def test_can_create_tool_with_strict_mode(self) -> None:
        """Can create tool with strict mode enabled."""

        tool: OpenAITool = {
            "type": "function",
            "function": {
                "name": "strict_function",
                "strict": True,
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                    "additionalProperties": False,
                },
            },
        }
        assert tool["function"]["strict"] is True


class TestOpenAIToolChoice:
    """Tests for OpenAIToolChoice and related schemas."""

    def test_can_import_schemas(self) -> None:
        """All tool choice schemas can be imported."""
        from apps.api.schemas.openai.tools import (
            OpenAIToolChoice,
            OpenAIToolChoiceFunction,
            OpenAIToolChoiceObject,
        )

        assert OpenAIToolChoice is not None
        assert OpenAIToolChoiceFunction is not None
        assert OpenAIToolChoiceObject is not None

    def test_can_create_auto_tool_choice(self) -> None:
        """Can use 'auto' string for tool_choice."""

        choice: OpenAIToolChoice = "auto"
        assert choice == "auto"

    def test_can_create_none_tool_choice(self) -> None:
        """Can use 'none' string for tool_choice."""

        choice: OpenAIToolChoice = "none"
        assert choice == "none"

    def test_can_create_required_tool_choice(self) -> None:
        """Can use 'required' string for tool_choice."""

        choice: OpenAIToolChoice = "required"
        assert choice == "required"

    def test_can_create_specific_function_choice(self) -> None:
        """Can create object form to force specific function."""

        choice: OpenAIToolChoice = {
            "type": "function",
            "function": {"name": "get_weather"},
        }
        assert choice["type"] == "function"
        assert choice["function"]["name"] == "get_weather"

    def test_tool_choice_function_schema(self) -> None:
        """OpenAIToolChoiceFunction has correct structure."""

        func: OpenAIToolChoiceFunction = {"name": "specific_function"}
        assert func["name"] == "specific_function"


class TestOpenAIFunctionCall:
    """Tests for OpenAIFunctionCall TypedDict."""

    def test_can_import_schema(self) -> None:
        """Schema can be imported from the module."""
        from apps.api.schemas.openai.tools import OpenAIFunctionCall

        assert OpenAIFunctionCall is not None

    def test_has_required_fields(self) -> None:
        """Schema has all required fields with correct types."""
        from apps.api.schemas.openai.tools import OpenAIFunctionCall

        hints = get_type_hints(OpenAIFunctionCall)
        assert "name" in hints
        assert "arguments" in hints

    def test_can_create_function_call(self) -> None:
        """Can create valid function call dict."""

        func_call: OpenAIFunctionCall = {
            "name": "get_weather",
            "arguments": '{"location": "San Francisco", "units": "celsius"}',
        }
        assert func_call["name"] == "get_weather"
        assert isinstance(func_call["arguments"], str)

    def test_arguments_is_json_string(self) -> None:
        """Arguments field is a JSON string, not parsed object."""

        func_call: OpenAIFunctionCall = {
            "name": "test_func",
            "arguments": "{}",  # Empty JSON string
        }
        assert func_call["arguments"] == "{}"

    def test_can_create_complex_arguments(self) -> None:
        """Can create function call with complex nested arguments."""

        import json

        args_dict = {
            "users": [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}],
            "filter": {"active": True},
        }
        func_call: OpenAIFunctionCall = {
            "name": "query_users",
            "arguments": json.dumps(args_dict),
        }
        assert func_call["name"] == "query_users"
        assert "Alice" in func_call["arguments"]


class TestOpenAIToolCall:
    """Tests for OpenAIToolCall TypedDict."""

    def test_can_import_schema(self) -> None:
        """Schema can be imported from the module."""
        from apps.api.schemas.openai.tools import OpenAIToolCall

        assert OpenAIToolCall is not None

    def test_has_required_fields(self) -> None:
        """Schema has all required fields with correct types."""
        from apps.api.schemas.openai.tools import OpenAIToolCall

        hints = get_type_hints(OpenAIToolCall)
        assert "id" in hints
        assert "type" in hints
        assert "function" in hints

    def test_can_create_tool_call(self) -> None:
        """Can create valid tool call dict."""

        tool_call: OpenAIToolCall = {
            "id": "call_abc123",
            "type": "function",
            "function": {"name": "get_weather", "arguments": '{"location": "NYC"}'},
        }
        assert tool_call["id"] == "call_abc123"
        assert tool_call["type"] == "function"
        assert tool_call["function"]["name"] == "get_weather"

    def test_tool_call_id_format(self) -> None:
        """Tool call ID follows OpenAI format (call_*)."""

        tool_call: OpenAIToolCall = {
            "id": "call_xyz789",
            "type": "function",
            "function": {"name": "test", "arguments": "{}"},
        }
        assert tool_call["id"].startswith("call_")


class TestOpenAIToolResultMessage:
    """Tests for OpenAIToolResultMessage TypedDict."""

    def test_can_import_schema(self) -> None:
        """Schema can be imported from the module."""
        from apps.api.schemas.openai.tools import OpenAIToolResultMessage

        assert OpenAIToolResultMessage is not None

    def test_has_required_fields(self) -> None:
        """Schema has all required fields with correct types."""
        from apps.api.schemas.openai.tools import OpenAIToolResultMessage

        hints = get_type_hints(OpenAIToolResultMessage)
        assert "role" in hints
        assert "tool_call_id" in hints
        assert "name" in hints
        assert "content" in hints

    def test_can_create_tool_result_message(self) -> None:
        """Can create valid tool result message."""

        message: OpenAIToolResultMessage = {
            "role": "tool",
            "tool_call_id": "call_abc123",
            "content": '{"temperature": 72, "condition": "sunny"}',
        }
        assert message["role"] == "tool"
        assert message["tool_call_id"] == "call_abc123"

    def test_can_create_message_with_function_name(self) -> None:
        """Can create tool result message with optional function name."""

        message: OpenAIToolResultMessage = {
            "role": "tool",
            "tool_call_id": "call_abc123",
            "name": "get_weather",
            "content": "Weather data",
        }
        assert message["name"] == "get_weather"

    def test_can_create_message_without_name(self) -> None:
        """Can create tool result message without function name."""

        message: OpenAIToolResultMessage = {
            "role": "tool",
            "tool_call_id": "call_abc123",
            "content": "Result data",
        }
        assert "name" not in message


class TestOpenAIFunctionCallDelta:
    """Tests for OpenAIFunctionCallDelta TypedDict."""

    def test_can_import_schema(self) -> None:
        """Schema can be imported from the module."""
        from apps.api.schemas.openai.tools import OpenAIFunctionCallDelta

        assert OpenAIFunctionCallDelta is not None

    def test_can_create_name_only_delta(self) -> None:
        """Can create delta with only function name."""

        delta: OpenAIFunctionCallDelta = {"name": "get_weather"}
        assert delta["name"] == "get_weather"
        assert "arguments" not in delta

    def test_can_create_arguments_only_delta(self) -> None:
        """Can create delta with only arguments chunk."""

        delta: OpenAIFunctionCallDelta = {"arguments": '{"loc'}
        assert delta["arguments"] == '{"loc'
        assert "name" not in delta

    def test_can_create_combined_delta(self) -> None:
        """Can create delta with both name and arguments."""

        delta: OpenAIFunctionCallDelta = {
            "name": "get_weather",
            "arguments": '{"location"',
        }
        assert delta["name"] == "get_weather"
        assert delta["arguments"] == '{"location"'

    def test_can_create_empty_delta(self) -> None:
        """Can create empty delta dict."""

        delta: OpenAIFunctionCallDelta = {}
        assert delta == {}


class TestOpenAIToolCallDelta:
    """Tests for OpenAIToolCallDelta TypedDict."""

    def test_can_import_schema(self) -> None:
        """Schema can be imported from the module."""
        from apps.api.schemas.openai.tools import OpenAIToolCallDelta

        assert OpenAIToolCallDelta is not None

    def test_has_required_fields(self) -> None:
        """Schema has all required fields with correct types."""
        from apps.api.schemas.openai.tools import OpenAIToolCallDelta

        hints = get_type_hints(OpenAIToolCallDelta)
        assert "index" in hints
        assert "id" in hints
        assert "type" in hints
        assert "function" in hints

    def test_can_create_first_chunk_delta(self) -> None:
        """Can create first chunk with id and type."""

        delta: OpenAIToolCallDelta = {
            "index": 0,
            "id": "call_abc123",
            "type": "function",
            "function": {"name": "get_weather"},
        }
        assert delta["index"] == 0
        assert delta["id"] == "call_abc123"
        assert delta["type"] == "function"

    def test_can_create_arguments_chunk_delta(self) -> None:
        """Can create subsequent chunk with only arguments."""

        delta: OpenAIToolCallDelta = {
            "index": 0,
            "function": {"arguments": '{"location"'},
        }
        assert delta["index"] == 0
        assert "id" not in delta
        assert "type" not in delta

    def test_can_create_multiple_tool_deltas(self) -> None:
        """Can create deltas for multiple tools using index."""

        delta1: OpenAIToolCallDelta = {
            "index": 0,
            "id": "call_1",
            "type": "function",
            "function": {"name": "func1"},
        }
        delta2: OpenAIToolCallDelta = {
            "index": 1,
            "id": "call_2",
            "type": "function",
            "function": {"name": "func2"},
        }
        assert delta1["index"] == 0
        assert delta2["index"] == 1


class TestOpenAIResponseMessageWithTools:
    """Tests for OpenAIResponseMessageWithTools TypedDict."""

    def test_can_import_schema(self) -> None:
        """Schema can be imported from the module."""
        from apps.api.schemas.openai.tools import OpenAIResponseMessageWithTools

        assert OpenAIResponseMessageWithTools is not None

    def test_has_required_fields(self) -> None:
        """Schema has all required fields with correct types."""
        from apps.api.schemas.openai.tools import OpenAIResponseMessageWithTools

        hints = get_type_hints(OpenAIResponseMessageWithTools)
        assert "role" in hints
        assert "content" in hints
        assert "tool_calls" in hints

    def test_can_create_regular_message(self) -> None:
        """Can create message without tool calls."""

        message: OpenAIResponseMessageWithTools = {
            "role": "assistant",
            "content": "Hello, how can I help you?",
        }
        assert message["role"] == "assistant"
        assert message["content"] == "Hello, how can I help you?"
        assert "tool_calls" not in message

    def test_can_create_message_with_tool_calls(self) -> None:
        """Can create message with tool calls."""

        message: OpenAIResponseMessageWithTools = {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "call_abc123",
                    "type": "function",
                    "function": {"name": "get_weather", "arguments": "{}"},
                }
            ],
        }
        assert message["role"] == "assistant"
        assert message["content"] is None
        assert len(message["tool_calls"]) == 1

    def test_can_create_message_with_multiple_tools(self) -> None:
        """Can create message with multiple tool calls."""

        message: OpenAIResponseMessageWithTools = {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {"name": "func1", "arguments": "{}"},
                },
                {
                    "id": "call_2",
                    "type": "function",
                    "function": {"name": "func2", "arguments": "{}"},
                },
            ],
        }
        assert len(message["tool_calls"]) == 2


class TestOpenAIChoiceWithTools:
    """Tests for OpenAIChoiceWithTools TypedDict."""

    def test_can_import_schema(self) -> None:
        """Schema can be imported from the module."""
        from apps.api.schemas.openai.tools import OpenAIChoiceWithTools

        assert OpenAIChoiceWithTools is not None

    def test_has_required_fields(self) -> None:
        """Schema has all required fields with correct types."""
        from apps.api.schemas.openai.tools import OpenAIChoiceWithTools

        hints = get_type_hints(OpenAIChoiceWithTools)
        assert "index" in hints
        assert "message" in hints
        assert "finish_reason" in hints

    def test_can_create_choice_with_stop_reason(self) -> None:
        """Can create choice with stop finish reason."""
        from apps.api.schemas.openai.tools import OpenAIChoiceWithTools

        choice: OpenAIChoiceWithTools = {
            "index": 0,
            "message": {"role": "assistant", "content": "Hello!"},
            "finish_reason": "stop",
        }
        assert choice["finish_reason"] == "stop"

    def test_can_create_choice_with_tool_calls_reason(self) -> None:
        """Can create choice with tool_calls finish reason."""
        from apps.api.schemas.openai.tools import OpenAIChoiceWithTools

        choice: OpenAIChoiceWithTools = {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_1",
                        "type": "function",
                        "function": {"name": "test", "arguments": "{}"},
                    }
                ],
            },
            "finish_reason": "tool_calls",
        }
        assert choice["finish_reason"] == "tool_calls"
        assert choice["message"]["content"] is None

    def test_can_create_choice_with_length_reason(self) -> None:
        """Can create choice with length finish reason."""
        from apps.api.schemas.openai.tools import OpenAIChoiceWithTools

        choice: OpenAIChoiceWithTools = {
            "index": 0,
            "message": {"role": "assistant", "content": "Truncated..."},
            "finish_reason": "length",
        }
        assert choice["finish_reason"] == "length"

    def test_can_create_choice_with_error_reason(self) -> None:
        """Can create choice with error finish reason."""
        from apps.api.schemas.openai.tools import OpenAIChoiceWithTools

        choice: OpenAIChoiceWithTools = {
            "index": 0,
            "message": {"role": "assistant", "content": None},
            "finish_reason": "error",
        }
        assert choice["finish_reason"] == "error"

    def test_can_create_choice_with_null_finish_reason(self) -> None:
        """Can create choice with null finish reason."""
        from apps.api.schemas.openai.tools import OpenAIChoiceWithTools

        choice: OpenAIChoiceWithTools = {
            "index": 0,
            "message": {"role": "assistant", "content": "In progress..."},
            "finish_reason": None,
        }
        assert choice["finish_reason"] is None


class TestOpenAIDeltaWithTools:
    """Tests for OpenAIDeltaWithTools TypedDict."""

    def test_can_import_schema(self) -> None:
        """Schema can be imported from the module."""
        from apps.api.schemas.openai.tools import OpenAIDeltaWithTools

        assert OpenAIDeltaWithTools is not None

    def test_can_create_role_delta(self) -> None:
        """Can create delta with only role."""

        delta: OpenAIDeltaWithTools = {"role": "assistant"}
        assert delta["role"] == "assistant"

    def test_can_create_content_delta(self) -> None:
        """Can create delta with only content."""

        delta: OpenAIDeltaWithTools = {"content": "Hello"}
        assert delta["content"] == "Hello"

    def test_can_create_tool_calls_delta(self) -> None:
        """Can create delta with tool calls."""

        delta: OpenAIDeltaWithTools = {
            "tool_calls": [{"index": 0, "id": "call_1", "type": "function"}]
        }
        assert len(delta["tool_calls"]) == 1

    def test_can_create_empty_delta(self) -> None:
        """Can create empty delta dict."""

        delta: OpenAIDeltaWithTools = {}
        assert delta == {}


class TestOpenAIStreamChoiceWithTools:
    """Tests for OpenAIStreamChoiceWithTools TypedDict."""

    def test_can_import_schema(self) -> None:
        """Schema can be imported from the module."""
        from apps.api.schemas.openai.tools import OpenAIStreamChoiceWithTools

        assert OpenAIStreamChoiceWithTools is not None

    def test_has_required_fields(self) -> None:
        """Schema has all required fields with correct types."""
        from apps.api.schemas.openai.tools import OpenAIStreamChoiceWithTools

        hints = get_type_hints(OpenAIStreamChoiceWithTools)
        assert "index" in hints
        assert "delta" in hints
        assert "finish_reason" in hints

    def test_can_create_initial_chunk(self) -> None:
        """Can create initial streaming chunk with role."""

        choice: OpenAIStreamChoiceWithTools = {
            "index": 0,
            "delta": {"role": "assistant"},
            "finish_reason": None,
        }
        assert choice["delta"]["role"] == "assistant"
        assert choice["finish_reason"] is None

    def test_can_create_content_chunk(self) -> None:
        """Can create streaming chunk with content delta."""

        choice: OpenAIStreamChoiceWithTools = {
            "index": 0,
            "delta": {"content": "Hello"},
            "finish_reason": None,
        }
        assert choice["delta"]["content"] == "Hello"

    def test_can_create_tool_calls_chunk(self) -> None:
        """Can create streaming chunk with tool call delta."""

        choice: OpenAIStreamChoiceWithTools = {
            "index": 0,
            "delta": {
                "tool_calls": [
                    {
                        "index": 0,
                        "id": "call_1",
                        "type": "function",
                        "function": {"name": "test"},
                    }
                ]
            },
            "finish_reason": None,
        }
        assert len(choice["delta"]["tool_calls"]) == 1

    def test_can_create_final_chunk(self) -> None:
        """Can create final streaming chunk with finish reason."""

        choice: OpenAIStreamChoiceWithTools = {
            "index": 0,
            "delta": {},
            "finish_reason": "tool_calls",
        }
        assert choice["finish_reason"] == "tool_calls"
        assert choice["delta"] == {}


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_function_parameters_with_nested_objects(self) -> None:
        """Can create parameters with deeply nested object structures."""

        params: OpenAIFunctionParameters = {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "address": {
                            "type": "object",
                            "properties": {
                                "street": {"type": "string"},
                                "city": {"type": "string"},
                            },
                        },
                    },
                }
            },
            "required": ["user"],
        }
        assert "user" in params["properties"]

    def test_function_parameters_with_array_properties(self) -> None:
        """Can create parameters with array properties."""

        params: OpenAIFunctionParameters = {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "items": {"type": "string"},
                }
            },
            "required": [],
        }
        assert params["properties"]["items"]["type"] == "array"

    def test_tool_call_with_empty_arguments(self) -> None:
        """Can create tool call with empty arguments string."""

        tool_call: OpenAIToolCall = {
            "id": "call_1",
            "type": "function",
            "function": {"name": "no_args_func", "arguments": "{}"},
        }
        assert tool_call["function"]["arguments"] == "{}"

    def test_streaming_multiple_tool_indices(self) -> None:
        """Can create tool call deltas for multiple indices in parallel."""
        from apps.api.schemas.openai.tools import OpenAIToolCallDelta

        deltas = [
            OpenAIToolCallDelta(
                index=0, id="call_1", type="function", function={"name": "func1"}
            ),
            OpenAIToolCallDelta(
                index=1, id="call_2", type="function", function={"name": "func2"}
            ),
            OpenAIToolCallDelta(index=0, function={"arguments": '{"a"'}),
            OpenAIToolCallDelta(index=1, function={"arguments": '{"b"'}),
        ]
        assert deltas[0]["index"] == 0
        assert deltas[1]["index"] == 1

    def test_tool_result_with_json_content(self) -> None:
        """Can create tool result with complex JSON content."""

        import json

        result_data = {
            "weather": {
                "temperature": 72,
                "conditions": ["sunny", "clear"],
                "forecast": [
                    {"day": "Monday", "high": 75},
                    {"day": "Tuesday", "high": 78},
                ],
            }
        }
        message: OpenAIToolResultMessage = {
            "role": "tool",
            "tool_call_id": "call_1",
            "name": "get_weather",
            "content": json.dumps(result_data),
        }
        assert "weather" in message["content"]
        assert json.loads(message["content"])["weather"]["temperature"] == 72

    def test_message_with_content_and_tool_calls_both_present(self) -> None:
        """Can create message with both content and tool_calls (edge case)."""

        message: OpenAIResponseMessageWithTools = {
            "role": "assistant",
            "content": "Let me check that for you.",
            "tool_calls": [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {"name": "search", "arguments": "{}"},
                }
            ],
        }
        assert message["content"] == "Let me check that for you."
        assert len(message["tool_calls"]) == 1
