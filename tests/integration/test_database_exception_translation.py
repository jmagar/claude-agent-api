"""Integration tests for database exception translation to APIError.

Tests verify that raw database exceptions (IntegrityError, OperationalError)
are properly translated to user-friendly APIError responses with correct
status codes and error codes.

These tests ensure:
1. No raw database exceptions leak to users
2. Proper HTTP status codes (409, 503, 500)
3. Machine-readable error codes
4. Security - no internal details leaked
"""

import pytest
from sqlalchemy.exc import IntegrityError, OperationalError
from unittest.mock import AsyncMock, patch

from apps.api.exceptions.base import APIError


class TestSessionServiceExceptionTranslation:
    """Test session service translates database exceptions."""

    @pytest.mark.integration
    async def test_session_create_integrity_error_returns_409(
        self, session_service_with_mocked_db
    ) -> None:
        """IntegrityError during session creation returns 409 ALREADY_EXISTS."""
        service, mock_repo = session_service_with_mocked_db

        # Simulate duplicate session ID
        mock_repo.create.side_effect = IntegrityError(
            "duplicate key value",
            params={},
            orig=Exception("session_id already exists"),
        )

        with pytest.raises(APIError) as exc_info:
            await service.create_session(
                api_key="test-key-123",
                model="sonnet",
            )

        assert exc_info.value.status_code == 409
        assert exc_info.value.code == "ALREADY_EXISTS"
        assert "already exists" in exc_info.value.message.lower()
        # Security: ensure no raw database details leaked
        assert "duplicate key" not in exc_info.value.message

    @pytest.mark.integration
    async def test_session_create_operational_error_returns_503(
        self, session_service_with_mocked_db
    ) -> None:
        """OperationalError during session creation returns 503 DATABASE_UNAVAILABLE."""
        service, mock_repo = session_service_with_mocked_db

        # Simulate database connection failure
        mock_repo.create.side_effect = OperationalError(
            "could not connect to server",
            params={},
            orig=Exception("Connection refused"),
        )

        with pytest.raises(APIError) as exc_info:
            await service.create_session(
                api_key="test-key-123",
                model="sonnet",
            )

        assert exc_info.value.status_code == 503
        assert exc_info.value.code == "DATABASE_UNAVAILABLE"
        assert "temporarily unavailable" in exc_info.value.message.lower()
        # Security: ensure no connection details leaked
        assert "Connection refused" not in exc_info.value.message

    @pytest.mark.integration
    async def test_session_create_generic_error_returns_500(
        self, session_service_with_mocked_db
    ) -> None:
        """Generic Exception during session creation returns 500 INTERNAL_ERROR."""
        service, mock_repo = session_service_with_mocked_db

        # Simulate unexpected error
        mock_repo.create.side_effect = Exception("Unexpected internal error")

        with pytest.raises(APIError) as exc_info:
            await service.create_session(
                api_key="test-key-123",
                model="sonnet",
            )

        assert exc_info.value.status_code == 500
        assert exc_info.value.code == "INTERNAL_ERROR"
        assert "failed to create session" in exc_info.value.message.lower()
        # Security: ensure no internal error details leaked
        assert "Unexpected internal error" not in exc_info.value.message


class TestAssistantServiceExceptionTranslation:
    """Test assistant service translates database exceptions."""

    @pytest.mark.integration
    async def test_assistant_create_integrity_error_returns_409(
        self, assistant_service_with_mocked_db
    ) -> None:
        """IntegrityError during assistant creation returns 409 ALREADY_EXISTS."""
        service, mock_repo = assistant_service_with_mocked_db

        # Simulate duplicate assistant ID
        mock_repo.create.side_effect = IntegrityError(
            "duplicate key value",
            params={},
            orig=Exception("assistant_id already exists"),
        )

        with pytest.raises(APIError) as exc_info:
            await service.create_assistant(
                api_key="test-key-123",
                name="Test Assistant",
                model="sonnet",
            )

        assert exc_info.value.status_code == 409
        assert exc_info.value.code == "ALREADY_EXISTS"
        assert "already exists" in exc_info.value.message.lower()

    @pytest.mark.integration
    async def test_assistant_create_operational_error_returns_503(
        self, assistant_service_with_mocked_db
    ) -> None:
        """OperationalError during assistant creation returns 503 DATABASE_UNAVAILABLE."""
        service, mock_repo = assistant_service_with_mocked_db

        # Simulate database connection failure
        mock_repo.create.side_effect = OperationalError(
            "server closed the connection",
            params={},
            orig=Exception("Connection lost"),
        )

        with pytest.raises(APIError) as exc_info:
            await service.create_assistant(
                api_key="test-key-123",
                name="Test Assistant",
                model="sonnet",
            )

        assert exc_info.value.status_code == 503
        assert exc_info.value.code == "DATABASE_UNAVAILABLE"
        assert "temporarily unavailable" in exc_info.value.message.lower()


