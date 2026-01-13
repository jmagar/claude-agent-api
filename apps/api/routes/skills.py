"""Skills API routes (CRUD with filesystem discovery)."""

from pathlib import Path

from fastapi import APIRouter, Query

from apps.api.dependencies import ApiKey, Cache
from apps.api.exceptions import APIError
from apps.api.schemas.requests.skills_crud import SkillCreateRequest, SkillUpdateRequest
from apps.api.schemas.responses import SkillDefinitionResponse, SkillListResponse
from apps.api.services.skills import SkillsService
from apps.api.services.skills_crud import SkillCrudService

router = APIRouter(prefix="/skills", tags=["Skills"])


def _get_skills_service() -> SkillsService:
    """Get skills service for filesystem discovery."""
    return SkillsService(project_path=Path.cwd())


@router.get("", response_model=SkillListResponse)
async def list_skills(
    _api_key: ApiKey,
    cache: Cache,
    source: str | None = Query(
        None,
        description="Filter by source: 'filesystem', 'database', or None for both",
    ),
) -> SkillListResponse:
    """List all skills from filesystem and database.

    Skills are discovered from:
    - Filesystem: .claude/skills/*.md (with YAML frontmatter)
    - Database: Skills created via API

    Use the 'source' query param to filter by source.
    """
    skills: list[SkillDefinitionResponse] = []

    # Get filesystem skills (unless filtering to database only)
    if source != "database":
        fs_service = _get_skills_service()
        fs_skills = fs_service.discover_skills()
        for skill in fs_skills:
            # Read content from file
            try:
                content = Path(skill["path"]).read_text()
            except OSError:
                content = ""

            skills.append(
                SkillDefinitionResponse(
                    id=f"fs:{skill['name']}",  # Prefix to distinguish from DB
                    name=skill["name"],
                    description=skill["description"],
                    content=content,
                    enabled=True,
                    source="filesystem",
                    path=skill["path"],
                )
            )

    # Get database skills (unless filtering to filesystem only)
    if source != "filesystem":
        db_service = SkillCrudService(cache)
        db_skills = await db_service.list_skills()
        for s in db_skills:
            skills.append(
                SkillDefinitionResponse(
                    id=s.id,
                    name=s.name,
                    description=s.description,
                    content=s.content,
                    enabled=s.enabled,
                    created_at=s.created_at,  # type: ignore[arg-type]
                    updated_at=s.updated_at,  # type: ignore[arg-type]
                    is_shared=s.is_shared,
                    share_url=s.share_url,
                    source="database",
                )
            )

    return SkillListResponse(skills=skills)


@router.post("", response_model=SkillDefinitionResponse, status_code=201)
async def create_skill(
    request: SkillCreateRequest,
    _api_key: ApiKey,
    cache: Cache,
) -> SkillDefinitionResponse:
    """Create a new skill in the database.

    Note: To add filesystem-based skills, create a .md file in .claude/skills/
    with YAML frontmatter containing 'name' and 'description' fields.
    """
    service = SkillCrudService(cache)
    skill = await service.create_skill(
        name=request.name,
        description=request.description,
        content=request.content,
        enabled=request.enabled,
    )
    return SkillDefinitionResponse(
        id=skill.id,
        name=skill.name,
        description=skill.description,
        content=skill.content,
        enabled=skill.enabled,
        created_at=skill.created_at,  # type: ignore[arg-type]
        updated_at=skill.updated_at,  # type: ignore[arg-type]
        is_shared=skill.is_shared,
        share_url=skill.share_url,
        source="database",
    )


@router.get("/{skill_id}", response_model=SkillDefinitionResponse)
async def get_skill(
    skill_id: str,
    _api_key: ApiKey,
    cache: Cache,
) -> SkillDefinitionResponse:
    """Get skill details by ID.

    For filesystem skills, use the 'fs:' prefix (e.g., 'fs:my-skill').
    For database skills, use the UUID directly.
    """
    # Check if it's a filesystem skill
    if skill_id.startswith("fs:"):
        skill_name = skill_id[3:]  # Remove 'fs:' prefix
        fs_service = _get_skills_service()
        fs_skills = fs_service.discover_skills()

        for skill in fs_skills:
            if skill["name"] == skill_name:
                try:
                    content = Path(skill["path"]).read_text()
                except OSError:
                    content = ""

                return SkillDefinitionResponse(
                    id=skill_id,
                    name=skill["name"],
                    description=skill["description"],
                    content=content,
                    enabled=True,
                    source="filesystem",
                    path=skill["path"],
                )

        raise APIError(
            message="Filesystem skill not found",
            code="SKILL_NOT_FOUND",
            status_code=404,
        )

    # Otherwise, look up in database
    service = SkillCrudService(cache)
    skill = await service.get_skill(skill_id)
    if skill is None:
        raise APIError(
            message="Skill not found",
            code="SKILL_NOT_FOUND",
            status_code=404,
        )
    return SkillDefinitionResponse(
        id=skill.id,
        name=skill.name,
        description=skill.description,
        content=skill.content,
        enabled=skill.enabled,
        created_at=skill.created_at,  # type: ignore[arg-type]
        updated_at=skill.updated_at,  # type: ignore[arg-type]
        is_shared=skill.is_shared,
        share_url=skill.share_url,
        source="database",
    )


@router.put("/{skill_id}", response_model=SkillDefinitionResponse)
async def update_skill(
    skill_id: str,
    request: SkillUpdateRequest,
    _api_key: ApiKey,
    cache: Cache,
) -> SkillDefinitionResponse:
    """Update a database skill.

    Note: Filesystem skills cannot be updated via API.
    Edit the .md file directly in .claude/skills/.
    """
    # Filesystem skills cannot be updated via API
    if skill_id.startswith("fs:"):
        raise APIError(
            message="Filesystem skills cannot be updated via API. Edit the file directly.",
            code="SKILL_READONLY",
            status_code=400,
        )

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
    return SkillDefinitionResponse(
        id=skill.id,
        name=skill.name,
        description=skill.description,
        content=skill.content,
        enabled=skill.enabled,
        created_at=skill.created_at,  # type: ignore[arg-type]
        updated_at=skill.updated_at,  # type: ignore[arg-type]
        is_shared=skill.is_shared,
        share_url=skill.share_url,
        source="database",
    )


@router.delete("/{skill_id}", status_code=204)
async def delete_skill(
    skill_id: str,
    _api_key: ApiKey,
    cache: Cache,
) -> None:
    """Delete a database skill.

    Note: Filesystem skills cannot be deleted via API.
    Delete the .md file directly from .claude/skills/.
    """
    # Filesystem skills cannot be deleted via API
    if skill_id.startswith("fs:"):
        raise APIError(
            message="Filesystem skills cannot be deleted via API. Delete the file directly.",
            code="SKILL_READONLY",
            status_code=400,
        )

    service = SkillCrudService(cache)
    deleted = await service.delete_skill(skill_id)
    if not deleted:
        raise APIError(
            message="Skill not found",
            code="SKILL_NOT_FOUND",
            status_code=404,
        )
