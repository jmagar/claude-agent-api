"""Integration tests for skills API endpoint."""

from pathlib import Path

import pytest
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.anyio
async def test_skills_endpoint_returns_discovered_skills(
    async_client: AsyncClient,
    tmp_path: Path,
    auth_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test GET /skills returns skills from filesystem."""
    # Create test skill in tmp_path
    skills_dir = tmp_path / ".claude" / "skills"
    skills_dir.mkdir(parents=True)
    (skills_dir / "example.md").write_text("""---
name: example-skill
description: An example skill
---
Content here""")

    # Change working directory to tmp_path so the service discovers the skills
    monkeypatch.chdir(tmp_path)
    # Mock Path.home() to prevent discovering real global skills
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

    # Make request
    response = await async_client.get("/api/v1/skills", headers=auth_headers)

    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert "skills" in data
    assert len(data["skills"]) == 1
    assert data["skills"][0]["name"] == "example-skill"
    assert data["skills"][0]["description"] == "An example skill"


@pytest.mark.integration
@pytest.mark.anyio
async def test_skills_endpoint_returns_empty_when_no_skills(
    async_client: AsyncClient,
    tmp_path: Path,
    auth_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test GET /skills returns empty list when no skills exist."""
    # Change working directory to isolated tmp_path with no skills
    monkeypatch.chdir(tmp_path)
    # Mock Path.home() to prevent discovering real global skills
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)

    response = await async_client.get("/api/v1/skills", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["skills"] == []
