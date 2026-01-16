"""Unit tests for skills discovery service."""

from pathlib import Path

from apps.api.services.skills import SkillsService


class TestSkillsDiscovery:
    """Test skills discovery from filesystem."""

    def test_discover_skills_from_project_directory(self, tmp_path: Path) -> None:
        """Test discovering skills from .claude/skills/ directory."""
        # Create test skill file
        skills_dir = tmp_path / ".claude" / "skills"
        skills_dir.mkdir(parents=True)
        skill_file = skills_dir / "test-skill.md"
        skill_file.write_text("""---
name: test-skill
description: A test skill for unit testing
---

This is a test skill.
""")

        # Discover skills (isolate from global skills)
        service = SkillsService(project_path=tmp_path, home_path=tmp_path)
        skills = service.discover_skills()

        # Assertions
        assert len(skills) == 1
        assert skills[0]["name"] == "test-skill"
        assert skills[0]["description"] == "A test skill for unit testing"
        assert skills[0]["path"] == str(skill_file)

    def test_discover_skills_returns_empty_when_no_directory(
        self, tmp_path: Path
    ) -> None:
        """Test discovering skills when .claude/skills/ doesn't exist."""
        service = SkillsService(project_path=tmp_path, home_path=tmp_path)
        skills = service.discover_skills()
        assert skills == []

    def test_discover_skills_skips_invalid_files(self, tmp_path: Path) -> None:
        """Test that invalid skill files are skipped."""
        skills_dir = tmp_path / ".claude" / "skills"
        skills_dir.mkdir(parents=True)

        # Create invalid file (no frontmatter)
        (skills_dir / "invalid.md").write_text("No frontmatter here")

        # Create valid file
        (skills_dir / "valid.md").write_text("""---
name: valid-skill
description: Valid skill
---
Content""")

        service = SkillsService(project_path=tmp_path, home_path=tmp_path)
        skills = service.discover_skills()

        assert len(skills) == 1
        assert skills[0]["name"] == "valid-skill"
