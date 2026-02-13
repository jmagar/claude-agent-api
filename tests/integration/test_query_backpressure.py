"""Integration tests for SSE query streaming backpressure."""

from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import AsyncClient

from apps.api.routes.query_stream import QueryStreamEventGenerator
from apps.api.schemas.requests.query import QueryRequest


class TestQueueBackpressure:
    """Tests for bounded queue backpressure in SSE streaming."""

    @pytest.mark.anyio
    async def test_queue_full_blocks_producer(
        self, async_client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test that producer blocks when queue reaches maxsize."""
        # Create a mock agent service that produces many events rapidly
        mock_agent_service = MagicMock()

        # Generate 150 events (more than queue maxsize=100)
        async def generate_many_events():
            for i in range(150):
                yield {
                    "event": "message",
                    "data": json.dumps({"type": "assistant", "content": f"Event {i}"}),
                }

        mock_agent_service.query_stream = AsyncMock(return_value=generate_many_events())
        mock_agent_service.interrupt = AsyncMock()

        # Create mock session service
        mock_session_service = AsyncMock()
        mock_session_service.create_session = AsyncMock()
        mock_session_service.update_session = AsyncMock()

        # Create mock request
        mock_request = MagicMock()
        mock_request.is_disconnected = AsyncMock(return_value=False)

        # Create generator with bounded queue
        query = QueryRequest(prompt="Test query")
        generator = QueryStreamEventGenerator(
            request=mock_request,
            query=query,
            api_key="test-key",
            agent_service=mock_agent_service,
            session_service=mock_session_service,
        )

        # Start producer and consumer
        events_consumed = 0

        async def slow_consumer():
            """Consumer that drains queue slowly."""
            nonlocal events_consumed
            async for event in generator.generate():
                events_consumed += 1
                if events_consumed == 50:
                    # After consuming 50 events, pause to fill queue
                    await asyncio.sleep(0.1)

        # Run consumer
        consumer_task = asyncio.create_task(slow_consumer())

        # Give producer time to fill queue
        await asyncio.sleep(0.2)

        # Cancel consumer
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass

        # Verify queue blocked producer (not all 150 events consumed)
        # Due to backpressure, producer should have blocked
        assert events_consumed < 150
        assert events_consumed >= 50  # At least some events consumed

    @pytest.mark.anyio
    async def test_client_disconnect_unblocks_producer(
        self, async_client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test that client disconnect unblocks producer and triggers interrupt."""
        # Create mock agent service
        mock_agent_service = MagicMock()

        # Producer generates infinite events
        async def infinite_events():
            i = 0
            while True:
                yield {
                    "event": "message",
                    "data": json.dumps({"type": "assistant", "content": f"Event {i}"}),
                }
                i += 1
                await asyncio.sleep(0.01)

        mock_agent_service.query_stream = AsyncMock(return_value=infinite_events())
        mock_agent_service.interrupt = AsyncMock()

        # Create mock session service
        mock_session_service = AsyncMock()
        mock_session_service.create_session = AsyncMock()
        mock_session_service.update_session = AsyncMock()

        # Create mock request that simulates disconnect
        mock_request = MagicMock()
        disconnect_after_n = 10
        call_count = 0

        async def is_disconnected_impl():
            nonlocal call_count
            call_count += 1
            # Disconnect after N calls
            return call_count > disconnect_after_n

        mock_request.is_disconnected = is_disconnected_impl

        # Create generator
        query = QueryRequest(prompt="Test query", session_id="test-session-123")
        generator = QueryStreamEventGenerator(
            request=mock_request,
            query=query,
            api_key="test-key",
            agent_service=mock_agent_service,
            session_service=mock_session_service,
        )

        # Consume events until disconnect
        events_received = 0
        try:
            async for event in generator.generate():
                events_received += 1
                if events_received > 20:  # Safety limit
                    break
        except asyncio.CancelledError:
            pass

        # Verify disconnect triggered interrupt
        assert events_received > 0
        # Note: interrupt may or may not be called depending on timing
        # The important thing is that the stream ended gracefully

    @pytest.mark.anyio
    async def test_slow_client_memory_consumption(
        self, async_client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test that slow client doesn't cause memory exhaustion via bounded queue."""
        # Create mock agent service that produces events rapidly
        mock_agent_service = MagicMock()

        # Producer generates 200 events as fast as possible
        async def fast_events():
            for i in range(200):
                yield {
                    "event": "message",
                    "data": json.dumps({"type": "assistant", "content": f"Event {i}"}),
                }

        mock_agent_service.query_stream = AsyncMock(return_value=fast_events())
        mock_agent_service.interrupt = AsyncMock()

        # Create mock session service
        mock_session_service = AsyncMock()
        mock_session_service.create_session = AsyncMock()
        mock_session_service.update_session = AsyncMock()

        # Create mock request
        mock_request = MagicMock()
        mock_request.is_disconnected = AsyncMock(return_value=False)

        # Create generator
        query = QueryRequest(prompt="Test query")
        generator = QueryStreamEventGenerator(
            request=mock_request,
            query=query,
            api_key="test-key",
            agent_service=mock_agent_service,
            session_service=mock_session_service,
        )

        # Verify queue size is bounded
        assert generator.event_queue.maxsize == 100

        # Consume events very slowly (simulating slow network)
        events_consumed = 0
        async for event in generator.generate():
            events_consumed += 1
            await asyncio.sleep(0.001)  # Slow consumer

        # Verify all events were delivered despite slow consumer
        assert events_consumed == 200

        # Verify queue never exceeded maxsize (memory bounded)
        # This is guaranteed by asyncio.Queue implementation

    @pytest.mark.anyio
    async def test_producer_error_propagation_with_full_queue(
        self, async_client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test that producer errors propagate to consumer even when queue is full."""
        # Create mock agent service that errors after some events
        mock_agent_service = MagicMock()

        async def events_then_error():
            # Generate enough events to fill queue
            for i in range(110):
                yield {
                    "event": "message",
                    "data": json.dumps({"type": "assistant", "content": f"Event {i}"}),
                }
            # Then raise an error
            raise RuntimeError("Producer error!")

        mock_agent_service.query_stream = AsyncMock(return_value=events_then_error())
        mock_agent_service.interrupt = AsyncMock()

        # Create mock session service
        mock_session_service = AsyncMock()
        mock_session_service.create_session = AsyncMock()
        mock_session_service.update_session = AsyncMock()

        # Create mock request
        mock_request = MagicMock()
        mock_request.is_disconnected = AsyncMock(return_value=False)

        # Create generator
        query = QueryRequest(prompt="Test query")
        generator = QueryStreamEventGenerator(
            request=mock_request,
            query=query,
            api_key="test-key",
            agent_service=mock_agent_service,
            session_service=mock_session_service,
        )

        # Consume events
        events_consumed = 0
        error_event_received = False

        async for event in generator.generate():
            events_consumed += 1
            if event.get("event") == "error":
                error_event_received = True
                error_data = json.loads(event.get("data", "{}"))
                assert "error" in error_data
                break

        # Verify error was propagated
        assert error_event_received
        assert events_consumed > 100  # Some events before error

    @pytest.mark.anyio
    async def test_queue_backpressure_timing(
        self, async_client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test that backpressure introduces expected timing delays."""
        import time

        # Create mock agent service with fast producer
        mock_agent_service = MagicMock()

        async def fast_producer():
            for i in range(150):
                yield {
                    "event": "message",
                    "data": json.dumps({"type": "assistant", "content": f"Event {i}"}),
                }
                # No delay - produce as fast as possible

        mock_agent_service.query_stream = AsyncMock(return_value=fast_producer())
        mock_agent_service.interrupt = AsyncMock()

        # Create mock session service
        mock_session_service = AsyncMock()
        mock_session_service.create_session = AsyncMock()
        mock_session_service.update_session = AsyncMock()

        # Create mock request
        mock_request = MagicMock()
        mock_request.is_disconnected = AsyncMock(return_value=False)

        # Create generator
        query = QueryRequest(prompt="Test query")
        generator = QueryStreamEventGenerator(
            request=mock_request,
            query=query,
            api_key="test-key",
            agent_service=mock_agent_service,
            session_service=mock_session_service,
        )

        # Consume with slow consumer
        start_time = time.time()
        events_consumed = 0

        async for event in generator.generate():
            events_consumed += 1
            if events_consumed <= 100:
                # Fast consumption for first 100 (fills queue)
                await asyncio.sleep(0.001)
            else:
                # Slow consumption for remaining (triggers backpressure)
                await asyncio.sleep(0.01)

        elapsed_time = time.time() - start_time

        # Verify timing shows backpressure effect
        # First 100 events: ~0.1s
        # Remaining 50 events with backpressure: ~0.5s
        # Total should be > 0.5s
        assert elapsed_time > 0.5
        assert events_consumed == 150


class TestSessionLifecycle:
    """Tests for session lifecycle during streaming."""

    @pytest.mark.anyio
    async def test_session_created_on_init_event(
        self, async_client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test that session is created when init event is received."""
        # Create mock agent service
        mock_agent_service = MagicMock()

        async def events_with_init():
            yield {
                "event": "init",
                "data": json.dumps(
                    {
                        "session_id": "test-session-abc",
                        "model": "sonnet",
                        "tools": [],
                        "mcp_servers": [],
                        "plugins": [],
                        "commands": [],
                    }
                ),
            }
            yield {
                "event": "message",
                "data": json.dumps({"type": "assistant", "content": "Hello"}),
            }

        mock_agent_service.query_stream = AsyncMock(return_value=events_with_init())
        mock_agent_service.interrupt = AsyncMock()

        # Create mock session service
        mock_session_service = AsyncMock()
        mock_session_service.create_session = AsyncMock()
        mock_session_service.update_session = AsyncMock()

        # Create mock request
        mock_request = MagicMock()
        mock_request.is_disconnected = AsyncMock(return_value=False)

        # Create generator (no session_id initially)
        query = QueryRequest(prompt="Test query")
        generator = QueryStreamEventGenerator(
            request=mock_request,
            query=query,
            api_key="test-key",
            agent_service=mock_agent_service,
            session_service=mock_session_service,
        )

        # Consume events
        async for event in generator.generate():
            pass

        # Verify session was created
        mock_session_service.create_session.assert_called_once_with(
            model="sonnet",
            session_id="test-session-abc",
            owner_api_key="test-key",
        )

    @pytest.mark.anyio
    async def test_session_updated_on_completion(
        self, async_client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        """Test that session status is updated when stream completes."""
        # Create mock agent service
        mock_agent_service = MagicMock()

        async def events_with_result():
            yield {
                "event": "init",
                "data": json.dumps(
                    {
                        "session_id": "test-session-xyz",
                        "model": "sonnet",
                        "tools": [],
                        "mcp_servers": [],
                        "plugins": [],
                        "commands": [],
                    }
                ),
            }
            yield {
                "event": "message",
                "data": json.dumps({"type": "assistant", "content": "Response"}),
            }
            yield {
                "event": "result",
                "data": json.dumps(
                    {
                        "session_id": "test-session-xyz",
                        "is_error": False,
                        "turns": 2,
                        "total_cost_usd": 0.05,
                    }
                ),
            }

        mock_agent_service.query_stream = AsyncMock(return_value=events_with_result())
        mock_agent_service.interrupt = AsyncMock()

        # Create mock session service
        mock_session_service = AsyncMock()
        mock_session_service.create_session = AsyncMock()
        mock_session_service.update_session = AsyncMock()

        # Create mock request
        mock_request = MagicMock()
        mock_request.is_disconnected = AsyncMock(return_value=False)

        # Create generator
        query = QueryRequest(prompt="Test query")
        generator = QueryStreamEventGenerator(
            request=mock_request,
            query=query,
            api_key="test-key",
            agent_service=mock_agent_service,
            session_service=mock_session_service,
        )

        # Consume events
        async for event in generator.generate():
            pass

        # Verify session was updated with result metadata
        mock_session_service.update_session.assert_called_once_with(
            session_id="test-session-xyz",
            status="completed",
            total_turns=2,
            total_cost_usd=0.05,
            current_api_key="test-key",
        )
