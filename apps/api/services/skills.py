"""Skills discovery and management service."""

import re
from pathlib import Path
from typing import TypedDict

import structlog

logger = structlog.get_logger(__name__)


class SkillInfo(TypedDict):
    """Information about a discovered skill."""

    name: str
    description: str
    path: str


class SkillsService:
    """Service for discovering and managing skills from filesystem."""

    def __init__(self, project_path: Path | str) -> None:
        """Initialize skills service.

        Args:
            project_path: Path to project root containing .claude/skills/
        """
        self.project_path = Path(project_path)
        self.skills_dir = self.project_path / ".claude" / "skills"

    def discover_skills(self) -> list[SkillInfo]:
        """Discover skills from .claude/skills/ directory.

        Returns:
            List of skill info dictionaries with name, description, path
        """
        if not self.skills_dir.exists():
            return []

        skills: list[SkillInfo] = []
        for skill_file in self.skills_dir.glob("*.md"):
            skill_info = self._parse_skill_file(skill_file)
            if skill_info:
                skills.append(skill_info)

        return skills

    def _parse_skill_file(self, file_path: Path) -> SkillInfo | None:
        """Parse skill markdown file and extract frontmatter.

        Args:
            file_path: Path to skill .md file

        Returns:
            SkillInfo dict or None if parsing fails
        """
        try:
            content = file_path.read_text()

            # Extract YAML frontmatter between --- delimiters
            frontmatter_match = re.match(
                r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL
            )

            if not frontmatter_match:
                logger.warning(
                    "skill_file_skipped_no_frontmatter",
                    file_path=str(file_path),
                    reason="missing_frontmatter",
                )
                return None

            frontmatter = frontmatter_match.group(1)

            # Extract name and description from frontmatter
            name_match = re.search(r"^name:\s*(.+)$", frontmatter, re.MULTILINE)
            desc_match = re.search(r"^description:\s*(.+)$", frontmatter, re.MULTILINE)

            if not name_match or not desc_match:
                logger.warning(
                    "skill_file_skipped_missing_fields",
                    file_path=str(file_path),
                    reason="missing_required_fields",
                    has_name=bool(name_match),
                    has_description=bool(desc_match),
                )
                return None

            return SkillInfo(
                name=name_match.group(1).strip(),
                description=desc_match.group(1).strip(),
                path=str(file_path),
            )

        except (OSError, UnicodeDecodeError, ValueError) as e:
            logger.error(
                "skill_file_parse_error",
                file_path=str(file_path),
                error_type=type(e).__name__,
                error_message=str(e),
            )
            return None
