"""OpenAI-compatible chat completions endpoint."""

from typing import Annotated

from fastapi import APIRouter, Depends

from apps.api.dependencies import get_agent_service
from apps.api.routes.openai.dependencies import (
    get_request_translator,
    get_response_translator,
)
from apps.api.schemas.openai.requests import ChatCompletionRequest
from apps.api.schemas.openai.responses import OpenAIChatCompletion
from apps.api.schemas.responses import SingleQueryResponse
from apps.api.services.agent.service import AgentService
from apps.api.services.openai.translator import RequestTranslator, ResponseTranslator

router = APIRouter(prefix="/chat", tags=["openai"])


@router.post("/completions")
async def create_chat_completion(
    request: ChatCompletionRequest,
    request_translator: Annotated[RequestTranslator, Depends(get_request_translator)],
    response_translator: Annotated[ResponseTranslator, Depends(get_response_translator)],
    agent_service: Annotated[AgentService, Depends(get_agent_service)],
) -> OpenAIChatCompletion:
    """Create a chat completion in OpenAI format.

    Non-streaming endpoint that translates OpenAI requests to Claude Agent SDK format,
    executes the query, and translates the response back to OpenAI format.

    Args:
        request: OpenAI chat completion request
        request_translator: Service for translating OpenAI → Claude format
        response_translator: Service for translating Claude → OpenAI format
        agent_service: Agent service for executing queries

    Returns:
        OpenAI-formatted chat completion response

    Raises:
        ValueError: If model name is not recognized
    """
    # Translate OpenAI request to Claude QueryRequest
    query_request = request_translator.translate(request)

    # Execute query using agent service (non-streaming)
    response_dict = await agent_service.query_single(query_request)

    # Convert dict to Pydantic model for type safety
    response = SingleQueryResponse(**response_dict)

    # Translate Claude response to OpenAI format
    openai_response = response_translator.translate(response, original_model=request.model)

    return openai_response
