"""OpenAI-compatible Assistants API endpoints.

Implements the Assistants API (beta) for managing AI assistants.
https://platform.openai.com/docs/api-reference/assistants
"""

from typing import Annotated, cast

from fastapi import APIRouter, Depends, HTTPException, Query

from apps.api.routes.openai.dependencies import get_assistant_service
from apps.api.schemas.openai.assistant_requests import (
    CreateAssistantRequest,
    ModifyAssistantRequest,
)
from apps.api.schemas.openai.assistants import (
    OpenAIAssistant,
    OpenAIAssistantList,
    OpenAIAssistantTool,
    OpenAIDeletionStatus,
)
from apps.api.services.assistants import AssistantService

router = APIRouter(tags=["Assistants"])


def _convert_assistant_to_response(assistant: object) -> OpenAIAssistant:
    """Convert service Assistant to OpenAI response format.

    Args:
        assistant: Service layer Assistant object.

    Returns:
        OpenAI-formatted assistant response.
    """
    # Extract timestamp
    created_at = getattr(assistant, "created_at", None)
    if hasattr(created_at, "timestamp"):
        created_at_int = int(created_at.timestamp())
    else:
        created_at_int = int(created_at) if created_at else 0

    # Convert tools to OpenAI format
    tools_raw = getattr(assistant, "tools", []) or []
    tools: list[OpenAIAssistantTool] = []
    for tool in tools_raw:
        if isinstance(tool, dict):
            tools.append(cast("OpenAIAssistantTool", dict(tool)))

    return OpenAIAssistant(
        id=str(getattr(assistant, "id", "")),
        object="assistant",
        created_at=created_at_int,
        model=str(getattr(assistant, "model", "")),
        name=getattr(assistant, "name", None),
        description=getattr(assistant, "description", None),
        instructions=getattr(assistant, "instructions", None),
        tools=tools,
        metadata=getattr(assistant, "metadata", {}) or {},
        temperature=getattr(assistant, "temperature", None),
        top_p=getattr(assistant, "top_p", None),
        response_format=None,
    )


@router.post("/assistants", response_model=None)
async def create_assistant(
    request: CreateAssistantRequest,
    assistant_service: Annotated[AssistantService, Depends(get_assistant_service)],
) -> OpenAIAssistant:
    """Create an assistant.

    Args:
        request: Create assistant request.
        assistant_service: Assistant service instance.

    Returns:
        Created assistant.
    """
    # Convert tools to service format
    tools: list[dict[str, object]] = []
    if request.tools:
        for tool in request.tools:
            # Tools are TypedDicts, explicitly cast and convert to regular dict
            # Each tool has at minimum a 'type' key
            tool_dict: dict[str, object] = {}
            for key, val in tool.items():
                tool_dict[key] = val
            tools.append(tool_dict)

    assistant = await assistant_service.create_assistant(
        model=request.model,
        name=request.name,
        description=request.description,
        instructions=request.instructions,
        tools=tools,
        metadata=request.metadata,
        temperature=request.temperature,
        top_p=request.top_p,
    )

    return _convert_assistant_to_response(assistant)


@router.get("/assistants/{assistant_id}", response_model=None)
async def get_assistant(
    assistant_id: str,
    assistant_service: Annotated[AssistantService, Depends(get_assistant_service)],
) -> OpenAIAssistant:
    """Get an assistant by ID.

    Args:
        assistant_id: The assistant ID.
        assistant_service: Assistant service instance.

    Returns:
        Assistant object.

    Raises:
        HTTPException: 404 if assistant not found.
    """
    assistant = await assistant_service.get_assistant(assistant_id)

    if not assistant:
        raise HTTPException(
            status_code=404,
            detail=f"Assistant '{assistant_id}' not found",
        )

    return _convert_assistant_to_response(assistant)


@router.get("/assistants", response_model=None)
async def list_assistants(
    assistant_service: Annotated[AssistantService, Depends(get_assistant_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    order: Annotated[str, Query(pattern="^(asc|desc)$")] = "desc",
    after: str | None = None,
    before: str | None = None,
) -> OpenAIAssistantList:
    """List assistants with pagination.

    Args:
        assistant_service: Assistant service instance.
        limit: Maximum number of results.
        order: Sort order (asc or desc).
        after: Cursor for pagination.
        before: Cursor for pagination.

    Returns:
        Paginated list of assistants.
    """
    result = await assistant_service.list_assistants(
        limit=limit,
        order=order,
        after=after,
        before=before,
    )

    # Convert assistants to OpenAI format
    data: list[OpenAIAssistant] = []
    for assistant in result.data:
        data.append(_convert_assistant_to_response(assistant))

    return OpenAIAssistantList(
        object="list",
        data=data,
        first_id=result.first_id,
        last_id=result.last_id,
        has_more=result.has_more,
    )


@router.post("/assistants/{assistant_id}", response_model=None)
async def modify_assistant(
    assistant_id: str,
    request: ModifyAssistantRequest,
    assistant_service: Annotated[AssistantService, Depends(get_assistant_service)],
) -> OpenAIAssistant:
    """Modify an assistant.

    Args:
        assistant_id: The assistant ID.
        request: Modify assistant request.
        assistant_service: Assistant service instance.

    Returns:
        Modified assistant.

    Raises:
        HTTPException: 404 if assistant not found.
    """
    # Convert tools to service format
    tools: list[dict[str, object]] | None = None
    if request.tools is not None:
        tools = []
        for tool in request.tools:
            # Tools are TypedDicts, explicitly cast and convert to regular dict
            tool_dict: dict[str, object] = {}
            for key, val in tool.items():
                tool_dict[key] = val
            tools.append(tool_dict)

    assistant = await assistant_service.update_assistant(
        assistant_id=assistant_id,
        model=request.model,
        name=request.name,
        description=request.description,
        instructions=request.instructions,
        tools=tools,
        metadata=request.metadata,
        temperature=request.temperature,
        top_p=request.top_p,
    )

    if not assistant:
        raise HTTPException(
            status_code=404,
            detail=f"Assistant '{assistant_id}' not found",
        )

    return _convert_assistant_to_response(assistant)


@router.delete("/assistants/{assistant_id}", response_model=None)
async def delete_assistant(
    assistant_id: str,
    assistant_service: Annotated[AssistantService, Depends(get_assistant_service)],
) -> OpenAIDeletionStatus:
    """Delete an assistant.

    Args:
        assistant_id: The assistant ID.
        assistant_service: Assistant service instance.

    Returns:
        Deletion status.

    Raises:
        HTTPException: 404 if assistant not found.
    """
    deleted = await assistant_service.delete_assistant(assistant_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail=f"Assistant '{assistant_id}' not found",
        )

    return OpenAIDeletionStatus(
        id=assistant_id,
        object="assistant.deleted",
        deleted=True,
    )
