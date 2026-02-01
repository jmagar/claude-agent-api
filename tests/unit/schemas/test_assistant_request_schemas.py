"""Unit tests for OpenAI Assistants API Pydantic request schemas (TDD - RED phase)."""

import pytest
from pydantic import ValidationError


class TestCreateAssistantRequest:
    """Tests for CreateAssistantRequest schema."""

    def test_can_import_schema(self) -> None:
        """Schema can be imported from the module."""
        from apps.api.schemas.openai.assistant_requests import CreateAssistantRequest

        assert CreateAssistantRequest is not None

    def test_minimal_valid_request(self) -> None:
        """Minimal valid request with only required fields."""
        from apps.api.schemas.openai.assistant_requests import CreateAssistantRequest

        request = CreateAssistantRequest(model="gpt-4")
        assert request.model == "gpt-4"
        assert request.name is None
        assert request.instructions is None

    def test_full_valid_request(self) -> None:
        """Request with all optional fields."""
        from apps.api.schemas.openai.assistant_requests import (
            AssistantToolCodeInterpreter,
            CreateAssistantRequest,
        )

        tool: AssistantToolCodeInterpreter = {"type": "code_interpreter"}
        request = CreateAssistantRequest(
            model="gpt-4",
            name="My Assistant",
            description="A helpful assistant",
            instructions="You are a helpful assistant.",
            tools=[tool],
            metadata={"key": "value"},
        )
        assert request.name == "My Assistant"
        assert request.instructions == "You are a helpful assistant."
        assert len(request.tools) == 1

    def test_validates_model_required(self) -> None:
        """Model field is required."""
        from apps.api.schemas.openai.assistant_requests import CreateAssistantRequest

        with pytest.raises(ValidationError):
            CreateAssistantRequest.model_validate({})

    def test_function_tool_validation(self) -> None:
        """Function tool format is validated."""
        from apps.api.schemas.openai.assistant_requests import (
            AssistantToolFunction,
            CreateAssistantRequest,
            FunctionDefinition,
            FunctionParameters,
        )

        parameters: FunctionParameters = {
            "type": "object",
            "properties": {"location": {"type": "string"}},
            "required": ["location"],
        }
        function_def: FunctionDefinition = {
            "name": "get_weather",
            "description": "Get weather for a location",
            "parameters": parameters,
        }
        tool: AssistantToolFunction = {
            "type": "function",
            "function": function_def,
        }
        request = CreateAssistantRequest(
            model="gpt-4",
            tools=[tool],
        )
        assert request.tools[0]["type"] == "function"


class TestModifyAssistantRequest:
    """Tests for ModifyAssistantRequest schema."""

    def test_can_import_schema(self) -> None:
        """Schema can be imported from the module."""
        from apps.api.schemas.openai.assistant_requests import ModifyAssistantRequest

        assert ModifyAssistantRequest is not None

    def test_empty_request_valid(self) -> None:
        """Empty request is valid (partial update)."""
        from apps.api.schemas.openai.assistant_requests import ModifyAssistantRequest

        request = ModifyAssistantRequest()
        assert request.model is None
        assert request.name is None

    def test_partial_update(self) -> None:
        """Can update individual fields."""
        from apps.api.schemas.openai.assistant_requests import ModifyAssistantRequest

        request = ModifyAssistantRequest(name="New Name")
        assert request.name == "New Name"
        assert request.model is None


class TestCreateThreadRequest:
    """Tests for CreateThreadRequest schema."""

    def test_can_import_schema(self) -> None:
        """Schema can be imported from the module."""
        from apps.api.schemas.openai.assistant_requests import CreateThreadRequest

        assert CreateThreadRequest is not None

    def test_empty_request_valid(self) -> None:
        """Empty request is valid."""
        from apps.api.schemas.openai.assistant_requests import CreateThreadRequest

        request = CreateThreadRequest()
        assert request.messages is None
        assert request.metadata is None

    def test_with_initial_messages(self) -> None:
        """Request with initial messages."""
        from apps.api.schemas.openai.assistant_requests import (
            CreateThreadRequest,
            ThreadMessageRequest,
        )

        message: ThreadMessageRequest = {"role": "user", "content": "Hello!"}
        request = CreateThreadRequest(
            messages=[message],
            metadata={"key": "value"},
        )
        assert request.messages is not None
        assert len(request.messages) == 1
        assert request.messages[0]["role"] == "user"


