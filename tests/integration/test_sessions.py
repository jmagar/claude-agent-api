"""Integration tests for session management (T041)."""

import json

import pytest
from httpx import AsyncClient
from httpx_sse import aconnect_sse


class TestSessionResumeIntegration:
    """Integration tests for session resume flow."""

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_query_creates_session_that_can_be_resumed(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_claude_sdk: None,
    ) -> None:
        """Test that a query creates a session that can be resumed."""
        # First query to create a session using SSE
        request_data = {"prompt": "Say hello"}

        events: list[dict[str, str]] = []
        async with aconnect_sse(
            async_client,
            "POST",
            "/api/v1/query",
            headers={**auth_headers, "Accept": "text/event-stream"},
            json=request_data,
        ) as event_source:
            async for sse in event_source.aiter_sse():
                if sse.event:
                    events.append({"event": sse.event, "data": sse.data})

        # Extract session ID from the init event
        init_events = [e for e in events if e["event"] == "init"]
        assert len(init_events) == 1
        init_data = json.loads(init_events[0]["data"])
        session_id = init_data["session_id"]
        assert session_id is not None

        # Resume the session
        resume_response = await async_client.post(
            f"/api/v1/sessions/{session_id}/resume",
            json={"prompt": "Continue the conversation"},
            headers=auth_headers,
        )
        assert resume_response.status_code == 200
        assert "text/event-stream" in resume_response.headers.get("content-type", "")

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_session_fork_creates_new_session(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_claude_sdk: None,
    ) -> None:
        """Test that forking creates a new session ID."""
        # First query to create a session using SSE
        request_data = {"prompt": "Count to 3"}

        events: list[dict[str, str]] = []
        async with aconnect_sse(
            async_client,
            "POST",
            "/api/v1/query",
            headers={**auth_headers, "Accept": "text/event-stream"},
            json=request_data,
        ) as event_source:
            async for sse in event_source.aiter_sse():
                if sse.event:
                    events.append({"event": sse.event, "data": sse.data})

        # Extract original session_id
        init_events = [e for e in events if e["event"] == "init"]
        assert len(init_events) == 1
        original_session_id = json.loads(init_events[0]["data"])["session_id"]

        # Fork the session using SSE
        fork_events: list[dict[str, str]] = []
        async with aconnect_sse(
            async_client,
            "POST",
            f"/api/v1/sessions/{original_session_id}/fork",
            headers={**auth_headers, "Accept": "text/event-stream"},
            json={"prompt": "Now count backwards from 3"},
        ) as event_source:
            async for sse in event_source.aiter_sse():
                if sse.event:
                    fork_events.append({"event": sse.event, "data": sse.data})

        # The forked session should have a different session_id
        fork_init_events = [e for e in fork_events if e["event"] == "init"]
        assert len(fork_init_events) == 1
        forked_session_id = json.loads(fork_init_events[0]["data"])["session_id"]

        assert forked_session_id != original_session_id

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_session_list_shows_created_sessions(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_claude_sdk: None,
    ) -> None:
        """Test that session list shows recently created sessions."""
        # Create a session using SSE
        request_data = {"prompt": "Test session listing"}

        events: list[dict[str, str]] = []
        async with aconnect_sse(
            async_client,
            "POST",
            "/api/v1/query",
            headers={**auth_headers, "Accept": "text/event-stream"},
            json=request_data,
        ) as event_source:
            async for sse in event_source.aiter_sse():
                if sse.event:
                    events.append({"event": sse.event, "data": sse.data})

        # Extract session ID
        init_events = [e for e in events if e["event"] == "init"]
        assert len(init_events) == 1
        session_id = json.loads(init_events[0]["data"])["session_id"]

        # Small delay to ensure database transaction commits
        import asyncio

        await asyncio.sleep(0.1)

        # List sessions
        list_response = await async_client.get(
            "/api/v1/sessions",
            headers=auth_headers,
        )
        assert list_response.status_code == 200
        data = list_response.json()

        # Session should appear in the list
        session_ids = [s["id"] for s in data["sessions"]]
        assert session_id in session_ids

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_session_detail_returns_session_info(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_claude_sdk: None,
    ) -> None:
        """Test that session detail returns session information."""
        # Create a session using SSE
        request_data = {"prompt": "Test session detail"}

        events: list[dict[str, str]] = []
        async with aconnect_sse(
            async_client,
            "POST",
            "/api/v1/query",
            headers={**auth_headers, "Accept": "text/event-stream"},
            json=request_data,
        ) as event_source:
            async for sse in event_source.aiter_sse():
                if sse.event:
                    events.append({"event": sse.event, "data": sse.data})

        # Extract session ID
        init_events = [e for e in events if e["event"] == "init"]
        assert len(init_events) == 1
        session_id = json.loads(init_events[0]["data"])["session_id"]

        # Get session detail
        detail_response = await async_client.get(
            f"/api/v1/sessions/{session_id}",
            headers=auth_headers,
        )
        assert detail_response.status_code == 200
        data = detail_response.json()

        assert data["id"] == session_id
        assert "status" in data
        assert "created_at" in data

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_single_query_session_is_persisted(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        mock_claude_sdk: None,
    ) -> None:
        """Test that sessions from /query/single are persisted and retrievable."""
        # Create a session via single query endpoint
        query_response = await async_client.post(
            "/api/v1/query/single",
            json={"prompt": "Test single query session persistence"},
            headers=auth_headers,
        )
        assert query_response.status_code == 200
        query_data = query_response.json()

        # Extract session_id from response
        session_id = query_data["session_id"]
        assert session_id is not None

        # Verify session can be retrieved
        detail_response = await async_client.get(
            f"/api/v1/sessions/{session_id}",
            headers=auth_headers,
        )
        assert detail_response.status_code == 200
        session_data = detail_response.json()

        # Verify session details
        assert session_data["id"] == session_id
        assert session_data["status"] in ["active", "completed", "error"]
        assert "created_at" in session_data
        assert "model" in session_data


