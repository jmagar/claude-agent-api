"""Integration tests for Threads API endpoints (TDD - RED phase)."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from apps.api.main import create_app
from apps.api.routes.openai.dependencies import (
    get_message_service,
    get_run_service,
    get_thread_service,
)
from apps.api.services.assistants import (
    Message,
    MessageListResult,
    MessageService,
    Run,
    RunListResult,
    RunService,
    Thread,
    ThreadService,
)

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from apps.api.services.assistants.message_service import (
        MessageContent,
        MessageTextContent,
    )


@pytest.fixture
def mock_thread() -> Thread:
    """Create a mock thread object."""
    return Thread(
        id="thread_abc123",
        created_at=1704067200,  # 2024-01-01 00:00:00 UTC
        metadata={},
        session_id="session_xyz789",
    )


@pytest.fixture
def mock_message() -> Message:
    """Create a mock message object."""
    text_content: MessageTextContent = {
        "type": "text",
        "text": {"value": "Hello", "annotations": []},
    }
    content: list[MessageContent] = [text_content]
    return Message(
        id="msg_abc123",
        thread_id="thread_abc123",
        created_at=1704067200,
        role="user",
        content=content,
        metadata={},
    )


@pytest.fixture
def mock_run() -> Run:
    """Create a mock run object."""
    return Run(
        id="run_abc123",
        thread_id="thread_abc123",
        assistant_id="asst_xyz789",
        created_at=1704067200,
        status="queued",
        model="gpt-4",
        tools=[],
        metadata={},
    )


@pytest.fixture
def mock_thread_service(mock_thread: Thread) -> AsyncMock:
    """Create mock thread service."""
    service = AsyncMock(spec=ThreadService)

    service.create_thread = AsyncMock(return_value=mock_thread)
    service.get_thread = AsyncMock(return_value=mock_thread)
    service.modify_thread = AsyncMock(return_value=mock_thread)
    service.delete_thread = AsyncMock(return_value=True)

    return service


@pytest.fixture
def mock_message_service(mock_message: Message) -> AsyncMock:
    """Create mock message service."""
    service = AsyncMock(spec=MessageService)

    service.create_message = AsyncMock(return_value=mock_message)
    service.get_message = AsyncMock(return_value=mock_message)
    service.modify_message = AsyncMock(return_value=mock_message)
    service.list_messages = AsyncMock(
        return_value=MessageListResult(
            data=[mock_message],
            first_id="msg_abc123",
            last_id="msg_abc123",
            has_more=False,
        )
    )

    return service


@pytest.fixture
def mock_run_service(mock_run: Run) -> AsyncMock:
    """Create mock run service."""
    service = AsyncMock(spec=RunService)

    service.create_run = AsyncMock(return_value=mock_run)
    service.get_run = AsyncMock(return_value=mock_run)
    service.cancel_run = AsyncMock(return_value=mock_run)
    service.list_runs = AsyncMock(
        return_value=RunListResult(
            data=[mock_run],
            first_id="run_abc123",
            last_id="run_abc123",
            has_more=False,
        )
    )

    return service


@pytest.fixture
async def threads_test_client(
    mock_thread_service: AsyncMock,
    mock_message_service: AsyncMock,
    mock_run_service: AsyncMock,
    test_api_key: str,
) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with mocked services."""
    test_app = create_app()

    test_app.dependency_overrides[get_thread_service] = lambda: mock_thread_service
    test_app.dependency_overrides[get_message_service] = lambda: mock_message_service
    test_app.dependency_overrides[get_run_service] = lambda: mock_run_service

    async with AsyncClient(
        transport=ASGITransport(app=test_app),
        base_url="http://test",
    ) as client:
        yield client

    test_app.dependency_overrides.clear()


class TestThreadsRoutesImport:
    """Tests for threads routes import."""

    def test_can_import_threads_router(self) -> None:
        """Threads router can be imported."""
        from apps.api.routes.openai.threads import router

        assert router is not None


