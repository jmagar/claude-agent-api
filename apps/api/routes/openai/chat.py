"""OpenAI-compatible chat completions endpoint."""

import json
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated, cast

import structlog
from fastapi import APIRouter, Depends, Request
from sse_starlette import EventSourceResponse

from apps.api.dependencies import get_agent_service, verify_api_key
from apps.api.protocols import RequestTranslator, ResponseTranslator
from apps.api.routes.openai.dependencies import (
    get_request_translator,
    get_response_translator,
)
from apps.api.schemas.openai.requests import ChatCompletionRequest
from apps.api.schemas.openai.responses import OpenAIChatCompletion
from apps.api.schemas.responses import SingleQueryResponse
from apps.api.services.agent import AgentService
from apps.api.services.openai.streaming import StreamingAdapter
from apps.api.types import MessageEventDataDict, ResultEventDataDict

if TYPE_CHECKING:
    from apps.api.schemas.requests.query import QueryRequest

router = APIRouter(prefix="/chat", tags=["openai"])
logger = structlog.get_logger(__name__)


@dataclass
class StreamingChatHandler:
    """Build OpenAI-compatible streaming chat responses."""

    request: Request
    payload: ChatCompletionRequest
    api_key: str
    agent_service: AgentService

    def build_response(self, query_request: "QueryRequest") -> EventSourceResponse:
        """Create SSE response for stream-enabled requests."""

        async def event_generator() -> AsyncGenerator[str, None]:
            native_events = self.agent_service.query_stream(query_request, self.api_key)
            adapter = StreamingAdapter(
                original_model=self.payload.model,
                mapped_model=self.payload.model,
            )
            async for chunk in adapter.adapt_stream(
                self._native_event_tuples(native_events)
            ):
                if chunk == "[DONE]":
                    yield "[DONE]"
                else:
                    yield json.dumps(chunk)

        return EventSourceResponse(event_generator())

    async def _native_event_tuples(
        self,
        native_events: AsyncGenerator[dict[str, str], None],
    ) -> AsyncGenerator[tuple[str, MessageEventDataDict | ResultEventDataDict], None]:
        """Parse native SSE events into adapter-compatible tuples."""
        async for event in native_events:
            if not isinstance(event, dict):
                continue

            event_type = event.get("event", "")
            event_data_raw = event.get("data", "{}")
            event_data = self._parse_event_data(event_type, event_data_raw)
            if event_data is None:
                continue

            if event_type in ("message", "partial", "result"):
                yield (event_type, event_data)

    def _parse_event_data(
        self,
        event_type: object,
        event_data_raw: object,
    ) -> MessageEventDataDict | ResultEventDataDict | None:
        """Safely parse event payload JSON from SSE data field."""
        if isinstance(event_data_raw, str):
            try:
                parsed = json.loads(event_data_raw)
            except json.JSONDecodeError:
                logger.warning(
                    "skipping_malformed_sse_event",
                    correlation_id=self.request.headers.get("X-Correlation-ID"),
                    event_type=event_type,
                    raw_data=event_data_raw[:100],
                )
                return None
            if isinstance(parsed, dict):
                return cast("MessageEventDataDict | ResultEventDataDict", parsed)
            return None

        if isinstance(event_data_raw, dict):
            return cast("MessageEventDataDict | ResultEventDataDict", event_data_raw)
        return None


@dataclass
class NonStreamingChatHandler:
    """Build OpenAI-compatible non-streaming chat responses."""

    payload: ChatCompletionRequest
    api_key: str
    agent_service: AgentService
    response_translator: ResponseTranslator

    async def build_response(
        self, query_request: "QueryRequest"
    ) -> OpenAIChatCompletion:
        """Execute single query and translate to OpenAI response shape."""
        response_dict = await self.agent_service.query_single(
            query_request, self.api_key
        )
        response = SingleQueryResponse.model_validate(response_dict)
        return self.response_translator.translate(
            response,
            original_model=self.payload.model,
        )


@router.post("/completions", response_model=None)
async def create_chat_completion(
    request: Request,
    payload: ChatCompletionRequest,
    api_key: Annotated[str, Depends(verify_api_key)],
    request_translator: Annotated[RequestTranslator, Depends(get_request_translator)],
    response_translator: Annotated[
        ResponseTranslator, Depends(get_response_translator)
    ],
    agent_service: Annotated[AgentService, Depends(get_agent_service)],
) -> OpenAIChatCompletion | EventSourceResponse:
    """Create a chat completion in OpenAI format."""
    permission_mode = request.headers.get("X-Permission-Mode")
    query_request = request_translator.translate(
        payload,
        permission_mode=permission_mode,
    )

    if payload.stream:
        return StreamingChatHandler(
            request=request,
            payload=payload,
            api_key=api_key,
            agent_service=agent_service,
        ).build_response(query_request)

    return await NonStreamingChatHandler(
        payload=payload,
        api_key=api_key,
        agent_service=agent_service,
        response_translator=response_translator,
    ).build_response(query_request)
