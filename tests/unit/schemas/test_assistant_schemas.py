"""Unit tests for OpenAI Assistants API TypedDict schemas (TDD - RED phase)."""

import time
from typing import get_type_hints

import pytest


class TestOpenAIAssistantSchema:
    """Tests for OpenAIAssistant TypedDict."""

    def test_can_import_schema(self) -> None:
        """Schema can be imported from the module."""
        from apps.api.schemas.openai.assistants import OpenAIAssistant

        assert OpenAIAssistant is not None

    def test_has_required_fields(self) -> None:
        """Schema has all required fields with correct types."""
        from apps.api.schemas.openai.assistants import OpenAIAssistant

        hints = get_type_hints(OpenAIAssistant)
        # Required fields per OpenAI spec
        assert "id" in hints
        assert "object" in hints
        assert "created_at" in hints
        assert "model" in hints
        assert "name" in hints
        assert "description" in hints
        assert "instructions" in hints
        assert "tools" in hints
        assert "metadata" in hints

    def test_can_create_valid_instance(self) -> None:
        """Can create a valid assistant dict."""
        from apps.api.schemas.openai.assistants import OpenAIAssistant

        assistant: OpenAIAssistant = {
            "id": "asst_abc123",
            "object": "assistant",
            "created_at": int(time.time()),
            "model": "gpt-4",
            "name": "Test Assistant",
            "description": "A test assistant",
            "instructions": "You are a helpful assistant.",
            "tools": [],
            "metadata": {},
        }
        assert assistant["id"] == "asst_abc123"
        assert assistant["object"] == "assistant"


class TestOpenAIAssistantToolSchema:
    """Tests for assistant tool schemas."""

    def test_code_interpreter_tool_schema(self) -> None:
        """Code interpreter tool has correct structure."""
        from apps.api.schemas.openai.assistants import OpenAIAssistantCodeInterpreterTool

        tool: OpenAIAssistantCodeInterpreterTool = {"type": "code_interpreter"}
        assert tool["type"] == "code_interpreter"

    def test_file_search_tool_schema(self) -> None:
        """File search tool has correct structure."""
        from apps.api.schemas.openai.assistants import OpenAIAssistantFileSearchTool

        tool: OpenAIAssistantFileSearchTool = {"type": "file_search"}
        assert tool["type"] == "file_search"

    def test_function_tool_schema(self) -> None:
        """Function tool has correct structure."""
        from apps.api.schemas.openai.assistants import OpenAIAssistantFunctionTool

        tool: OpenAIAssistantFunctionTool = {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get weather for a location",
                "parameters": {
                    "type": "object",
                    "properties": {"location": {"type": "string"}},
                    "required": ["location"],
                },
            },
        }
        assert tool["type"] == "function"
        assert tool["function"]["name"] == "get_weather"


class TestOpenAIThreadSchema:
    """Tests for OpenAIThread TypedDict."""

    def test_can_import_schema(self) -> None:
        """Schema can be imported from the module."""
        from apps.api.schemas.openai.assistants import OpenAIThread

        assert OpenAIThread is not None

    def test_has_required_fields(self) -> None:
        """Schema has all required fields with correct types."""
        from apps.api.schemas.openai.assistants import OpenAIThread

        hints = get_type_hints(OpenAIThread)
        assert "id" in hints
        assert "object" in hints
        assert "created_at" in hints
        assert "metadata" in hints

    def test_can_create_valid_instance(self) -> None:
        """Can create a valid thread dict."""
        from apps.api.schemas.openai.assistants import OpenAIThread

        thread: OpenAIThread = {
            "id": "thread_abc123",
            "object": "thread",
            "created_at": int(time.time()),
            "metadata": {},
        }
        assert thread["id"] == "thread_abc123"
        assert thread["object"] == "thread"


