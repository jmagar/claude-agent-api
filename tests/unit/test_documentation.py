"""Unit tests for documentation completeness."""

from pathlib import Path

import pytest


@pytest.mark.unit
def test_adr_001_exists_and_has_required_sections() -> None:
    """Test that ADR-001 exists and contains required sections."""
    adr_path = Path("docs/adr/0001-distributed-session-state.md")

    assert adr_path.exists(), "ADR-001 should exist"

    content = adr_path.read_text()

    # Check required sections
    assert "# ADR-001" in content, "ADR should have title"
    assert "## Context" in content, "ADR should have Context section"
    assert "## Decision" in content, "ADR should have Decision section"
    assert "## Consequences" in content, "ADR should have Consequences section"
    assert "Redis" in content, "ADR should mention Redis"
    assert "PostgreSQL" in content, "ADR should mention PostgreSQL"


@pytest.mark.unit
def test_readme_has_distributed_session_section() -> None:
    """Test that README.md documents distributed session architecture."""
    readme_path = Path("README.md")

    assert readme_path.exists(), "README.md should exist"

    content = readme_path.read_text()

    assert "Distributed Session" in content, (
        "README should document distributed sessions"
    )
