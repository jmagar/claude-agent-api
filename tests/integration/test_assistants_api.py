"""Integration tests for Assistants API endpoints (TDD - RED phase)."""

from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from apps.api.main import create_app
from apps.api.routes.openai.dependencies import get_assistant_service
from apps.api.services.assistants import Assistant, AssistantListResult, AssistantService


@pytest.fixture
def mock_assistant() -> Assistant:
    """Create a mock assistant object."""
    return Assistant(
        id="asst_abc123",
        model="gpt-4",
        name="Test Assistant",
        description="A test assistant",
        instructions="You are a helpful assistant.",
        tools=[],
        metadata={},
        temperature=None,
        top_p=None,
        created_at=datetime(2024, 1, 1, tzinfo=UTC),
        updated_at=datetime(2024, 1, 1, tzinfo=UTC),
    )


@pytest.fixture
def mock_assistant_service(mock_assistant: Assistant) -> AsyncMock:
    """Create mock assistant service."""
    service = AsyncMock(spec=AssistantService)

    service.create_assistant = AsyncMock(return_value=mock_assistant)
    service.get_assistant = AsyncMock(return_value=mock_assistant)
    service.update_assistant = AsyncMock(return_value=mock_assistant)
    service.delete_assistant = AsyncMock(return_value=True)
    service.list_assistants = AsyncMock(
        return_value=AssistantListResult(
            data=[mock_assistant],
            first_id="asst_abc123",
            last_id="asst_abc123",
            has_more=False,
        )
    )

    return service