class TestModifyThreadRequest:
    """Tests for ModifyThreadRequest schema."""

    def test_can_import_schema(self) -> None:
        """Schema can be imported from the module."""
        from apps.api.schemas.openai.assistant_requests import ModifyThreadRequest

        assert ModifyThreadRequest is not None

    def test_metadata_update(self) -> None:
        """Can update metadata."""
        from apps.api.schemas.openai.assistant_requests import ModifyThreadRequest

        request = ModifyThreadRequest(metadata={"new_key": "new_value"})
        assert request.metadata == {"new_key": "new_value"}


class TestCreateMessageRequest:
    """Tests for CreateMessageRequest schema."""

    def test_can_import_schema(self) -> None:
        """Schema can be imported from the module."""
        from apps.api.schemas.openai.assistant_requests import CreateMessageRequest

        assert CreateMessageRequest is not None

    def test_minimal_valid_request(self) -> None:
        """Minimal valid request with required fields."""
        from apps.api.schemas.openai.assistant_requests import CreateMessageRequest

        request = CreateMessageRequest(role="user", content="Hello!")
        assert request.role == "user"
        assert request.content == "Hello!"

    def test_validates_role(self) -> None:
        """Role must be 'user' or 'assistant'."""
        from apps.api.schemas.openai.assistant_requests import CreateMessageRequest

        # Valid roles
        CreateMessageRequest(role="user", content="test")
        # Assistant role (for pre-populating history)
        CreateMessageRequest(role="assistant", content="test")

    def test_with_metadata(self) -> None:
        """Request with metadata."""
        from apps.api.schemas.openai.assistant_requests import CreateMessageRequest

        request = CreateMessageRequest(
            role="user",
            content="Hello!",
            metadata={"key": "value"},
        )
        assert request.metadata == {"key": "value"}


class TestModifyMessageRequest:
    """Tests for ModifyMessageRequest schema."""

    def test_can_import_schema(self) -> None:
        """Schema can be imported from the module."""
        from apps.api.schemas.openai.assistant_requests import ModifyMessageRequest

        assert ModifyMessageRequest is not None

    def test_metadata_update(self) -> None:
        """Can update metadata."""
        from apps.api.schemas.openai.assistant_requests import ModifyMessageRequest

        request = ModifyMessageRequest(metadata={"new_key": "new_value"})
        assert request.metadata == {"new_key": "new_value"}


class TestCreateRunRequest:
    """Tests for CreateRunRequest schema."""

    def test_can_import_schema(self) -> None:
        """Schema can be imported from the module."""
        from apps.api.schemas.openai.assistant_requests import CreateRunRequest

        assert CreateRunRequest is not None

    def test_minimal_valid_request(self) -> None:
        """Minimal valid request with only required fields."""
        from apps.api.schemas.openai.assistant_requests import CreateRunRequest

        request = CreateRunRequest(assistant_id="asst_abc123")
        assert request.assistant_id == "asst_abc123"

    def test_with_instructions_override(self) -> None:
        """Request with instructions override."""
        from apps.api.schemas.openai.assistant_requests import CreateRunRequest

        request = CreateRunRequest(
            assistant_id="asst_abc123",
            instructions="Override instructions",
            model="gpt-4",
        )
        assert request.instructions == "Override instructions"
        assert request.model == "gpt-4"

    def test_with_additional_messages(self) -> None:
        """Request with additional messages to append."""
        from apps.api.schemas.openai.assistant_requests import (
            CreateRunRequest,
            ThreadMessageRequest,
        )

        message: ThreadMessageRequest = {"role": "user", "content": "Follow-up"}
        request = CreateRunRequest(
            assistant_id="asst_abc123",
            additional_messages=[message],
        )
        assert request.additional_messages is not None
        assert len(request.additional_messages) == 1

    def test_streaming_flag(self) -> None:
        """Request with streaming enabled."""
        from apps.api.schemas.openai.assistant_requests import CreateRunRequest

        request = CreateRunRequest(
            assistant_id="asst_abc123",
            stream=True,
        )
        assert request.stream is True


