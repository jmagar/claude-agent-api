"""Tool preset management endpoints."""

from fastapi import APIRouter

from apps.api.dependencies import ApiKey, ToolPresetSvc
from apps.api.exceptions import ToolPresetNotFoundError
from apps.api.schemas.requests.tool_presets import (
    ToolPresetCreateRequest,
    ToolPresetUpdateRequest,
)
from apps.api.schemas.responses import ToolPresetListResponse, ToolPresetResponse

router = APIRouter(prefix="/tool-presets", tags=["Tool Presets"])


@router.get("", response_model=ToolPresetListResponse)
async def list_tool_presets(
    _api_key: ApiKey,
    tool_preset_service: ToolPresetSvc,
) -> ToolPresetListResponse:
    """List all tool presets."""
    service = tool_preset_service
    presets = await service.list_presets()

    return ToolPresetListResponse(
        presets=[
            ToolPresetResponse.model_validate(preset, from_attributes=True)
            for preset in presets
        ]
    )


@router.post("", response_model=ToolPresetResponse, status_code=201)
async def create_tool_preset(
    request: ToolPresetCreateRequest,
    _api_key: ApiKey,
    tool_preset_service: ToolPresetSvc,
) -> ToolPresetResponse:
    """Create a new tool preset."""
    service = tool_preset_service
    allowed_tools = (
        request.allowed_tools if request.allowed_tools is not None else request.tools
    )
    disallowed_tools = request.disallowed_tools or []
    preset = await service.create_preset(
        name=request.name,
        description=request.description,
        allowed_tools=allowed_tools,
        disallowed_tools=disallowed_tools,
    )

    return ToolPresetResponse.model_validate(preset, from_attributes=True)


@router.get("/{preset_id}", response_model=ToolPresetResponse)
async def get_tool_preset(
    preset_id: str,
    _api_key: ApiKey,
    tool_preset_service: ToolPresetSvc,
) -> ToolPresetResponse:
    """Get tool preset details by ID."""
    service = tool_preset_service
    preset = await service.get_preset(preset_id)
    if preset is None:
        raise ToolPresetNotFoundError(preset_id)

    return ToolPresetResponse.model_validate(preset, from_attributes=True)


@router.put("/{preset_id}", response_model=ToolPresetResponse)
async def update_tool_preset(
    preset_id: str,
    request: ToolPresetUpdateRequest,
    _api_key: ApiKey,
    tool_preset_service: ToolPresetSvc,
) -> ToolPresetResponse:
    """Update a tool preset by ID."""
    service = tool_preset_service
    allowed_tools = (
        request.allowed_tools if request.allowed_tools is not None else request.tools
    )
    if allowed_tools is None:
        allowed_tools = []
    disallowed_tools = request.disallowed_tools or []
    preset = await service.update_preset(
        preset_id=preset_id,
        name=request.name,
        description=request.description,
        allowed_tools=allowed_tools,
        disallowed_tools=disallowed_tools,
    )
    if preset is None:
        raise ToolPresetNotFoundError(preset_id)

    return ToolPresetResponse.model_validate(preset, from_attributes=True)


@router.delete("/{preset_id}", status_code=204)
async def delete_tool_preset(
    preset_id: str,
    _api_key: ApiKey,
    tool_preset_service: ToolPresetSvc,
) -> None:
    """Delete a tool preset by ID."""
    service = tool_preset_service
    deleted = await service.delete_preset(preset_id)
    if not deleted:
        raise ToolPresetNotFoundError(preset_id)
