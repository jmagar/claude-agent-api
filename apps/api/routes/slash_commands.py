"""Slash command management endpoints."""

from fastapi import APIRouter

from apps.api.dependencies import ApiKey, Cache
from apps.api.exceptions import APIError
from apps.api.schemas.requests.slash_commands import (
    SlashCommandCreateRequest,
    SlashCommandUpdateRequest,
)
from apps.api.schemas.responses import (
    SlashCommandDefinitionResponse,
    SlashCommandListResponse,
)
from apps.api.services.slash_commands import SlashCommandService

router = APIRouter(prefix="/slash-commands", tags=["Slash Commands"])


@router.get("", response_model=SlashCommandListResponse)
async def list_slash_commands(
    _api_key: ApiKey,
    cache: Cache,
) -> SlashCommandListResponse:
    """<summary>List slash commands.</summary>"""
    service = SlashCommandService(cache)
    commands = await service.list_commands()
    return SlashCommandListResponse(
        commands=[SlashCommandDefinitionResponse(**c.__dict__) for c in commands]
    )


@router.post("", response_model=SlashCommandDefinitionResponse, status_code=201)
async def create_slash_command(
    request: SlashCommandCreateRequest,
    _api_key: ApiKey,
    cache: Cache,
) -> SlashCommandDefinitionResponse:
    """<summary>Create a slash command.</summary>"""
    service = SlashCommandService(cache)
    command = await service.create_command(
        name=request.name,
        description=request.description,
        content=request.content,
        enabled=request.enabled,
    )
    return SlashCommandDefinitionResponse(**command.__dict__)


@router.get("/{command_id}", response_model=SlashCommandDefinitionResponse)
async def get_slash_command(
    command_id: str,
    _api_key: ApiKey,
    cache: Cache,
) -> SlashCommandDefinitionResponse:
    """<summary>Get slash command details.</summary>"""
    service = SlashCommandService(cache)
    command = await service.get_command(command_id)
    if command is None:
        raise APIError(
            message="Slash command not found",
            code="SLASH_COMMAND_NOT_FOUND",
            status_code=404,
        )
    return SlashCommandDefinitionResponse(**command.__dict__)


@router.put("/{command_id}", response_model=SlashCommandDefinitionResponse)
async def update_slash_command(
    command_id: str,
    request: SlashCommandUpdateRequest,
    _api_key: ApiKey,
    cache: Cache,
) -> SlashCommandDefinitionResponse:
    """<summary>Update slash command.</summary>"""
    service = SlashCommandService(cache)
    command = await service.update_command(
        command_id=command_id,
        name=request.name,
        description=request.description,
        content=request.content,
        enabled=request.enabled,
    )
    if command is None:
        raise APIError(
            message="Slash command not found",
            code="SLASH_COMMAND_NOT_FOUND",
            status_code=404,
        )
    return SlashCommandDefinitionResponse(**command.__dict__)


@router.delete("/{command_id}", status_code=204)
async def delete_slash_command(
    command_id: str,
    _api_key: ApiKey,
    cache: Cache,
) -> None:
    """<summary>Delete slash command.</summary>"""
    service = SlashCommandService(cache)
    deleted = await service.delete_command(command_id)
    if not deleted:
        raise APIError(
            message="Slash command not found",
            code="SLASH_COMMAND_NOT_FOUND",
            status_code=404,
        )
