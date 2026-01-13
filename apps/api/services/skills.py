"""Skills discovery and management service.

Discovers skills from:
1. Global: ~/.claude/skills/*/SKILL.md
2. Project: .claude/skills/*/SKILL.md
"""

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
    source: str  # "global" or "project"


class SkillsService:
    """Service for discovering and managing skills from filesystem.

    Skills are discovered from:
    - Global: ~/.claude/skills/*/SKILL.md
    - Project: .claude/skills/*/SKILL.md

    Each skill is a directory containing a SKILL.md file with YAML frontmatter.
    """

    def __init__(
        self,
        project_path: Path | str | None = None,
        home_path: Path | str | None = None,
    ) -> None:
        """Initialize skills service.

        Args:
            project_path: Path to project root containing .claude/skills/
            home_path: Path to home directory (defaults to ~)
        """
        self.project_path = Path(project_path) if project_path else Path.cwd()
        self.home_path = Path(home_path) if home_path else Path.home()
        self.project_skills_dir = self.project_path / ".claude" / "skills"
        self.global_skills_dir = self.home_path / ".claude" / "skills"

    def discover_skills(self) -> list[SkillInfo]:
        """Discover skills from both global and project directories.

        Order of discovery:
        1. Global ~/.claude/skills/*/SKILL.md
        2. Project .claude/skills/*/SKILL.md (can override global)

        Returns:
            List of skill info dictionaries with name, description, path, source
        """
        skills: dict[str, SkillInfo] = {}

        # Discover global skills first
        global_skills = self._discover_from_dir(self.global_skills_dir, "global")
        for skill in global_skills:
            skills[skill["name"]] = skill

        # Discover project skills (override global with same name)
        project_skills = self._discover_from_dir(self.project_skills_dir, "project")
        for skill in project_skills:
            skills[skill["name"]] = skill

        logger.debug(
            "skills_discovered",
            global_count=len(global_skills),
            project_count=len(project_skills),
            total_count=len(skills),
            skills=list(skills.keys()),
        )

        return list(skills.values())

    def _discover_from_dir(self, skills_dir: Path, source: str) -> list[SkillInfo]:
        """Discover skills from a specific directory.

        Looks for:
        - skills_dir/*/SKILL.md (subdirectory pattern)
        - skills_dir/*.md (legacy flat file pattern)

        Args:
            skills_dir: Directory to search for skills.
            source: Source label ("global" or "project").

        Returns:
            List of discovered skills.
        """
        if not skills_dir.exists():
            return []

        skills: list[SkillInfo] = []

        # Pattern 1: Subdirectory with SKILL.md (preferred)
        for skill_file in skills_dir.glob("*/SKILL.md"):
            skill_info = self._parse_skill_file(skill_file, source)
            if skill_info:
                skills.append(skill_info)

        # Pattern 2: Direct .md files in skills dir (legacy)
        for skill_file in skills_dir.glob("*.md"):
            # Skip if it's a SKILL.md in root (shouldn't happen but be safe)
            if skill_file.name == "SKILL.md":
                continue
            skill_info = self._parse_skill_file(skill_file, source)
            if skill_info:
                skills.append(skill_info)

        return skills

    def _parse_skill_file(self, file_path: Path, source: str) -> SkillInfo | None:
        """Parse skill markdown file and extract frontmatter.

        Args:
            file_path: Path to skill .md file
            source: Source label ("global" or "project")

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
                source=source,
            )

        except (OSError, UnicodeDecodeError, ValueError) as e:
            logger.error(
                "skill_file_parse_error",
                file_path=str(file_path),
                error_type=type(e).__name__,
                error_message=str(e),
            )
            return None
