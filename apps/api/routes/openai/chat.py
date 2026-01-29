"""OpenAI-compatible chat completions endpoint."""

import json
from collections.abc import AsyncGenerator
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, Request
from sse_starlette import EventSourceResponse

from apps.api.dependencies import get_agent_service, verify_api_key
from apps.api.protocols import AgentService, RequestTranslator, ResponseTranslator
from apps.api.routes.openai.dependencies import (
    get_request_translator,
    get_response_translator,
)
from apps.api.schemas.openai.requests import ChatCompletionRequest
from apps.api.schemas.openai.responses import OpenAIChatCompletion
from apps.api.schemas.responses import SingleQueryResponse
from apps.api.services.openai.streaming import StreamingAdapter
from apps.api.types import MessageEventDataDict, ResultEventDataDict

router = APIRouter(prefix="/chat", tags=["openai"])
logger = structlog.get_logger(__name__)


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
    """Create a chat completion in OpenAI format.

    Supports both streaming and non-streaming completions. When stream=true,
    returns SSE event stream. When stream=false, returns JSON response.

    Args:
        request: FastAPI request object for headers/correlation.
        payload: OpenAI chat completion request
        request_translator: Service for translating OpenAI → Claude format
        response_translator: Service for translating Claude → OpenAI format
        agent_service: Agent service for executing queries

    Returns:
        OpenAIChatCompletion: Non-streaming JSON response (stream=false)
        EventSourceResponse: SSE event stream (stream=true)

    Raises:
        APIError: If model name is not recognized
    """
    # Translate OpenAI request to Claude QueryRequest
    query_request = request_translator.translate(payload)

    # Handle streaming vs non-streaming
    if payload.stream:
        # Streaming: Return SSE event stream
        async def event_generator() -> AsyncGenerator[str, None]:
            """Generate SSE events from Claude SDK stream."""
            # Get native SDK event stream
            native_events = agent_service.query_stream(query_request, api_key)

            # Adapt to OpenAI streaming format
            adapter = StreamingAdapter(
                original_model=payload.model,
                mapped_model=query_request.model,
            )

            # Create async generator that yields (event_type, event_data) tuples
            async def native_event_tuples() -> AsyncGenerator[
                tuple[str, MessageEventDataDict | ResultEventDataDict], None
            ]:
                """Parse native SSE events into (event_type, data) tuples."""
                async for event in await native_events:
                    # Native events are dicts with 'event' and 'data' keys
                    # where 'data' is a JSON string that needs to be parsed
                    if isinstance(event, dict):
                        event_type = event.get("event", "")
                        event_data_raw = event.get("data", "{}")
                        # Parse JSON string to dict
                        if isinstance(event_data_raw, str):
                            try:
                                event_data = json.loads(event_data_raw)
                            except json.JSONDecodeError:
                                logger.warning(
                                    "skipping_malformed_sse_event",
                                    correlation_id=request.headers.get(
                                        "X-Correlation-ID"
                                    ),
                                    event_type=event_type,
                                    raw_data=event_data_raw[:100],
                                )
                                continue  # Skip malformed events
                        else:
                            event_data = event_data_raw
                        # Only yield events that streaming adapter expects
                        if event_type in ("partial", "result"):
                            yield (event_type, event_data)

            # Adapt events and yield as SSE format
            # EventSourceResponse from sse_starlette automatically adds "data: " prefix
            # and "\n\n" suffix, so we only need to yield the content
            async for chunk in adapter.adapt_stream(native_event_tuples()):
                if chunk == "[DONE]":
                    yield "[DONE]"
                else:
                    # Serialize chunk to JSON and yield (sse_starlette adds data: prefix)
                    yield json.dumps(chunk)

        return EventSourceResponse(event_generator())
    else:
        # Non-streaming: Execute query and return JSON
        response_dict = await agent_service.query_single(query_request, api_key)

        # Convert dict to Pydantic model for type safety
        # Pydantic will handle nested dict → model conversion automatically
        response = SingleQueryResponse.model_validate(response_dict)

        # Translate Claude response to OpenAI format
        openai_response = response_translator.translate(
            response, original_model=payload.model
        )

        return openai_response
