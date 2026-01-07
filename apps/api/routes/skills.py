"""Skills API routes (T116b)."""

from fastapi import APIRouter, Depends

from apps.api.dependencies import verify_api_key
from apps.api.schemas.responses import SkillDiscoveryResponse, SkillResponse

router = APIRouter(prefix="/skills", tags=["skills"])


@router.get(
    "",
    response_model=SkillDiscoveryResponse,
    summary="List available skills",
    description="Returns list of skills available for use with the Skill tool.",
)
async def list_skills(
    _: str = Depends(verify_api_key),
) -> SkillDiscoveryResponse:
    """List all available skills.

    Skills are discovered from plugin configurations and
    .claude/skills directories. Returns an empty list if
    no skills are configured.

    Returns:
        SkillDiscoveryResponse with list of available skills.
    """
    # TODO: Implement actual skill discovery from filesystem/plugins
    # For now, return empty list as skills require filesystem configuration
    skills: list[SkillResponse] = []

    return SkillDiscoveryResponse(skills=skills)