class TestSessionListFiltering:
    """Integration tests for session list filtering."""

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_list_sessions_filters_by_mode(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test filtering sessions by mode parameter."""
        from uuid import uuid4

        from apps.api.adapters.session_repo import SessionRepository
        from apps.api.dependencies import get_db

        # Create sessions with different modes
        db_gen = get_db()
        db_session = await anext(db_gen)
        try:
            repo = SessionRepository(db_session)

            # Create brainstorm session
            brainstorm_session = await repo.create(
                session_id=uuid4(),
                model="sonnet",
                metadata={"mode": "brainstorm", "title": "Brainstorm Session"},
                owner_api_key=auth_headers["X-API-Key"],
            )

            # Create code session
            code_session = await repo.create(
                session_id=uuid4(),
                model="sonnet",
                metadata={"mode": "code", "title": "Code Session"},
                owner_api_key=auth_headers["X-API-Key"],
            )

            # Query with mode filter for brainstorm
            response = await async_client.get(
                "/api/v1/sessions?mode=brainstorm",
                headers=auth_headers,
            )
            assert response.status_code == 200
            data = response.json()

            # Assert only brainstorm sessions returned
            session_ids = [s["id"] for s in data["sessions"]]
            assert str(brainstorm_session.id) in session_ids
            assert str(code_session.id) not in session_ids

            # All returned sessions should be brainstorm mode
            for session in data["sessions"]:
                assert session["mode"] == "brainstorm"

        finally:
            await db_gen.aclose()

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_list_sessions_filters_by_project_id(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test filtering sessions by project_id parameter."""
        from uuid import uuid4

        from apps.api.adapters.session_repo import SessionRepository
        from apps.api.dependencies import get_db

        project_a = "project-alpha"
        project_b = "project-beta"

        db_gen = get_db()
        db_session = await anext(db_gen)
        try:
            repo = SessionRepository(db_session)

            # Create sessions in different projects
            session_a = await repo.create(
                session_id=uuid4(),
                model="sonnet",
                metadata={"project_id": project_a, "title": "Session A"},
                owner_api_key=auth_headers["X-API-Key"],
            )

            session_b = await repo.create(
                session_id=uuid4(),
                model="sonnet",
                metadata={"project_id": project_b, "title": "Session B"},
                owner_api_key=auth_headers["X-API-Key"],
            )

            # Query with project_id filter
            response = await async_client.get(
                f"/api/v1/sessions?project_id={project_a}",
                headers=auth_headers,
            )
            assert response.status_code == 200
            data = response.json()

            # Assert only project_a sessions returned
            session_ids = [s["id"] for s in data["sessions"]]
            assert str(session_a.id) in session_ids
            assert str(session_b.id) not in session_ids

        finally:
            await db_gen.aclose()

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_list_sessions_filters_by_tags(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test filtering sessions by tags parameter."""
        from uuid import uuid4

        from apps.api.adapters.session_repo import SessionRepository
        from apps.api.dependencies import get_db

        db_gen = get_db()
        db_session = await anext(db_gen)
        try:
            repo = SessionRepository(db_session)

            # Create sessions with different tags
            tagged_session = await repo.create(
                session_id=uuid4(),
                model="sonnet",
                metadata={
                    "tags": ["important", "feature-x"],
                    "title": "Tagged Session",
                },
                owner_api_key=auth_headers["X-API-Key"],
            )

            untagged_session = await repo.create(
                session_id=uuid4(),
                model="sonnet",
                metadata={"tags": ["unrelated"], "title": "Untagged Session"},
                owner_api_key=auth_headers["X-API-Key"],
            )

            # Query with tags filter (all tags must match)
            response = await async_client.get(
                "/api/v1/sessions?tags=important&tags=feature-x",
                headers=auth_headers,
            )
            assert response.status_code == 200
            data = response.json()

            # Assert only sessions with ALL tags returned
            session_ids = [s["id"] for s in data["sessions"]]
            assert str(tagged_session.id) in session_ids
            assert str(untagged_session.id) not in session_ids

        finally:
            await db_gen.aclose()

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_list_sessions_search_by_title(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test searching sessions by title."""
        from uuid import uuid4

        from apps.api.adapters.session_repo import SessionRepository
        from apps.api.dependencies import get_db

        db_gen = get_db()
        db_session = await anext(db_gen)
        try:
            repo = SessionRepository(db_session)

            # Create sessions with different titles
            matching_session = await repo.create(
                session_id=uuid4(),
                model="sonnet",
                metadata={"title": "Implement authentication feature"},
                owner_api_key=auth_headers["X-API-Key"],
            )

            non_matching_session = await repo.create(
                session_id=uuid4(),
                model="sonnet",
                metadata={"title": "Fix database migration"},
                owner_api_key=auth_headers["X-API-Key"],
            )

            # Query with search parameter (case-insensitive)
            response = await async_client.get(
                "/api/v1/sessions?search=authentication",
                headers=auth_headers,
            )
            assert response.status_code == 200
            data = response.json()

            # Assert only matching sessions returned
            session_ids = [s["id"] for s in data["sessions"]]
            assert str(matching_session.id) in session_ids
            assert str(non_matching_session.id) not in session_ids

        finally:
            await db_gen.aclose()


class TestSessionListPagination:
    """Integration tests for session list pagination."""

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_list_sessions_pagination_empty_results(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test pagination returns empty results when no sessions exist."""
        response = await async_client.get(
            "/api/v1/sessions?page=1&page_size=10",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()

        assert data["sessions"] == []
        assert data["total"] >= 0
        assert data["page"] == 1
        assert data["page_size"] == 10

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_list_sessions_pagination_last_page(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test pagination correctly handles last page."""
        from uuid import uuid4

        from apps.api.adapters.session_repo import SessionRepository
        from apps.api.dependencies import get_db

        db_gen = get_db()
        db_session = await anext(db_gen)
        try:
            repo = SessionRepository(db_session)

            # Create exactly 3 sessions
            for i in range(3):
                await repo.create(
                    session_id=uuid4(),
                    model="sonnet",
                    metadata={"title": f"Session {i}"},
                    owner_api_key=auth_headers["X-API-Key"],
                )

            # Request page 2 with page_size=2 (should return 1 item)
            response = await async_client.get(
                "/api/v1/sessions?page=2&page_size=2",
                headers=auth_headers,
            )
            assert response.status_code == 200
            data = response.json()

            assert len(data["sessions"]) == 1
            assert data["total"] == 3
            assert data["page"] == 2
            assert data["page_size"] == 2

        finally:
            await db_gen.aclose()

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_list_sessions_pagination_beyond_last_page(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test pagination returns empty when requesting beyond last page."""
        from uuid import uuid4

        from apps.api.adapters.session_repo import SessionRepository
        from apps.api.dependencies import get_db

        db_gen = get_db()
        db_session = await anext(db_gen)
        try:
            repo = SessionRepository(db_session)

            # Create 2 sessions
            for i in range(2):
                await repo.create(
                    session_id=uuid4(),
                    model="sonnet",
                    metadata={"title": f"Session {i}"},
                    owner_api_key=auth_headers["X-API-Key"],
                )

            # Request page 10 (beyond available data)
            response = await async_client.get(
                "/api/v1/sessions?page=10&page_size=10",
                headers=auth_headers,
            )
            assert response.status_code == 200
            data = response.json()

            assert data["sessions"] == []
            assert data["total"] == 2
            assert data["page"] == 10

        finally:
            await db_gen.aclose()


class TestSessionUpdates:
    """Integration tests for session update operations."""

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_update_session_tags_validates_list(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test updating session tags with valid list."""
        from uuid import uuid4

        from apps.api.adapters.session_repo import SessionRepository
        from apps.api.dependencies import get_db

        db_gen = get_db()
        db_session = await anext(db_gen)
        try:
            repo = SessionRepository(db_session)

            # Create session
            session = await repo.create(
                session_id=uuid4(),
                model="sonnet",
                metadata={"tags": ["old-tag"]},
                owner_api_key=auth_headers["X-API-Key"],
            )

            # Update tags
            response = await async_client.patch(
                f"/api/v1/sessions/{session.id}/tags",
                json={"tags": ["new-tag-1", "new-tag-2"]},
                headers=auth_headers,
            )
            assert response.status_code == 200
            data = response.json()

            assert data["id"] == str(session.id)
            assert data["tags"] == ["new-tag-1", "new-tag-2"]

        finally:
            await db_gen.aclose()

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_update_session_tags_rejects_non_list(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test updating session tags rejects non-list values."""
        from uuid import uuid4

        from apps.api.adapters.session_repo import SessionRepository
        from apps.api.dependencies import get_db

        db_gen = get_db()
        db_session = await anext(db_gen)
        try:
            repo = SessionRepository(db_session)

            # Create session
            session = await repo.create(
                session_id=uuid4(),
                model="sonnet",
                owner_api_key=auth_headers["X-API-Key"],
            )

            # Attempt to update tags with non-list value
            response = await async_client.patch(
                f"/api/v1/sessions/{session.id}/tags",
                json={"tags": "not-a-list"},
                headers=auth_headers,
            )
            assert response.status_code == 400
            data = response.json()

            assert data["code"] == "VALIDATION_ERROR"
            assert "must be a list" in data["message"].lower()

        finally:
            await db_gen.aclose()

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_update_session_metadata(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test updating session metadata preserves existing fields."""
        from uuid import uuid4

        from apps.api.adapters.session_repo import SessionRepository
        from apps.api.dependencies import get_db

        db_gen = get_db()
        db_session = await anext(db_gen)
        try:
            repo = SessionRepository(db_session)

            # Create session with initial metadata
            session = await repo.create(
                session_id=uuid4(),
                model="sonnet",
                metadata={"title": "Original Title", "project_id": "proj-123"},
                owner_api_key=auth_headers["X-API-Key"],
            )

            # Update tags (should preserve other metadata)
            response = await async_client.patch(
                f"/api/v1/sessions/{session.id}/tags",
                json={"tags": ["tag1"]},
                headers=auth_headers,
            )
            assert response.status_code == 200
            data = response.json()

            # Verify metadata preserved
            assert data["title"] == "Original Title"
            assert data["project_id"] == "proj-123"
            assert data["tags"] == ["tag1"]

        finally:
            await db_gen.aclose()


class TestSessionPromotion:
    """Integration tests for session promotion."""

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_promote_session_to_code_mode(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test promoting a brainstorm session to code mode."""
        from uuid import uuid4

        from apps.api.adapters.session_repo import SessionRepository
        from apps.api.dependencies import get_db

        db_gen = get_db()
        db_session = await anext(db_gen)
        try:
            repo = SessionRepository(db_session)

            # Create brainstorm session
            session = await repo.create(
                session_id=uuid4(),
                model="sonnet",
                metadata={"mode": "brainstorm", "title": "Brainstorm Session"},
                owner_api_key=auth_headers["X-API-Key"],
            )

            # Promote to code mode
            response = await async_client.post(
                f"/api/v1/sessions/{session.id}/promote",
                json={"project_id": "project-123"},
                headers=auth_headers,
            )
            assert response.status_code == 200
            data = response.json()

            # Verify mode changed and project_id set
            assert data["id"] == str(session.id)
            assert data["mode"] == "code"
            assert data["project_id"] == "project-123"

        finally:
            await db_gen.aclose()

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_promote_session_validates_mode(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that promotion always sets mode to code."""
        from uuid import uuid4

        from apps.api.adapters.session_repo import SessionRepository
        from apps.api.dependencies import get_db

        db_gen = get_db()
        db_session = await anext(db_gen)
        try:
            repo = SessionRepository(db_session)

            # Create session already in code mode
            session = await repo.create(
                session_id=uuid4(),
                model="sonnet",
                metadata={"mode": "code"},
                owner_api_key=auth_headers["X-API-Key"],
            )

            # Promote (should still work, mode remains code)
            response = await async_client.post(
                f"/api/v1/sessions/{session.id}/promote",
                json={"project_id": "project-456"},
                headers=auth_headers,
            )
            assert response.status_code == 200
            data = response.json()

            assert data["mode"] == "code"
            assert data["project_id"] == "project-456"

        finally:
            await db_gen.aclose()

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_promote_session_requires_permission(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that promotion requires ownership of the session."""
        from uuid import uuid4

        from apps.api.adapters.session_repo import SessionRepository
        from apps.api.dependencies import get_db

        db_gen = get_db()
        db_session = await anext(db_gen)
        try:
            repo = SessionRepository(db_session)

            # Create session owned by different API key
            session = await repo.create(
                session_id=uuid4(),
                model="sonnet",
                metadata={"mode": "brainstorm"},
                owner_api_key="different-api-key",
            )

            # Attempt to promote with wrong API key
            response = await async_client.post(
                f"/api/v1/sessions/{session.id}/promote",
                json={"project_id": "project-789"},
                headers=auth_headers,
            )
            assert response.status_code == 404  # Not found (authorization check)
            data = response.json()

            assert data["code"] == "SESSION_NOT_FOUND"

        finally:
            await db_gen.aclose()


class TestSessionErrorCases:
    """Integration tests for session error cases."""

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_update_session_404_for_unknown_id(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test updating tags for non-existent session returns 404."""
        from uuid import uuid4

        unknown_id = str(uuid4())

        response = await async_client.patch(
            f"/api/v1/sessions/{unknown_id}/tags",
            json={"tags": ["tag1"]},
            headers=auth_headers,
        )
        assert response.status_code == 404
        data = response.json()

        assert data["code"] == "SESSION_NOT_FOUND"
        assert unknown_id in data["message"]

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_get_session_404_for_unknown_id(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test getting non-existent session returns 404."""
        from uuid import uuid4

        unknown_id = str(uuid4())

        response = await async_client.get(
            f"/api/v1/sessions/{unknown_id}",
            headers=auth_headers,
        )
        assert response.status_code == 404
        data = response.json()

        assert data["code"] == "SESSION_NOT_FOUND"

    @pytest.mark.integration
    @pytest.mark.anyio
    async def test_promote_session_404_for_unknown_id(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test promoting non-existent session returns 404."""
        from uuid import uuid4

        unknown_id = str(uuid4())

        response = await async_client.post(
            f"/api/v1/sessions/{unknown_id}/promote",
            json={"project_id": "project-123"},
            headers=auth_headers,
        )
        assert response.status_code == 404
        data = response.json()

        assert data["code"] == "SESSION_NOT_FOUND"
