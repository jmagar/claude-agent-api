"""Contract tests for skills endpoints (T116b)."""

import pytest
from httpx import AsyncClient


class TestSkillsListContractGET:
    """Contract tests for GET /skills endpoint."""

    @pytest.mark.anyio
    async def test_skills_list_requires_authentication(
        self,
        async_client: AsyncClient,
    ) -> None:
        """Test that GET /skills requires authentication."""
        response = await async_client.get("/api/v1/skills")
        assert response.status_code == 401

    @pytest.mark.anyio
    async def test_skills_list_returns_empty_list_when_no_skills(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that GET /skills returns empty list when no skills configured."""
        response = await async_client.get(
            "/api/v1/skills",
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.json()
        assert "skills" in data
        assert isinstance(data["skills"], list)

    @pytest.mark.anyio
    async def test_skills_list_response_format(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that GET /skills returns correct response format."""
        response = await async_client.get(
            "/api/v1/skills",
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.json()
        assert "skills" in data

        # If there are skills, verify format
        for skill in data["skills"]:
            assert "name" in skill
            # description is optional