class TestOpenAIMessageSchema:
    """Tests for OpenAIMessage TypedDict (Assistants API version)."""

    def test_can_import_schema(self) -> None:
        """Schema can be imported from the module."""
        from apps.api.schemas.openai.assistants import OpenAIThreadMessage

        assert OpenAIThreadMessage is not None

    def test_has_required_fields(self) -> None:
        """Schema has all required fields with correct types."""
        from apps.api.schemas.openai.assistants import OpenAIThreadMessage

        hints = get_type_hints(OpenAIThreadMessage)
        assert "id" in hints
        assert "object" in hints
        assert "created_at" in hints
        assert "thread_id" in hints
        assert "role" in hints
        assert "content" in hints
        assert "metadata" in hints

    def test_can_create_user_message(self) -> None:
        """Can create a valid user message dict."""
        from apps.api.schemas.openai.assistants import OpenAIThreadMessage

        message: OpenAIThreadMessage = {
            "id": "msg_abc123",
            "object": "thread.message",
            "created_at": int(time.time()),
            "thread_id": "thread_abc123",
            "role": "user",
            "content": [{"type": "text", "text": {"value": "Hello!", "annotations": []}}],
            "metadata": {},
        }
        assert message["id"] == "msg_abc123"
        assert message["role"] == "user"

    def test_can_create_assistant_message(self) -> None:
        """Can create a valid assistant message dict."""
        from apps.api.schemas.openai.assistants import OpenAIThreadMessage

        message: OpenAIThreadMessage = {
            "id": "msg_abc123",
            "object": "thread.message",
            "created_at": int(time.time()),
            "thread_id": "thread_abc123",
            "role": "assistant",
            "content": [{"type": "text", "text": {"value": "Hi there!", "annotations": []}}],
            "assistant_id": "asst_abc123",
            "run_id": "run_abc123",
            "metadata": {},
        }
        assert message["role"] == "assistant"
        assert message["assistant_id"] == "asst_abc123"


class TestOpenAIMessageContentSchema:
    """Tests for message content block schemas."""

    def test_text_content_schema(self) -> None:
        """Text content block has correct structure."""
        from apps.api.schemas.openai.assistants import OpenAIMessageTextContent

        content: OpenAIMessageTextContent = {
            "type": "text",
            "text": {"value": "Hello world", "annotations": []},
        }
        assert content["type"] == "text"
        assert content["text"]["value"] == "Hello world"

    def test_image_file_content_schema(self) -> None:
        """Image file content block has correct structure."""
        from apps.api.schemas.openai.assistants import OpenAIMessageImageFileContent

        content: OpenAIMessageImageFileContent = {
            "type": "image_file",
            "image_file": {"file_id": "file_abc123"},
        }
        assert content["type"] == "image_file"


class TestOpenAIRunSchema:
    """Tests for OpenAIRun TypedDict."""

    def test_can_import_schema(self) -> None:
        """Schema can be imported from the module."""
        from apps.api.schemas.openai.assistants import OpenAIRun

        assert OpenAIRun is not None

    def test_has_required_fields(self) -> None:
        """Schema has all required fields with correct types."""
        from apps.api.schemas.openai.assistants import OpenAIRun

        hints = get_type_hints(OpenAIRun)
        assert "id" in hints
        assert "object" in hints
        assert "created_at" in hints
        assert "thread_id" in hints
        assert "assistant_id" in hints
        assert "status" in hints
        assert "model" in hints

    def test_can_create_queued_run(self) -> None:
        """Can create a run in queued state."""
        from apps.api.schemas.openai.assistants import OpenAIRun

        run: OpenAIRun = {
            "id": "run_abc123",
            "object": "thread.run",
            "created_at": int(time.time()),
            "thread_id": "thread_abc123",
            "assistant_id": "asst_abc123",
            "status": "queued",
            "model": "gpt-4",
            "instructions": "You are a helpful assistant.",
            "tools": [],
            "metadata": {},
        }
        assert run["status"] == "queued"

    def test_can_create_run_requiring_action(self) -> None:
        """Can create a run in requires_action state with tool calls."""
        from apps.api.schemas.openai.assistants import OpenAIRun

        run: OpenAIRun = {
            "id": "run_abc123",
            "object": "thread.run",
            "created_at": int(time.time()),
            "thread_id": "thread_abc123",
            "assistant_id": "asst_abc123",
            "status": "requires_action",
            "model": "gpt-4",
            "instructions": "You are a helpful assistant.",
            "tools": [],
            "metadata": {},
            "required_action": {
                "type": "submit_tool_outputs",
                "submit_tool_outputs": {
                    "tool_calls": [
                        {
                            "id": "call_abc123",
                            "type": "function",
                            "function": {
                                "name": "get_weather",
                                "arguments": '{"location": "NYC"}',
                            },
                        }
                    ]
                },
            },
        }
        assert run["status"] == "requires_action"
        assert run["required_action"] is not None