class TestModifyRunRequest:
    """Tests for ModifyRunRequest schema."""

    def test_can_import_schema(self) -> None:
        """Schema can be imported from the module."""
        from apps.api.schemas.openai.assistant_requests import ModifyRunRequest

        assert ModifyRunRequest is not None

    def test_metadata_update(self) -> None:
        """Can update metadata."""
        from apps.api.schemas.openai.assistant_requests import ModifyRunRequest

        request = ModifyRunRequest(metadata={"new_key": "new_value"})
        assert request.metadata == {"new_key": "new_value"}


class TestSubmitToolOutputsRequest:
    """Tests for SubmitToolOutputsRequest schema."""

    def test_can_import_schema(self) -> None:
        """Schema can be imported from the module."""
        from apps.api.schemas.openai.assistant_requests import SubmitToolOutputsRequest

        assert SubmitToolOutputsRequest is not None

    def test_valid_tool_output(self) -> None:
        """Valid tool output submission."""
        from apps.api.schemas.openai.assistant_requests import SubmitToolOutputsRequest

        request = SubmitToolOutputsRequest(
            tool_outputs=[
                {"tool_call_id": "call_abc123", "output": '{"result": "sunny"}'},
            ]
        )
        assert len(request.tool_outputs) == 1
        assert request.tool_outputs[0]["tool_call_id"] == "call_abc123"

    def test_multiple_tool_outputs(self) -> None:
        """Multiple tool outputs in one submission."""
        from apps.api.schemas.openai.assistant_requests import SubmitToolOutputsRequest

        request = SubmitToolOutputsRequest(
            tool_outputs=[
                {"tool_call_id": "call_abc123", "output": '{"result": "A"}'},
                {"tool_call_id": "call_def456", "output": '{"result": "B"}'},
            ]
        )
        assert len(request.tool_outputs) == 2

    def test_validates_tool_outputs_required(self) -> None:
        """tool_outputs field is required."""
        from apps.api.schemas.openai.assistant_requests import SubmitToolOutputsRequest

        with pytest.raises(ValidationError):
            SubmitToolOutputsRequest.model_validate({})

    def test_streaming_with_tool_outputs(self) -> None:
        """Can enable streaming when submitting tool outputs."""
        from apps.api.schemas.openai.assistant_requests import SubmitToolOutputsRequest

        request = SubmitToolOutputsRequest(
            tool_outputs=[{"tool_call_id": "call_abc123", "output": "result"}],
            stream=True,
        )
        assert request.stream is True


class TestCreateThreadAndRunRequest:
    """Tests for CreateThreadAndRunRequest schema (combined operation)."""

    def test_can_import_schema(self) -> None:
        """Schema can be imported from the module."""
        from apps.api.schemas.openai.assistant_requests import CreateThreadAndRunRequest

        assert CreateThreadAndRunRequest is not None

    def test_minimal_valid_request(self) -> None:
        """Minimal valid request."""
        from apps.api.schemas.openai.assistant_requests import CreateThreadAndRunRequest

        request = CreateThreadAndRunRequest(assistant_id="asst_abc123")
        assert request.assistant_id == "asst_abc123"
        assert request.thread is None

    def test_with_thread_and_messages(self) -> None:
        """Request with thread containing messages."""
        from apps.api.schemas.openai.assistant_requests import (
            CreateThreadAndRunRequest,
            ThreadMessageRequest,
        )

        message: ThreadMessageRequest = {"role": "user", "content": "Hello!"}
        request = CreateThreadAndRunRequest(
            assistant_id="asst_abc123",
            thread={"messages": [message]},
        )
        assert request.thread is not None
        assert len(request.thread["messages"]) == 1
