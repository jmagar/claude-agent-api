"""Slash command management endpoints."""

from fastapi import APIRouter

from apps.api.dependencies import ApiKey, SlashCommandSvc
from apps.api.exceptions import APIError
from apps.api.schemas.requests.slash_commands import (
    SlashCommandCreateRequest,
    SlashCommandUpdateRequest,
)
from apps.api.schemas.responses import (
    SlashCommandDefinitionResponse,
    SlashCommandListResponse,
)

router = APIRouter(prefix="/slash-commands", tags=["Slash Commands"])


@router.get("", response_model=SlashCommandListResponse)
async def list_slash_commands(
    _api_key: ApiKey,
    slash_command_service: SlashCommandSvc,
) -> SlashCommandListResponse:
    """<summary>List slash commands.</summary>"""
    service = slash_command_service
    commands = await service.list_commands()
    return SlashCommandListResponse(
        commands=[
            SlashCommandDefinitionResponse.model_validate(c, from_attributes=True)
            for c in commands
        ]
    )


@router.post("", response_model=SlashCommandDefinitionResponse, status_code=201)
async def create_slash_command(
    request: SlashCommandCreateRequest,
    _api_key: ApiKey,
    slash_command_service: SlashCommandSvc,
) -> SlashCommandDefinitionResponse:
    """<summary>Create a slash command.</summary>"""
    service = slash_command_service
    command = await service.create_command(
        name=request.name,
        description=request.description,
        content=request.content,
        enabled=request.enabled,
    )
    return SlashCommandDefinitionResponse.model_validate(command, from_attributes=True)


@router.get("/{command_id}", response_model=SlashCommandDefinitionResponse)
async def get_slash_command(
    command_id: str,
    _api_key: ApiKey,
    slash_command_service: SlashCommandSvc,
) -> SlashCommandDefinitionResponse:
    """<summary>Get slash command details.</summary>"""
    service = slash_command_service
    command = await service.get_command(command_id)
    if command is None:
        raise APIError(
            message="Slash command not found",
            code="SLASH_COMMAND_NOT_FOUND",
            status_code=404,
        )
    return SlashCommandDefinitionResponse.model_validate(command, from_attributes=True)


@router.put("/{command_id}", response_model=SlashCommandDefinitionResponse)
async def update_slash_command(
    command_id: str,
    request: SlashCommandUpdateRequest,
    _api_key: ApiKey,
    slash_command_service: SlashCommandSvc,
) -> SlashCommandDefinitionResponse:
    """<summary>Update slash command.</summary>"""
    service = slash_command_service
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
    return SlashCommandDefinitionResponse.model_validate(command, from_attributes=True)


@router.delete("/{command_id}", status_code=204)
async def delete_slash_command(
    command_id: str,
    _api_key: ApiKey,
    slash_command_service: SlashCommandSvc,
) -> None:
    """<summary>Delete slash command.</summary>"""
    service = slash_command_service
    deleted = await service.delete_command(command_id)
    if not deleted:
        raise APIError(
            message="Slash command not found",
            code="SLASH_COMMAND_NOT_FOUND",
            status_code=404,
        )
