"""Skill persistence service."""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import cast
from uuid import uuid4

from apps.api.protocols import Cache


@dataclass
class SkillRecord:
    """<summary>Skill record stored in cache.</summary>"""

    id: str
    name: str
    description: str
    content: str
    enabled: bool
    created_at: str
    updated_at: str | None
    is_shared: bool | None
    share_url: str | None


class SkillCrudService:
    """<summary>Service for managing skills in cache.</summary>"""

    _INDEX_KEY = "skills:index"

    def __init__(self, cache: Cache) -> None:
        """<summary>Initialize skill service.</summary>"""
        self._cache = cache

    def _skill_key(self, skill_id: str) -> str:
        """<summary>Build cache key for a skill.</summary>"""
        return f"skill:{skill_id}"

    async def list_skills(self) -> list[SkillRecord]:
        """<summary>List all skills.</summary>"""
        ids = await self._cache.set_members(self._INDEX_KEY)
        if not ids:
            return []

        keys = [self._skill_key(skill_id) for skill_id in ids]
        raw_skills = await self._cache.get_many_json(keys)
        skills: list[SkillRecord] = []

        for skill_id, raw in zip(ids, raw_skills, strict=True):
            if raw is None:
                await self._cache.remove_from_set(self._INDEX_KEY, skill_id)
                continue
            skills.append(
                SkillRecord(
                    id=str(raw.get("id", skill_id)),
                    name=str(raw.get("name", "")),
                    description=str(raw.get("description", "")),
                    content=str(raw.get("content", "")),
                    enabled=bool(raw.get("enabled", True)),
                    created_at=str(raw.get("created_at", "")),
                    updated_at=cast("str | None", raw.get("updated_at")),
                    is_shared=cast("bool | None", raw.get("is_shared")),
                    share_url=cast("str | None", raw.get("share_url")),
                )
            )

        return skills

    async def create_skill(
        self,
        name: str,
        description: str,
        content: str,
        enabled: bool,
    ) -> SkillRecord:
        """<summary>Create a skill.</summary>"""
        skill_id = str(uuid4())
        now = datetime.now(UTC).isoformat()
        skill = SkillRecord(
            id=skill_id,
            name=name,
            description=description,
            content=content,
            enabled=enabled,
            created_at=now,
            updated_at=None,
            is_shared=False,
            share_url=None,
        )

        await self._cache.set_json(self._skill_key(skill_id), skill.__dict__)
        await self._cache.add_to_set(self._INDEX_KEY, skill_id)
        return skill

    async def get_skill(self, skill_id: str) -> SkillRecord | None:
        """<summary>Get a skill by ID.</summary>"""
        raw = await self._cache.get_json(self._skill_key(skill_id))
        if raw is None:
            return None
        return SkillRecord(
            id=str(raw.get("id", skill_id)),
            name=str(raw.get("name", "")),
            description=str(raw.get("description", "")),
            content=str(raw.get("content", "")),
            enabled=bool(raw.get("enabled", True)),
            created_at=str(raw.get("created_at", "")),
            updated_at=cast("str | None", raw.get("updated_at")),
            is_shared=cast("bool | None", raw.get("is_shared")),
            share_url=cast("str | None", raw.get("share_url")),
        )

    async def update_skill(
        self,
        skill_id: str,
        name: str,
        description: str,
        content: str,
        enabled: bool,
    ) -> SkillRecord | None:
        """<summary>Update a skill.</summary>"""
        existing = await self.get_skill(skill_id)
        if existing is None:
            return None

        updated = SkillRecord(
            id=existing.id,
            name=name,
            description=description,
            content=content,
            enabled=enabled,
            created_at=existing.created_at,
            updated_at=datetime.now(UTC).isoformat(),
            is_shared=existing.is_shared,
            share_url=existing.share_url,
        )

        await self._cache.set_json(self._skill_key(skill_id), updated.__dict__)
        return updated

    async def delete_skill(self, skill_id: str) -> bool:
        """<summary>Delete a skill.</summary>"""
        await self._cache.remove_from_set(self._INDEX_KEY, skill_id)
        return await self._cache.delete(self._skill_key(skill_id))