@pytest.fixture
async def assistants_test_client(
    mock_assistant_service: AsyncMock,
    test_api_key: str,
) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with mocked assistant service.

    Creates a fresh app instance and overrides the assistant service dependency.
    Uses the test_api_key fixture to ensure proper authentication.
    """
    # Create fresh app instance for testing
    test_app = create_app()

    # Override the dependency
    test_app.dependency_overrides[get_assistant_service] = lambda: mock_assistant_service

    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://test",
    ) as client:
        yield client

    # Clear the override
    test_app.dependency_overrides.clear()


class TestAssistantsRoutesImport:
    """Tests for assistants routes import."""

    def test_can_import_assistants_router(self) -> None:
        """Assistants router can be imported."""
        from apps.api.routes.openai.assistants import router

        assert router is not None


class TestCreateAssistant:
    """Tests for POST /v1/assistants."""

    @pytest.mark.anyio
    async def test_create_assistant_success(
        self,
        assistants_test_client: AsyncClient,
        test_api_key: str,
    ) -> None:
        """Create assistant with valid input."""
        response = await assistants_test_client.post(
            "/v1/assistants",
            json={
                "model": "gpt-4",
                "name": "Test Assistant",
                "instructions": "You are a helpful assistant.",
            },
            headers={"X-API-Key": test_api_key},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["object"] == "assistant"
        assert data["id"].startswith("asst_")
        assert data["model"] == "gpt-4"

    @pytest.mark.anyio
    async def test_create_assistant_minimal(
        self,
        assistants_test_client: AsyncClient,
        test_api_key: str,
    ) -> None:
        """Create assistant with only required fields."""
        response = await assistants_test_client.post(
            "/v1/assistants",
            json={"model": "gpt-4"},
            headers={"X-API-Key": test_api_key},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["object"] == "assistant"
        assert data["model"] == "gpt-4"

    @pytest.mark.anyio
    async def test_create_assistant_with_tools(
        self,
        assistants_test_client: AsyncClient,
        mock_assistant_service: AsyncMock,
        test_api_key: str,
    ) -> None:
        """Create assistant with tools."""
        response = await assistants_test_client.post(
            "/v1/assistants",
            json={
                "model": "gpt-4",
                "tools": [
                    {"type": "code_interpreter"},
                    {
                        "type": "function",
                        "function": {
                            "name": "get_weather",
                            "description": "Get the weather",
                        },
                    },
                ],
            },
            headers={"X-API-Key": test_api_key},
        )

        assert response.status_code == 200
        mock_assistant_service.create_assistant.assert_called_once()


class TestGetAssistant:
    """Tests for GET /v1/assistants/{assistant_id}."""

    @pytest.mark.anyio
    async def test_get_assistant_success(
        self,
        assistants_test_client: AsyncClient,
        test_api_key: str,
    ) -> None:
        """Get assistant by ID."""
        response = await assistants_test_client.get(
            "/v1/assistants/asst_abc123",
            headers={"X-API-Key": test_api_key},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["object"] == "assistant"
        assert data["id"] == "asst_abc123"

    @pytest.mark.anyio
    async def test_get_assistant_not_found(
        self,
        mock_assistant_service: AsyncMock,
        test_api_key: str,
    ) -> None:
        """Get assistant returns 404 when not found."""
        mock_assistant_service.get_assistant = AsyncMock(return_value=None)

        # Create fresh app with updated mock
        test_app = create_app()
        test_app.dependency_overrides[get_assistant_service] = lambda: mock_assistant_service

        async with AsyncClient(
            transport=ASGITransport(app=test_app),
            base_url="http://test",
        ) as client:
            response = await client.get(
                "/v1/assistants/asst_nonexistent",
                headers={"X-API-Key": test_api_key},
            )

        test_app.dependency_overrides.clear()

        assert response.status_code == 404


class TestListAssistants:
    """Tests for GET /v1/assistants."""

    @pytest.mark.anyio
    async def test_list_assistants_success(
        self,
        assistants_test_client: AsyncClient,
        test_api_key: str,
    ) -> None:
        """List assistants with pagination."""
        response = await assistants_test_client.get(
            "/v1/assistants",
            headers={"X-API-Key": test_api_key},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["object"] == "list"
        assert len(data["data"]) == 1
        assert data["has_more"] is False

    @pytest.mark.anyio
    async def test_list_assistants_with_params(
        self,
        assistants_test_client: AsyncClient,
        mock_assistant_service: AsyncMock,
        test_api_key: str,
    ) -> None:
        """List assistants with query parameters."""
        response = await assistants_test_client.get(
            "/v1/assistants?limit=10&order=asc",
            headers={"X-API-Key": test_api_key},
        )

        assert response.status_code == 200
        mock_assistant_service.list_assistants.assert_called_once()


class TestModifyAssistant:
    """Tests for POST /v1/assistants/{assistant_id}."""

    @pytest.mark.anyio
    async def test_modify_assistant_success(
        self,
        assistants_test_client: AsyncClient,
        mock_assistant_service: AsyncMock,
        test_api_key: str,
    ) -> None:
        """Modify assistant metadata."""
        response = await assistants_test_client.post(
            "/v1/assistants/asst_abc123",
            json={
                "name": "Updated Assistant",
                "instructions": "New instructions",
            },
            headers={"X-API-Key": test_api_key},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["object"] == "assistant"
        mock_assistant_service.update_assistant.assert_called_once()

    @pytest.mark.anyio
    async def test_modify_assistant_not_found(
        self,
        mock_assistant_service: AsyncMock,
        test_api_key: str,
    ) -> None:
        """Modify assistant returns 404 when not found."""
        mock_assistant_service.update_assistant = AsyncMock(return_value=None)

        # Create fresh app with updated mock
        test_app = create_app()
        test_app.dependency_overrides[get_assistant_service] = lambda: mock_assistant_service

        async with AsyncClient(
            transport=ASGITransport(app=test_app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/v1/assistants/asst_nonexistent",
                json={"name": "Updated"},
                headers={"X-API-Key": test_api_key},
            )

        test_app.dependency_overrides.clear()

        assert response.status_code == 404


class TestDeleteAssistant:
    """Tests for DELETE /v1/assistants/{assistant_id}."""

    @pytest.mark.anyio
    async def test_delete_assistant_success(
        self,
        assistants_test_client: AsyncClient,
        test_api_key: str,
    ) -> None:
        """Delete assistant."""
        response = await assistants_test_client.delete(
            "/v1/assistants/asst_abc123",
            headers={"X-API-Key": test_api_key},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["object"] == "assistant.deleted"
        assert data["deleted"] is True
        assert data["id"] == "asst_abc123"

    @pytest.mark.anyio
    async def test_delete_assistant_not_found(
        self,
        mock_assistant_service: AsyncMock,
        test_api_key: str,
    ) -> None:
        """Delete assistant returns 404 when not found."""
        mock_assistant_service.delete_assistant = AsyncMock(return_value=False)

        # Create fresh app with updated mock
        test_app = create_app()
        test_app.dependency_overrides[get_assistant_service] = lambda: mock_assistant_service

        async with AsyncClient(
            transport=ASGITransport(app=test_app),
            base_url="http://test",
        ) as client:
            response = await client.delete(
                "/v1/assistants/asst_nonexistent",
                headers={"X-API-Key": test_api_key},
            )

        test_app.dependency_overrides.clear()

        assert response.status_code == 404
