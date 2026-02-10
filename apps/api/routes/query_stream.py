"""Stream event generator for query streaming endpoint."""

import asyncio
import contextlib
import json
from collections.abc import AsyncGenerator
from typing import Literal

import structlog
from fastapi import Request

from apps.api.protocols import AgentService
from apps.api.schemas.requests.query import QueryRequest
from apps.api.services.session import SessionService
from apps.api.utils.crypto import hash_api_key

logger = structlog.get_logger(__name__)


class QueryStreamEventGenerator:
    """Generates SSE events for streaming query responses.

    Handles producer-consumer pattern with bounded queue for backpressure,
    session lifecycle management, and client disconnect detection.
    """

    def __init__(
        self,
        request: Request,
        query: QueryRequest,
        api_key: str,
        agent_service: AgentService,
        session_service: SessionService,
    ) -> None:
        """Initialize event generator.

        Args:
            request: FastAPI request for disconnect detection.
            query: Query request with prompt and config.
            api_key: Authenticated API key.
            agent_service: Agent service for query execution.
            session_service: Session service for state management.
        """
        self.request = request
        self.query = query
        self.api_key = api_key
        self.agent_service = agent_service
        self.session_service = session_service

        # Session tracking state
        self.session_id: str | None = query.session_id
        self.is_error = False
        self.num_turns = 0
        self.total_cost_usd: float | None = None

        # Bounded queue for backpressure control (prevents memory exhaustion)
        # maxsize=100: When queue fills, producer blocks until consumer drains events.
        # This prevents fast SDK output from consuming unbounded memory if client is slow.
        # Trade-off: Producer may lag behind SDK if consumer network is slow.
        self.event_queue: asyncio.Queue[dict[str, str] | None] = asyncio.Queue(
            maxsize=100
        )
        self.producer_task: asyncio.Task[None] | None = None

    async def _handle_init_event(self, event_data: str) -> None:
        """Handle session initialization event.

        Args:
            event_data: JSON string with init event data.
        """
        try:
            init_data = json.loads(event_data)
            self.session_id = init_data.get("session_id")
            if not self.session_id:
                return

            # Session lifecycle:
            # 1. SDK generates session_id and emits it in 'init' event
            # 2. We extract session_id from init event and create database record
            # 3. DO NOT set query.session_id before execution - that would cause
            #    SDK to attempt resuming a non-existent conversation!
            # 4. Only set query.session_id when resuming existing sessions
            model = init_data.get("model", "sonnet")
            await self.session_service.create_session(
                model=model,
                session_id=self.session_id,
                owner_api_key=self.api_key,
            )
        except json.JSONDecodeError as e:
            logger.error(
                "Failed to parse init event",
                error=str(e),
                error_type=type(e).__name__,
                event_data=event_data,
                session_id=self.session_id,
                api_key_hash=hash_api_key(self.api_key),
                prompt_preview=self.query.prompt[:100] if self.query.prompt else None,
                error_id="ERR_INIT_PARSE_FAILED",
            )
            await self.event_queue.put(
                {
                    "event": "error",
                    "data": json.dumps(
                        {
                            "error": "Session initialization failed",
                            "message": "Invalid session initialization format",
                        }
                    ),
                }
            )
            self.is_error = True
            # Do NOT re-raise - error event already queued, prevents duplicate from _producer
        except Exception as e:
            logger.error(
                "Failed to create session",
                error=str(e),
                error_type=type(e).__name__,
                session_id=self.session_id,
                api_key_hash=hash_api_key(self.api_key),
                prompt_preview=self.query.prompt[:100] if self.query.prompt else None,
                error_id="ERR_SESSION_CREATE_FAILED",
            )
            await self.event_queue.put(
                {
                    "event": "error",
                    "data": json.dumps(
                        {
                            "error": "Session creation failed",
                            "message": "Unable to initialize session",
                        }
                    ),
                }
            )
            self.is_error = True
            # Do NOT re-raise - error event already queued, prevents duplicate from _producer

    def _track_event_metadata(self, event_type: str, event_data: str) -> None:
        """Track metadata from events (turns, cost, errors).

        Args:
            event_type: Type of event (message, error, result).
            event_data: JSON string with event data.
        """
        if event_type == "message":
            self.num_turns += 1
        if event_type == "error":
            self.is_error = True
        if event_type == "result":
            try:
                result_data = json.loads(event_data)
                if "turns" in result_data:
                    self.num_turns = result_data["turns"]
                if "total_cost_usd" in result_data:
                    self.total_cost_usd = result_data["total_cost_usd"]
            except json.JSONDecodeError as e:
                logger.error(
                    "failed_to_parse_result_event",
                    session_id=self.session_id,
                    api_key_hash=hash_api_key(self.api_key),
                    prompt_preview=self.query.prompt[:100] if self.query.prompt else None,
                    error=str(e),
                    event_data=event_data[:500],
                    error_id="ERR_RESULT_PARSE_FAILED",
                )

    async def _producer(self) -> None:
        """Producer task: reads events from SDK and queues them."""
        try:
            async for event in self.agent_service.query_stream(
                self.query, self.api_key
            ):
                event_type = event.get("event", "")
                event_data = event.get("data", "{}")

                # Track metadata from events
                self._track_event_metadata(event_type, event_data)

                # Handle session initialization
                if self.session_id is None and event_type == "init":
                    await self._handle_init_event(event_data)

                # Check for client disconnect
                if await self.request.is_disconnected():
                    if self.session_id:
                        await self.agent_service.interrupt(self.session_id)
                    break

                # Put event in queue (blocks if full - backpressure!)
                await self.event_queue.put(event)

        except asyncio.CancelledError:
            # Producer cancelled (client disconnected or error)
            if self.session_id:
                await self.agent_service.interrupt(self.session_id)
            raise
        except Exception as e:
            # Unexpected error in producer - log full details server-side
            logger.error(
                "Producer error in event stream",
                error=str(e),
                error_type=type(e).__name__,
                session_id=self.session_id,
                api_key_hash=hash_api_key(self.api_key),
                prompt_preview=self.query.prompt[:100] if self.query.prompt else None,
                error_id="ERR_STREAM_PRODUCER_FAILED",
            )
            # Return generic error to client (prevent exception detail leakage)
            await self.event_queue.put(
                {
                    "event": "error",
                    "data": json.dumps(
                        {
                            "error": "Internal stream error",
                            "message": "An unexpected error occurred while processing the stream",
                        }
                    ),
                }
            )
        finally:
            # Signal end of stream with None sentinel
            await self.event_queue.put(None)

    async def _update_session_status(self) -> None:
        """Update session status when stream completes."""
        if not self.session_id:
            return

        status: Literal["completed", "error"] = "error" if self.is_error else "completed"
        await self.session_service.update_session(
            session_id=self.session_id,
            status=status,
            total_turns=self.num_turns,
            total_cost_usd=self.total_cost_usd,
            current_api_key=self.api_key,
        )

    async def generate(self) -> AsyncGenerator[dict[str, str], None]:
        """Generate SSE events with disconnect monitoring and backpressure.

        Yields:
            Event dictionaries with 'event' and 'data' keys.
        """
        try:
            # Start producer task
            self.producer_task = asyncio.create_task(self._producer())

            # Consumer: yield events from queue until None sentinel
            while True:
                event = await self.event_queue.get()
                if event is None:
                    # Producer finished
                    break
                yield event

        except asyncio.CancelledError:
            # Client disconnected
            if self.session_id:
                await self.agent_service.interrupt(self.session_id)
            raise
        finally:
            # Clean up producer task
            if self.producer_task and not self.producer_task.done():
                self.producer_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await self.producer_task

            # Update session status when stream completes
            await self._update_session_status()