class TestSessionRepositoryExceptionTranslation:
    """Test session repository translates database exceptions."""

    @pytest.mark.integration
    async def test_add_message_integrity_error_returns_409(
        self, db_session
    ) -> None:
        """IntegrityError during add_message returns 409 ALREADY_EXISTS."""
        from apps.api.adapters.session_repo import SessionRepository
        from uuid import uuid4

        repo = SessionRepository(db_session)
        session_id = uuid4()

        # Mock database commit to raise IntegrityError
        with patch.object(
            db_session, "commit", side_effect=IntegrityError(
                "duplicate message",
                params={},
                orig=Exception("message_id already exists"),
            )
        ):
            with pytest.raises(APIError) as exc_info:
                await repo.add_message(
                    session_id=session_id,
                    message_type="user",
                    content="test message",
                )

        assert exc_info.value.status_code == 409
        assert exc_info.value.code == "ALREADY_EXISTS"
        assert "already exists" in exc_info.value.message.lower()

    @pytest.mark.integration
    async def test_add_message_operational_error_returns_503(
        self, db_session
    ) -> None:
        """OperationalError during add_message returns 503 DATABASE_UNAVAILABLE."""
        from apps.api.adapters.session_repo import SessionRepository
        from uuid import uuid4

        repo = SessionRepository(db_session)
        session_id = uuid4()

        # Mock database commit to raise OperationalError
        with patch.object(
            db_session, "commit", side_effect=OperationalError(
                "database locked",
                params={},
                orig=Exception("LOCK TIMEOUT"),
            )
        ):
            with pytest.raises(APIError) as exc_info:
                await repo.add_message(
                    session_id=session_id,
                    message_type="user",
                    content="test message",
                )

        assert exc_info.value.status_code == 503
        assert exc_info.value.code == "DATABASE_UNAVAILABLE"
        assert "temporarily unavailable" in exc_info.value.message.lower()

    @pytest.mark.integration
    async def test_add_checkpoint_integrity_error_returns_409(
        self, db_session
    ) -> None:
        """IntegrityError during add_checkpoint returns 409 ALREADY_EXISTS."""
        from apps.api.adapters.session_repo import SessionRepository
        from uuid import uuid4

        repo = SessionRepository(db_session)
        session_id = uuid4()
        user_message_uuid = uuid4()

        # Mock database commit to raise IntegrityError
        with patch.object(
            db_session, "commit", side_effect=IntegrityError(
                "duplicate checkpoint",
                params={},
                orig=Exception("checkpoint_id already exists"),
            )
        ):
            with pytest.raises(APIError) as exc_info:
                await repo.add_checkpoint(
                    session_id=session_id,
                    user_message_uuid=user_message_uuid,
                    files_modified=["test.py"],
                )

        assert exc_info.value.status_code == 409
        assert exc_info.value.code == "ALREADY_EXISTS"
        assert "already exists" in exc_info.value.message.lower()

    @pytest.mark.integration
    async def test_add_checkpoint_operational_error_returns_503(
        self, db_session
    ) -> None:
        """OperationalError during add_checkpoint returns 503 DATABASE_UNAVAILABLE."""
        from apps.api.adapters.session_repo import SessionRepository
        from uuid import uuid4

        repo = SessionRepository(db_session)
        session_id = uuid4()
        user_message_uuid = uuid4()

        # Mock database commit to raise OperationalError
        with patch.object(
            db_session, "commit", side_effect=OperationalError(
                "deadlock detected",
                params={},
                orig=Exception("DEADLOCK"),
            )
        ):
            with pytest.raises(APIError) as exc_info:
                await repo.add_checkpoint(
                    session_id=session_id,
                    user_message_uuid=user_message_uuid,
                    files_modified=["test.py"],
                )

        assert exc_info.value.status_code == 503
        assert exc_info.value.code == "DATABASE_UNAVAILABLE"
        assert "temporarily unavailable" in exc_info.value.message.lower()


# Fixtures for mocked services
@pytest.fixture
def session_service_with_mocked_db():
    """Session service with mocked database repository."""
    from apps.api.services.session import SessionService

    mock_repo = AsyncMock()
    service = SessionService(
        settings=None,  # type: ignore
        cache=None,
        db_repo=mock_repo,
    )
    return service, mock_repo


@pytest.fixture
def assistant_service_with_mocked_db():
    """Assistant service with mocked database repository."""
    from apps.api.services.assistants.assistant_service import AssistantService

    mock_repo = AsyncMock()
    service = AssistantService(
        settings=None,  # type: ignore
        cache=None,
        db_repo=mock_repo,
    )
    return service, mock_repo
