"""OpenAI-compatible Threads API endpoints.

Implements the Threads API (beta) for managing conversation threads.
https://platform.openai.com/docs/api-reference/threads
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from apps.api.routes.openai.dependencies import (
    get_message_service,
    get_run_service,
    get_thread_service,
)
from apps.api.schemas.openai.assistant_requests import (
    CreateMessageRequest,
    CreateRunRequest,
    CreateThreadRequest,
    ModifyMessageRequest,
    ModifyThreadRequest,
)
from apps.api.schemas.openai.assistants import (
    OpenAIDeletionStatus,
    OpenAIRun,
    OpenAIRunList,
    OpenAIThread,
    OpenAIThreadMessage,
    OpenAIThreadMessageList,
)
from apps.api.services.assistants import MessageService, RunService, ThreadService

router = APIRouter(tags=["Threads"])


# =============================================================================
# Conversion Helpers
# =============================================================================


def _convert_thread_to_response(thread: object) -> OpenAIThread:
    """Convert service Thread to OpenAI response format.

    Args:
        thread: Service layer Thread object.

    Returns:
        OpenAI-formatted thread response.
    """
    # Extract metadata
    metadata_raw = getattr(thread, "metadata", {}) or {}
    metadata: dict[str, str] = {}
    if isinstance(metadata_raw, dict):
        for k, v in metadata_raw.items():
            if isinstance(k, str) and isinstance(v, str):
                metadata[k] = v

    return OpenAIThread(
        id=str(getattr(thread, "id", "")),
        object="thread",
        created_at=int(getattr(thread, "created_at", 0)),
        metadata=metadata,
        tool_resources=None,
    )


def _convert_message_to_response(message: object) -> OpenAIThreadMessage:
    """Convert service Message to OpenAI response format.

    Args:
        message: Service layer Message object.

    Returns:
        OpenAI-formatted message response.
    """
    # Extract content
    content_raw = getattr(message, "content", []) or []
    content: list[dict[str, object]] = []
    for block in content_raw:
        if isinstance(block, dict):
            content.append(dict(block))

    # Extract metadata
    metadata_raw = getattr(message, "metadata", {}) or {}
    metadata: dict[str, str] = {}
    if isinstance(metadata_raw, dict):
        for k, v in metadata_raw.items():
            if isinstance(k, str) and isinstance(v, str):
                metadata[k] = v

    return OpenAIThreadMessage(
        id=str(getattr(message, "id", "")),
        object="thread.message",
        created_at=int(getattr(message, "created_at", 0)),
        thread_id=str(getattr(message, "thread_id", "")),
        role=getattr(message, "role", "user"),
        content=content,  # type: ignore[typeddict-item]
        metadata=metadata,
        assistant_id=getattr(message, "assistant_id", None),
        run_id=getattr(message, "run_id", None),
    )


def _convert_run_to_response(run: object) -> OpenAIRun:
    """Convert service Run to OpenAI response format.

    Args:
        run: Service layer Run object.

    Returns:
        OpenAI-formatted run response.
    """
    # Extract tools
    tools_raw = getattr(run, "tools", []) or []
    tools: list[dict[str, object]] = []
    for tool in tools_raw:
        if isinstance(tool, dict):
            tools.append(dict(tool))

    # Extract metadata
    metadata_raw = getattr(run, "metadata", {}) or {}
    metadata: dict[str, str] = {}
    if isinstance(metadata_raw, dict):
        for k, v in metadata_raw.items():
            if isinstance(k, str) and isinstance(v, str):
                metadata[k] = v

    return OpenAIRun(
        id=str(getattr(run, "id", "")),
        object="thread.run",
        created_at=int(getattr(run, "created_at", 0)),
        thread_id=str(getattr(run, "thread_id", "")),
        assistant_id=str(getattr(run, "assistant_id", "")),
        status=getattr(run, "status", "queued"),
        model=str(getattr(run, "model", "")),
        instructions=getattr(run, "instructions", None),
        tools=tools,  # type: ignore[typeddict-item]
        metadata=metadata,
        required_action=getattr(run, "required_action", None),
        last_error=getattr(run, "last_error", None),
        usage=getattr(run, "usage", None),
        started_at=getattr(run, "started_at", None),
        expires_at=getattr(run, "expires_at", None),
        cancelled_at=getattr(run, "cancelled_at", None),
        failed_at=getattr(run, "failed_at", None),
        completed_at=getattr(run, "completed_at", None),
        parallel_tool_calls=True,
    )


# =============================================================================
# Thread Endpoints
# =============================================================================


@router.post("/threads", response_model=None)
async def create_thread(
    request: CreateThreadRequest,
    thread_service: Annotated[ThreadService, Depends(get_thread_service)],
    message_service: Annotated[MessageService, Depends(get_message_service)],
) -> OpenAIThread:
    """Create a new thread.

    Args:
        request: Create thread request.
        thread_service: Thread service instance.
        message_service: Message service for initial messages.

    Returns:
        Created thread.
    """
    # Convert metadata to proper type
    metadata: dict[str, str] | None = None
    if request.metadata is not None:
        metadata = {}
        for k, v in request.metadata.items():
            metadata[k] = str(v)

    thread = await thread_service.create_thread(metadata=metadata)

    # Create initial messages if provided
    if request.messages:
        for msg in request.messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            msg_metadata = msg.get("metadata")
            if role in ("user", "assistant") and content:
                await message_service.create_message(
                    thread_id=thread.id,
                    role=role,
                    content=str(content),
                    metadata=msg_metadata,
                )

    return _convert_thread_to_response(thread)


@router.get("/threads/{thread_id}", response_model=None)
async def get_thread(
    thread_id: str,
    thread_service: Annotated[ThreadService, Depends(get_thread_service)],
) -> OpenAIThread:
    """Get a thread by ID.

    Args:
        thread_id: The thread ID.
        thread_service: Thread service instance.

    Returns:
        Thread object.

    Raises:
        HTTPException: 404 if thread not found.
    """
    thread = await thread_service.get_thread(thread_id)

    if not thread:
        raise HTTPException(
            status_code=404,
            detail=f"Thread '{thread_id}' not found",
        )

    return _convert_thread_to_response(thread)


@router.post("/threads/{thread_id}", response_model=None)
async def modify_thread(
    thread_id: str,
    request: ModifyThreadRequest,
    thread_service: Annotated[ThreadService, Depends(get_thread_service)],
) -> OpenAIThread:
    """Modify a thread's metadata.

    Args:
        thread_id: The thread ID.
        request: Modify thread request.
        thread_service: Thread service instance.

    Returns:
        Modified thread.

    Raises:
        HTTPException: 404 if thread not found.
    """
    # Convert metadata to proper type
    metadata: dict[str, str] | None = None
    if request.metadata is not None:
        metadata = {}
        for k, v in request.metadata.items():
            metadata[k] = str(v)

    thread = await thread_service.modify_thread(
        thread_id=thread_id,
        metadata=metadata,
    )

    if not thread:
        raise HTTPException(
            status_code=404,
            detail=f"Thread '{thread_id}' not found",
        )

    return _convert_thread_to_response(thread)


@router.delete("/threads/{thread_id}", response_model=None)
async def delete_thread(
    thread_id: str,
    thread_service: Annotated[ThreadService, Depends(get_thread_service)],
) -> OpenAIDeletionStatus:
    """Delete a thread.

    Args:
        thread_id: The thread ID.
        thread_service: Thread service instance.

    Returns:
        Deletion status.

    Raises:
        HTTPException: 404 if thread not found.
    """
    deleted = await thread_service.delete_thread(thread_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail=f"Thread '{thread_id}' not found",
        )

    return OpenAIDeletionStatus(
        id=thread_id,
        object="thread.deleted",
        deleted=True,
    )


# =============================================================================
# Message Endpoints
# =============================================================================


@router.post("/threads/{thread_id}/messages", response_model=None)
async def create_message(
    thread_id: str,
    request: CreateMessageRequest,
    message_service: Annotated[MessageService, Depends(get_message_service)],
) -> OpenAIThreadMessage:
    """Create a message in a thread.

    Args:
        thread_id: The thread ID.
        request: Create message request.
        message_service: Message service instance.

    Returns:
        Created message.
    """
    # Convert metadata to proper type
    metadata: dict[str, str] | None = None
    if request.metadata is not None:
        metadata = {}
        for k, v in request.metadata.items():
            metadata[k] = str(v)

    message = await message_service.create_message(
        thread_id=thread_id,
        role=request.role,
        content=request.content,
        metadata=metadata,
    )

    return _convert_message_to_response(message)


@router.get("/threads/{thread_id}/messages", response_model=None)
async def list_messages(
    thread_id: str,
    message_service: Annotated[MessageService, Depends(get_message_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    order: Annotated[str, Query(pattern="^(asc|desc)$")] = "desc",
    after: str | None = None,
    before: str | None = None,
) -> OpenAIThreadMessageList:
    """List messages in a thread.

    Args:
        thread_id: The thread ID.
        message_service: Message service instance.
        limit: Maximum number of results.
        order: Sort order.
        after: Cursor for pagination.
        before: Cursor for pagination.

    Returns:
        Paginated list of messages.
    """
    result = await message_service.list_messages(
        thread_id=thread_id,
        limit=limit,
        order=order,
        after=after,
        before=before,
    )

    # Convert messages
    data: list[OpenAIThreadMessage] = []
    for message in result.data:
        data.append(_convert_message_to_response(message))

    return OpenAIThreadMessageList(
        object="list",
        data=data,
        first_id=result.first_id,
        last_id=result.last_id,
        has_more=result.has_more,
    )


@router.get("/threads/{thread_id}/messages/{message_id}", response_model=None)
async def get_message(
    thread_id: str,
    message_id: str,
    message_service: Annotated[MessageService, Depends(get_message_service)],
) -> OpenAIThreadMessage:
    """Get a message by ID.

    Args:
        thread_id: The thread ID.
        message_id: The message ID.
        message_service: Message service instance.

    Returns:
        Message object.

    Raises:
        HTTPException: 404 if message not found.
    """
    message = await message_service.get_message(thread_id, message_id)

    if not message:
        raise HTTPException(
            status_code=404,
            detail=f"Message '{message_id}' not found in thread '{thread_id}'",
        )

    return _convert_message_to_response(message)


@router.post("/threads/{thread_id}/messages/{message_id}", response_model=None)
async def modify_message(
    thread_id: str,
    message_id: str,
    request: ModifyMessageRequest,
    message_service: Annotated[MessageService, Depends(get_message_service)],
) -> OpenAIThreadMessage:
    """Modify a message's metadata.

    Args:
        thread_id: The thread ID.
        message_id: The message ID.
        request: Modify message request.
        message_service: Message service instance.

    Returns:
        Modified message.

    Raises:
        HTTPException: 404 if message not found.
    """
    # Convert metadata to proper type
    metadata: dict[str, str] | None = None
    if request.metadata is not None:
        metadata = {}
        for k, v in request.metadata.items():
            metadata[k] = str(v)

    message = await message_service.modify_message(
        thread_id=thread_id,
        message_id=message_id,
        metadata=metadata,
    )

    if not message:
        raise HTTPException(
            status_code=404,
            detail=f"Message '{message_id}' not found in thread '{thread_id}'",
        )

    return _convert_message_to_response(message)


# =============================================================================
# Run Endpoints
# =============================================================================


@router.post("/threads/{thread_id}/runs", response_model=None)
async def create_run(
    thread_id: str,
    request: CreateRunRequest,
    run_service: Annotated[RunService, Depends(get_run_service)],
) -> OpenAIRun:
    """Create a run on a thread.

    Args:
        thread_id: The thread ID.
        request: Create run request.
        run_service: Run service instance.

    Returns:
        Created run.
    """
    # Convert tools to proper type
    tools: list[dict[str, object]] | None = None
    if request.tools is not None:
        tools = []
        for tool in request.tools:
            tool_dict: dict[str, object] = {}
            for key, val in tool.items():
                tool_dict[key] = val
            tools.append(tool_dict)

    # Convert metadata to proper type
    metadata: dict[str, str] | None = None
    if request.metadata is not None:
        metadata = {}
        for k, v in request.metadata.items():
            metadata[k] = str(v)

    run = await run_service.create_run(
        thread_id=thread_id,
        assistant_id=request.assistant_id,
        model=request.model or "gpt-4",
        instructions=request.instructions,
        tools=tools,
        metadata=metadata,
    )

    return _convert_run_to_response(run)


@router.get("/threads/{thread_id}/runs", response_model=None)
async def list_runs(
    thread_id: str,
    run_service: Annotated[RunService, Depends(get_run_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    order: Annotated[str, Query(pattern="^(asc|desc)$")] = "desc",
) -> OpenAIRunList:
    """List runs in a thread.

    Args:
        thread_id: The thread ID.
        run_service: Run service instance.
        limit: Maximum number of results.
        order: Sort order.

    Returns:
        Paginated list of runs.
    """
    result = await run_service.list_runs(
        thread_id=thread_id,
        limit=limit,
        order=order,
    )

    # Convert runs
    data: list[OpenAIRun] = []
    for run in result.data:
        data.append(_convert_run_to_response(run))

    return OpenAIRunList(
        object="list",
        data=data,
        first_id=result.first_id,
        last_id=result.last_id,
        has_more=result.has_more,
    )


@router.get("/threads/{thread_id}/runs/{run_id}", response_model=None)
async def get_run(
    thread_id: str,
    run_id: str,
    run_service: Annotated[RunService, Depends(get_run_service)],
) -> OpenAIRun:
    """Get a run by ID.

    Args:
        thread_id: The thread ID.
        run_id: The run ID.
        run_service: Run service instance.

    Returns:
        Run object.

    Raises:
        HTTPException: 404 if run not found.
    """
    run = await run_service.get_run(thread_id, run_id)

    if not run:
        raise HTTPException(
            status_code=404,
            detail=f"Run '{run_id}' not found in thread '{thread_id}'",
        )

    return _convert_run_to_response(run)


@router.post("/threads/{thread_id}/runs/{run_id}/cancel", response_model=None)
async def cancel_run(
    thread_id: str,
    run_id: str,
    run_service: Annotated[RunService, Depends(get_run_service)],
) -> OpenAIRun:
    """Cancel a run.

    Args:
        thread_id: The thread ID.
        run_id: The run ID.
        run_service: Run service instance.

    Returns:
        Cancelled run.

    Raises:
        HTTPException: 404 if run not found.
    """
    run = await run_service.cancel_run(thread_id, run_id)

    if not run:
        raise HTTPException(
            status_code=404,
            detail=f"Run '{run_id}' not found in thread '{thread_id}'",
        )

    return _convert_run_to_response(run)
