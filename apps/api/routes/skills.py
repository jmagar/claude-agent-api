"""Skills API routes (CRUD with filesystem discovery)."""

from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Query

from apps.api.dependencies import ApiKey, SkillCrudSvc, SkillsSvc
from apps.api.exceptions import APIError
from apps.api.schemas.requests.skills_crud import SkillCreateRequest, SkillUpdateRequest
from apps.api.schemas.responses import SkillDefinitionResponse, SkillListResponse
from apps.api.services.skills_crud import SkillRecord


def _parse_datetime(value: str | None) -> datetime | None:
    """Parse ISO timestamp string to datetime, or return None."""
    if value:
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            pass
    return None


router = APIRouter(prefix="/skills", tags=["Skills"])


@router.get("", response_model=SkillListResponse)
async def list_skills(
    _api_key: ApiKey,
    skills_discovery: SkillsSvc,
    skills_crud: SkillCrudSvc,
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
        fs_skills = skills_discovery.discover_skills()
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
        db_skills = await skills_crud.list_skills()
        for db_skill in db_skills:
            skills.append(
                SkillDefinitionResponse(
                    id=db_skill.id,
                    name=db_skill.name,
                    description=db_skill.description,
                    content=db_skill.content,
                    enabled=db_skill.enabled,
                    created_at=_parse_datetime(db_skill.created_at),
                    updated_at=_parse_datetime(db_skill.updated_at),
                    is_shared=db_skill.is_shared,
                    share_url=db_skill.share_url,
                    source="database",
                )
            )

    return SkillListResponse(skills=skills)


@router.post("", response_model=SkillDefinitionResponse, status_code=201)
async def create_skill(
    request: SkillCreateRequest,
    _api_key: ApiKey,
    skills_crud: SkillCrudSvc,
) -> SkillDefinitionResponse:
    """Create a new skill in the database.

    Note: To add filesystem-based skills, create a .md file in .claude/skills/
    with YAML frontmatter containing 'name' and 'description' fields.
    """
    created_skill = await skills_crud.create_skill(
        name=request.name,
        description=request.description,
        content=request.content,
        enabled=request.enabled,
    )
    return SkillDefinitionResponse(
        id=created_skill.id,
        name=created_skill.name,
        description=created_skill.description,
        content=created_skill.content,
        enabled=created_skill.enabled,
        created_at=_parse_datetime(created_skill.created_at),
        updated_at=_parse_datetime(created_skill.updated_at),
        is_shared=created_skill.is_shared,
        share_url=created_skill.share_url,
        source="database",
    )


@router.get("/{skill_id}", response_model=SkillDefinitionResponse)
async def get_skill(
    skill_id: str,
    _api_key: ApiKey,
    skills_discovery: SkillsSvc,
    skills_crud: SkillCrudSvc,
) -> SkillDefinitionResponse:
    """Get skill details by ID.

    For filesystem skills, use the 'fs:' prefix (e.g., 'fs:my-skill').
    For database skills, use the UUID directly.
    """
    # Check if it's a filesystem skill
    if skill_id.startswith("fs:"):
        skill_name = skill_id[3:]  # Remove 'fs:' prefix
        fs_skills = skills_discovery.discover_skills()

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
    db_skill: SkillRecord | None = await skills_crud.get_skill(skill_id)
    if db_skill is None:
        raise APIError(
            message="Skill not found",
            code="SKILL_NOT_FOUND",
            status_code=404,
        )
    return SkillDefinitionResponse(
        id=db_skill.id,
        name=db_skill.name,
        description=db_skill.description,
        content=db_skill.content,
        enabled=db_skill.enabled,
        created_at=_parse_datetime(db_skill.created_at),
        updated_at=_parse_datetime(db_skill.updated_at),
        is_shared=db_skill.is_shared,
        share_url=db_skill.share_url,
        source="database",
    )


@router.put("/{skill_id}", response_model=SkillDefinitionResponse)
async def update_skill(
    skill_id: str,
    request: SkillUpdateRequest,
    _api_key: ApiKey,
    skills_crud: SkillCrudSvc,
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

    updated_skill = await skills_crud.update_skill(
        skill_id=skill_id,
        name=request.name,
        description=request.description,
        content=request.content,
        enabled=request.enabled,
    )
    if updated_skill is None:
        raise APIError(
            message="Skill not found",
            code="SKILL_NOT_FOUND",
            status_code=404,
        )
    return SkillDefinitionResponse(
        id=updated_skill.id,
        name=updated_skill.name,
        description=updated_skill.description,
        content=updated_skill.content,
        enabled=updated_skill.enabled,
        created_at=_parse_datetime(updated_skill.created_at),
        updated_at=_parse_datetime(updated_skill.updated_at),
        is_shared=updated_skill.is_shared,
        share_url=updated_skill.share_url,
        source="database",
    )


@router.delete("/{skill_id}", status_code=204)
async def delete_skill(
    skill_id: str,
    _api_key: ApiKey,
    skills_crud: SkillCrudSvc,
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

    deleted = await skills_crud.delete_skill(skill_id)
    if not deleted:
        raise APIError(
            message="Skill not found",
            code="SKILL_NOT_FOUND",
            status_code=404,
        )
