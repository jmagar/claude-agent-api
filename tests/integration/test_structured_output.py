"""Integration tests for structured output functionality (User Story 8).

These tests verify that the API correctly handles output_format parameters
for enforcing structured JSON output from the agent.
"""

import pytest
from httpx import AsyncClient

from apps.api.schemas.requests.config import OutputFormatSchema
from apps.api.schemas.requests.query import QueryRequest


class TestOutputFormatValidation:
    """Tests for output_format request validation."""

    @pytest.mark.anyio
    async def test_json_output_format_accepted(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that json output format type is accepted in query request."""
        response = await async_client.post(
            "/api/v1/query",
            json={
                "prompt": "List files in JSON format",
                "output_format": {
                    "type": "json",
                },
            },
            headers=auth_headers,
        )
        # Should accept the request (stream starts) - status 200 for SSE
        assert response.status_code == 200

    @pytest.mark.anyio
    async def test_json_schema_output_format_accepted(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that json_schema output format with valid schema is accepted."""
        response = await async_client.post(
            "/api/v1/query",
            json={
                "prompt": "List files with their sizes",
                "output_format": {
                    "type": "json_schema",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "files": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "size": {"type": "integer"},
                                    },
                                    "required": ["name", "size"],
                                },
                            },
                        },
                        "required": ["files"],
                    },
                },
            },
            headers=auth_headers,
        )
        assert response.status_code == 200

    @pytest.mark.anyio
    async def test_json_schema_without_schema_rejected(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that json_schema type without schema field is rejected with 422."""
        response = await async_client.post(
            "/api/v1/query",
            json={
                "prompt": "List files",
                "output_format": {
                    "type": "json_schema",
                    # Missing schema field
                },
            },
            headers=auth_headers,
        )
        assert response.status_code == 422
        error_data = response.json()
        assert "detail" in error_data

    @pytest.mark.anyio
    async def test_invalid_schema_without_type_rejected(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that schema without 'type' property is rejected with 422."""
        response = await async_client.post(
            "/api/v1/query",
            json={
                "prompt": "List files",
                "output_format": {
                    "type": "json_schema",
                    "schema": {
                        # Missing 'type' property in schema
                        "properties": {
                            "name": {"type": "string"},
                        },
                    },
                },
            },
            headers=auth_headers,
        )
        assert response.status_code == 422
        error_data = response.json()
        assert "detail" in error_data

    @pytest.mark.anyio
    async def test_invalid_output_format_type_rejected(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that invalid output format type is rejected with 422."""
        response = await async_client.post(
            "/api/v1/query",
            json={
                "prompt": "List files",
                "output_format": {
                    "type": "invalid_format",
                },
            },
            headers=auth_headers,
        )
        assert response.status_code == 422
        error_data = response.json()
        assert "detail" in error_data


class TestOutputFormatSchemaValidation:
    """Tests for OutputFormatSchema Pydantic model validation."""

    def test_json_type_does_not_require_schema(self) -> None:
        """Test that json type doesn't require schema field."""
        output_format = OutputFormatSchema(type="json")
        assert output_format.type == "json"
        assert output_format.schema_ is None

    def test_json_schema_type_requires_schema(self) -> None:
        """Test that json_schema type requires schema field."""
        with pytest.raises(ValueError) as excinfo:
            OutputFormatSchema(type="json_schema")
        assert "json_schema type requires 'schema' field" in str(excinfo.value)

    def test_json_schema_with_valid_schema(self) -> None:
        """Test json_schema type with valid schema passes validation."""
        output_format = OutputFormatSchema(
            type="json_schema",
            schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                },
            },
        )
        assert output_format.type == "json_schema"
        assert output_format.schema_ is not None
        assert output_format.schema_["type"] == "object"

    def test_schema_without_type_property_rejected(self) -> None:
        """Test that schema without 'type' property fails validation."""
        with pytest.raises(ValueError) as excinfo:
            OutputFormatSchema(
                type="json_schema",
                schema={
                    "properties": {
                        "name": {"type": "string"},
                    },
                },
            )
        assert "JSON schema must have 'type' property" in str(excinfo.value)

    def test_json_type_with_schema_accepted(self) -> None:
        """Test that json type with optional schema is accepted."""
        # Schema is ignored for json type but should not cause error
        output_format = OutputFormatSchema(
            type="json",
            schema={
                "type": "object",
                "properties": {},
            },
        )
        assert output_format.type == "json"
        # Schema is accepted but effectively ignored for "json" type
        assert output_format.schema_ is not None


