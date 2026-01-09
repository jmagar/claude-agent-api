"""Skills API routes (T116b)."""

from fastapi import APIRouter

from apps.api.dependencies import ApiKey, SkillsSvc
from apps.api.schemas.responses import SkillDiscoveryResponse, SkillResponse

router = APIRouter(prefix="/skills", tags=["skills"])


@router.get(
    "",
    response_model=SkillDiscoveryResponse,
    summary="List available skills",
    description="Returns list of skills available for use with the Skill tool.",
)
async def list_skills(
    _api_key: ApiKey,
    skills_service: SkillsSvc,
) -> SkillDiscoveryResponse:
    """List all available skills.

    Skills are discovered from plugin configurations and
    .claude/skills directories. Returns an empty list if
    no skills are configured.

    Returns:
        SkillDiscoveryResponse with list of available skills.
    """
    discovered_skills = skills_service.discover_skills()

    skills = [
        SkillResponse(
            name=skill["name"],
            description=skill["description"],
            path=skill["path"],
        )
        for skill in discovered_skills
    ]

    return SkillDiscoveryResponse(skills=skills)