class TestCreateThread:
    """Tests for POST /v1/threads."""

    @pytest.mark.anyio
    async def test_create_thread_success(
        self,
        threads_test_client: AsyncClient,
        test_api_key: str,
    ) -> None:
        """Create thread with valid input."""
        response = await threads_test_client.post(
            "/v1/threads",
            json={},
            headers={"X-API-Key": test_api_key},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["object"] == "thread"
        assert data["id"].startswith("thread_")

    @pytest.mark.anyio
    async def test_create_thread_with_metadata(
        self,
        threads_test_client: AsyncClient,
        mock_thread_service: AsyncMock,
        test_api_key: str,
    ) -> None:
        """Create thread with metadata."""
        response = await threads_test_client.post(
            "/v1/threads",
            json={"metadata": {"key": "value"}},
            headers={"X-API-Key": test_api_key},
        )

        assert response.status_code == 200
        mock_thread_service.create_thread.assert_called_once()


class TestGetThread:
    """Tests for GET /v1/threads/{thread_id}."""

    @pytest.mark.anyio
    async def test_get_thread_success(
        self,
        threads_test_client: AsyncClient,
        test_api_key: str,
    ) -> None:
        """Get thread by ID."""
        response = await threads_test_client.get(
            "/v1/threads/thread_abc123",
            headers={"X-API-Key": test_api_key},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["object"] == "thread"
        assert data["id"] == "thread_abc123"

    @pytest.mark.anyio
    async def test_get_thread_not_found(
        self,
        mock_thread_service: AsyncMock,
        test_api_key: str,
    ) -> None:
        """Get thread returns 404 when not found."""
        mock_thread_service.get_thread = AsyncMock(return_value=None)

        test_app = create_app()
        test_app.dependency_overrides[get_thread_service] = lambda: mock_thread_service

        async with AsyncClient(
            transport=ASGITransport(app=test_app),
            base_url="http://test",
        ) as client:
            response = await client.get(
                "/v1/threads/thread_nonexistent",
                headers={"X-API-Key": test_api_key},
            )

        test_app.dependency_overrides.clear()

        assert response.status_code == 404


class TestModifyThread:
    """Tests for POST /v1/threads/{thread_id}."""

    @pytest.mark.anyio
    async def test_modify_thread_success(
        self,
        threads_test_client: AsyncClient,
        mock_thread_service: AsyncMock,
        test_api_key: str,
    ) -> None:
        """Modify thread metadata."""
        response = await threads_test_client.post(
            "/v1/threads/thread_abc123",
            json={"metadata": {"updated": "value"}},
            headers={"X-API-Key": test_api_key},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["object"] == "thread"
        mock_thread_service.modify_thread.assert_called_once()


class TestDeleteThread:
    """Tests for DELETE /v1/threads/{thread_id}."""

    @pytest.mark.anyio
    async def test_delete_thread_success(
        self,
        threads_test_client: AsyncClient,
        test_api_key: str,
    ) -> None:
        """Delete thread."""
        response = await threads_test_client.delete(
            "/v1/threads/thread_abc123",
            headers={"X-API-Key": test_api_key},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["object"] == "thread.deleted"
        assert data["deleted"] is True


class TestCreateMessage:
    """Tests for POST /v1/threads/{thread_id}/messages."""

    @pytest.mark.anyio
    async def test_create_message_success(
        self,
        threads_test_client: AsyncClient,
        test_api_key: str,
    ) -> None:
        """Create message in thread."""
        response = await threads_test_client.post(
            "/v1/threads/thread_abc123/messages",
            json={"role": "user", "content": "Hello"},
            headers={"X-API-Key": test_api_key},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["object"] == "thread.message"
        assert data["id"].startswith("msg_")


class TestListMessages:
    """Tests for GET /v1/threads/{thread_id}/messages."""

    @pytest.mark.anyio
    async def test_list_messages_success(
        self,
        threads_test_client: AsyncClient,
        test_api_key: str,
    ) -> None:
        """List messages in thread."""
        response = await threads_test_client.get(
            "/v1/threads/thread_abc123/messages",
            headers={"X-API-Key": test_api_key},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["object"] == "list"
        assert len(data["data"]) == 1


class TestGetMessage:
    """Tests for GET /v1/threads/{thread_id}/messages/{message_id}."""

    @pytest.mark.anyio
    async def test_get_message_success(
        self,
        threads_test_client: AsyncClient,
        test_api_key: str,
    ) -> None:
        """Get message by ID."""
        response = await threads_test_client.get(
            "/v1/threads/thread_abc123/messages/msg_abc123",
            headers={"X-API-Key": test_api_key},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["object"] == "thread.message"
        assert data["id"] == "msg_abc123"


class TestModifyMessage:
    """Tests for POST /v1/threads/{thread_id}/messages/{message_id}."""

    @pytest.mark.anyio
    async def test_modify_message_success(
        self,
        threads_test_client: AsyncClient,
        mock_message_service: AsyncMock,
        test_api_key: str,
    ) -> None:
        """Modify message metadata."""
        response = await threads_test_client.post(
            "/v1/threads/thread_abc123/messages/msg_abc123",
            json={"metadata": {"updated": "value"}},
            headers={"X-API-Key": test_api_key},
        )

        assert response.status_code == 200
        mock_message_service.modify_message.assert_called_once()


class TestCreateRun:
    """Tests for POST /v1/threads/{thread_id}/runs."""

    @pytest.mark.anyio
    async def test_create_run_success(
        self,
        threads_test_client: AsyncClient,
        test_api_key: str,
    ) -> None:
        """Create run in thread."""
        response = await threads_test_client.post(
            "/v1/threads/thread_abc123/runs",
            json={"assistant_id": "asst_xyz789"},
            headers={"X-API-Key": test_api_key},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["object"] == "thread.run"
        assert data["id"].startswith("run_")


class TestListRuns:
    """Tests for GET /v1/threads/{thread_id}/runs."""

    @pytest.mark.anyio
    async def test_list_runs_success(
        self,
        threads_test_client: AsyncClient,
        test_api_key: str,
    ) -> None:
        """List runs in thread."""
        response = await threads_test_client.get(
            "/v1/threads/thread_abc123/runs",
            headers={"X-API-Key": test_api_key},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["object"] == "list"
        assert len(data["data"]) == 1


class TestGetRun:
    """Tests for GET /v1/threads/{thread_id}/runs/{run_id}."""

    @pytest.mark.anyio
    async def test_get_run_success(
        self,
        threads_test_client: AsyncClient,
        test_api_key: str,
    ) -> None:
        """Get run by ID."""
        response = await threads_test_client.get(
            "/v1/threads/thread_abc123/runs/run_abc123",
            headers={"X-API-Key": test_api_key},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["object"] == "thread.run"
        assert data["id"] == "run_abc123"


class TestCancelRun:
    """Tests for POST /v1/threads/{thread_id}/runs/{run_id}/cancel."""

    @pytest.mark.anyio
    async def test_cancel_run_success(
        self,
        threads_test_client: AsyncClient,
        mock_run_service: AsyncMock,
        test_api_key: str,
    ) -> None:
        """Cancel a run."""
        # Update mock to return cancelled run
        cancelled_run = Run(
            id="run_abc123",
            thread_id="thread_abc123",
            assistant_id="asst_xyz789",
            created_at=1704067200,
            status="cancelled",
            model="gpt-4",
            tools=[],
            metadata={},
        )
        mock_run_service.cancel_run = AsyncMock(return_value=cancelled_run)

        response = await threads_test_client.post(
            "/v1/threads/thread_abc123/runs/run_abc123/cancel",
            headers={"X-API-Key": test_api_key},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "cancelled"