class TestOpenAIRunStepSchema:
    """Tests for OpenAIRunStep TypedDict."""

    def test_can_import_schema(self) -> None:
        """Schema can be imported from the module."""
        from apps.api.schemas.openai.assistants import OpenAIRunStep

        assert OpenAIRunStep is not None

    def test_has_required_fields(self) -> None:
        """Schema has all required fields with correct types."""
        from apps.api.schemas.openai.assistants import OpenAIRunStep

        hints = get_type_hints(OpenAIRunStep)
        assert "id" in hints
        assert "object" in hints
        assert "created_at" in hints
        assert "run_id" in hints
        assert "type" in hints
        assert "status" in hints
        assert "step_details" in hints

    def test_can_create_message_creation_step(self) -> None:
        """Can create a message creation run step."""
        from apps.api.schemas.openai.assistants import OpenAIRunStep

        step: OpenAIRunStep = {
            "id": "step_abc123",
            "object": "thread.run.step",
            "created_at": int(time.time()),
            "run_id": "run_abc123",
            "assistant_id": "asst_abc123",
            "thread_id": "thread_abc123",
            "type": "message_creation",
            "status": "completed",
            "step_details": {
                "type": "message_creation",
                "message_creation": {"message_id": "msg_abc123"},
            },
        }
        assert step["type"] == "message_creation"

    def test_can_create_tool_calls_step(self) -> None:
        """Can create a tool calls run step."""
        from apps.api.schemas.openai.assistants import OpenAIRunStep

        step: OpenAIRunStep = {
            "id": "step_abc123",
            "object": "thread.run.step",
            "created_at": int(time.time()),
            "run_id": "run_abc123",
            "assistant_id": "asst_abc123",
            "thread_id": "thread_abc123",
            "type": "tool_calls",
            "status": "in_progress",
            "step_details": {
                "type": "tool_calls",
                "tool_calls": [
                    {
                        "id": "call_abc123",
                        "type": "function",
                        "function": {"name": "get_weather", "arguments": "{}", "output": None},
                    }
                ],
            },
        }
        assert step["type"] == "tool_calls"


class TestPaginatedListSchemas:
    """Tests for paginated list response schemas."""

    def test_assistant_list_schema(self) -> None:
        """Can create a paginated assistant list."""
        from apps.api.schemas.openai.assistants import OpenAIAssistantList

        list_response: OpenAIAssistantList = {
            "object": "list",
            "data": [],
            "first_id": None,
            "last_id": None,
            "has_more": False,
        }
        assert list_response["object"] == "list"

    def test_message_list_schema(self) -> None:
        """Can create a paginated message list."""
        from apps.api.schemas.openai.assistants import OpenAIThreadMessageList

        list_response: OpenAIThreadMessageList = {
            "object": "list",
            "data": [],
            "first_id": None,
            "last_id": None,
            "has_more": False,
        }
        assert list_response["object"] == "list"

    def test_run_list_schema(self) -> None:
        """Can create a paginated run list."""
        from apps.api.schemas.openai.assistants import OpenAIRunList

        list_response: OpenAIRunList = {
            "object": "list",
            "data": [],
            "first_id": None,
            "last_id": None,
            "has_more": False,
        }
        assert list_response["object"] == "list"

    def test_run_step_list_schema(self) -> None:
        """Can create a paginated run step list."""
        from apps.api.schemas.openai.assistants import OpenAIRunStepList

        list_response: OpenAIRunStepList = {
            "object": "list",
            "data": [],
            "first_id": None,
            "last_id": None,
            "has_more": False,
        }
        assert list_response["object"] == "list"


class TestDeletionStatusSchema:
    """Tests for deletion status schema."""

    def test_can_import_schema(self) -> None:
        """Schema can be imported from the module."""
        from apps.api.schemas.openai.assistants import OpenAIDeletionStatus

        assert OpenAIDeletionStatus is not None

    def test_can_create_deletion_status(self) -> None:
        """Can create a valid deletion status dict."""
        from apps.api.schemas.openai.assistants import OpenAIDeletionStatus

        status: OpenAIDeletionStatus = {
            "id": "asst_abc123",
            "object": "assistant.deleted",
            "deleted": True,
        }
        assert status["deleted"] is True
