"""Skills API routes (CRUD)."""

from fastapi import APIRouter

from apps.api.dependencies import ApiKey, Cache
from apps.api.exceptions import APIError
from apps.api.schemas.requests.skills_crud import SkillCreateRequest, SkillUpdateRequest
from apps.api.schemas.responses import SkillDefinitionResponse, SkillListResponse
from apps.api.services.skills_crud import SkillCrudService

router = APIRouter(prefix="/skills", tags=["Skills"])


@router.get("", response_model=SkillListResponse)
async def list_skills(
    _api_key: ApiKey,
    cache: Cache,
) -> SkillListResponse:
    """<summary>List all skills.</summary>"""
    service = SkillCrudService(cache)
    skills = await service.list_skills()
    return SkillListResponse(skills=[SkillDefinitionResponse(**s.__dict__) for s in skills])


@router.post("", response_model=SkillDefinitionResponse, status_code=201)
async def create_skill(
    request: SkillCreateRequest,
    _api_key: ApiKey,
    cache: Cache,
) -> SkillDefinitionResponse:
    """<summary>Create a new skill.</summary>"""
    service = SkillCrudService(cache)
    skill = await service.create_skill(
        name=request.name,
        description=request.description,
        content=request.content,
        enabled=request.enabled,
    )
    return SkillDefinitionResponse(**skill.__dict__)


@router.get("/{skill_id}", response_model=SkillDefinitionResponse)
async def get_skill(
    skill_id: str,
    _api_key: ApiKey,
    cache: Cache,
) -> SkillDefinitionResponse:
    """<summary>Get skill details.</summary>"""
    service = SkillCrudService(cache)
    skill = await service.get_skill(skill_id)
    if skill is None:
        raise APIError(
            message="Skill not found",
            code="SKILL_NOT_FOUND",
            status_code=404,
        )
    return SkillDefinitionResponse(**skill.__dict__)


@router.put("/{skill_id}", response_model=SkillDefinitionResponse)
async def update_skill(
    skill_id: str,
    request: SkillUpdateRequest,
    _api_key: ApiKey,
    cache: Cache,
) -> SkillDefinitionResponse:
    """<summary>Update a skill.</summary>"""
    service = SkillCrudService(cache)
    skill = await service.update_skill(
        skill_id=skill_id,
        name=request.name,
        description=request.description,
        content=request.content,
        enabled=request.enabled,
    )
    if skill is None:
        raise APIError(
            message="Skill not found",
            code="SKILL_NOT_FOUND",
            status_code=404,
        )
    return SkillDefinitionResponse(**skill.__dict__)


@router.delete("/{skill_id}", status_code=204)
async def delete_skill(
    skill_id: str,
    _api_key: ApiKey,
    cache: Cache,
) -> None:
    """<summary>Delete a skill.</summary>"""
    service = SkillCrudService(cache)
    deleted = await service.delete_skill(skill_id)
    if not deleted:
        raise APIError(
            message="Skill not found",
            code="SKILL_NOT_FOUND",
            status_code=404,
        )