class TestOutputFormatSingleQuery:
    """Tests for output_format in non-streaming (single) query."""

    @pytest.mark.anyio
    async def test_single_query_with_json_output_format(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that output_format works with single (non-streaming) query."""
        response = await async_client.post(
            "/api/v1/query/single",
            json={
                "prompt": "Return a JSON object with a greeting",
                "output_format": {
                    "type": "json",
                },
            },
            headers=auth_headers,
        )
        # Single query endpoint should accept output_format
        assert response.status_code == 200

    @pytest.mark.anyio
    async def test_single_query_with_json_schema_output_format(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test single query with json_schema output format."""
        response = await async_client.post(
            "/api/v1/query/single",
            json={
                "prompt": "Return a greeting message",
                "output_format": {
                    "type": "json_schema",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "message": {"type": "string"},
                            "timestamp": {"type": "string"},
                        },
                        "required": ["message"],
                    },
                },
            },
            headers=auth_headers,
        )
        assert response.status_code == 200

    @pytest.mark.anyio
    async def test_single_query_invalid_output_format_rejected(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that invalid output_format is rejected in single query."""
        response = await async_client.post(
            "/api/v1/query/single",
            json={
                "prompt": "List files",
                "output_format": {
                    "type": "not_a_valid_type",
                },
            },
            headers=auth_headers,
        )
        assert response.status_code == 422


class TestOutputFormatInQueryRequest:
    """Tests for output_format in QueryRequest schema."""

    def test_query_request_accepts_output_format(self) -> None:
        """Test that QueryRequest accepts output_format parameter."""
        request = QueryRequest(
            prompt="Test prompt",
            output_format=OutputFormatSchema(
                type="json_schema",
                schema={
                    "type": "object",
                    "properties": {"result": {"type": "string"}},
                },
            ),
        )
        assert request.output_format is not None
        assert request.output_format.type == "json_schema"

    def test_query_request_output_format_defaults_to_none(self) -> None:
        """Test that output_format defaults to None when not specified."""
        request = QueryRequest(prompt="Test prompt")
        assert request.output_format is None

    def test_query_request_with_complex_schema(self) -> None:
        """Test QueryRequest with a complex nested JSON schema."""
        complex_schema: dict[str, object] = {
            "type": "object",
            "properties": {
                "users": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "name": {"type": "string"},
                            "email": {"type": "string"},
                            "roles": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                        },
                        "required": ["id", "name"],
                    },
                },
                "total_count": {"type": "integer"},
            },
            "required": ["users", "total_count"],
        }
        request = QueryRequest(
            prompt="List all users",
            output_format=OutputFormatSchema(
                type="json_schema",
                schema=complex_schema,
            ),
        )
        assert request.output_format is not None
        assert request.output_format.schema_ is not None
        assert "users" in request.output_format.schema_.get("properties", {})


class TestOutputFormatWithSession:
    """Tests for output_format with session operations."""

    @pytest.mark.anyio
    async def test_resume_with_output_format(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_session_id: str,
    ) -> None:
        """Test that output_format can be specified when resuming a session.

        Note: Resume requests use ResumeRequest schema which may not have
        output_format. This test verifies the expected behavior.
        """
        # Resume currently uses ResumeRequest which doesn't include output_format
        # This test documents that limitation - output_format should be set
        # in the original query request, not in resume
        response = await async_client.post(
            f"/api/v1/sessions/{mock_session_id}/resume",
            json={
                "prompt": "Continue and return JSON",
                # output_format not supported in ResumeRequest currently
            },
            headers=auth_headers,
        )
        # Should accept the request (output_format inheritance handled by session)
        assert response.status_code == 200


class TestStructuredOutputInResponse:
    """Tests for structured_output field in response events.

    These tests verify that when output_format is specified, the result
    event includes a structured_output field with parsed JSON data.
    """

    def test_result_includes_structured_output_field(self) -> None:
        """Test that result event schema includes structured_output field.

        This test verifies the ResultEventData schema has the structured_output
        field available for when the agent returns structured data.
        """
        from apps.api.schemas.responses import ResultEventData

        # Verify the schema supports structured_output
        fields = ResultEventData.model_fields
        assert "structured_output" in fields
        # The field should be optional (dict | None)
        assert fields["structured_output"].annotation == dict[str, object] | None

    def test_single_query_response_includes_structured_output_field(self) -> None:
        """Test that SingleQueryResponse schema includes structured_output field."""
        from apps.api.schemas.responses import SingleQueryResponse

        # Verify the schema supports structured_output
        fields = SingleQueryResponse.model_fields
        assert "structured_output" in fields
