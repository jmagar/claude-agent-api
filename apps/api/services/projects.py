"""Project persistence service."""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from apps.api.protocols import Cache


@dataclass
class ProjectRecord:
    """<summary>Project record stored in cache.</summary>"""

    id: str
    name: str
    path: str
    created_at: str
    last_accessed_at: str | None
    session_count: int | None
    metadata: dict[str, object] | None


class ProjectService:
    """<summary>Service for managing projects in cache.</summary>"""

    _INDEX_KEY = "projects:index"

    def __init__(self, cache: Cache) -> None:
        """<summary>Initialize project service.</summary>"""
        self._cache = cache

    def _project_key(self, project_id: str) -> str:
        """<summary>Build cache key for a project.</summary>"""
        return f"project:{project_id}"

    async def list_projects(self) -> list[ProjectRecord]:
        """<summary>List all projects.</summary>"""
        ids = await self._cache.set_members(self._INDEX_KEY)
        if not ids:
            return []

        keys = [self._project_key(project_id) for project_id in ids]
        raw_projects = await self._cache.get_many_json(keys)
        projects: list[ProjectRecord] = []

        for project_id, raw in zip(ids, raw_projects, strict=True):
            if raw is None:
                await self._cache.remove_from_set(self._INDEX_KEY, project_id)
                continue
            projects.append(
                ProjectRecord(
                    id=str(raw.get("id", project_id)),
                    name=str(raw.get("name", "")),
                    path=str(raw.get("path", "")),
                    created_at=str(raw.get("created_at", "")),
                    last_accessed_at=cast("str | None", raw.get("last_accessed_at")),
                    session_count=cast("int | None", raw.get("session_count")),
                    metadata=cast("dict[str, Any] | None", raw.get("metadata")),
                )
            )

        return projects

    async def create_project(
        self,
        name: str,
        path: str | None,
        metadata: dict[str, object] | None,
    ) -> ProjectRecord | None:
        """<summary>Create a project if name/path are unique.</summary>"""
        existing = await self.list_projects()
        normalized_path = path or name
        for project in existing:
            if project.name == name or project.path == normalized_path:
                return None

        project_id = str(uuid4())
        now = datetime.now(UTC).isoformat()
        project = ProjectRecord(
            id=project_id,
            name=name,
            path=normalized_path,
            created_at=now,
            last_accessed_at=None,
            session_count=0,
            metadata=metadata,
        )

        await self._cache.set_json(self._project_key(project_id), project.__dict__)
        await self._cache.add_to_set(self._INDEX_KEY, project_id)
        return project

    async def get_project(self, project_id: str) -> ProjectRecord | None:
        """<summary>Get a project by ID.</summary>"""
        raw = await self._cache.get_json(self._project_key(project_id))
        if raw is None:
            return None
        return ProjectRecord(
            id=str(raw.get("id", project_id)),
            name=str(raw.get("name", "")),
            path=str(raw.get("path", "")),
            created_at=str(raw.get("created_at", "")),
            last_accessed_at=cast("str | None", raw.get("last_accessed_at")),
            session_count=cast("int | None", raw.get("session_count")),
            metadata=cast("dict[str, Any] | None", raw.get("metadata")),
        )

    async def update_project(
        self,
        project_id: str,
        name: str | None,
        metadata: dict[str, object] | None,
    ) -> ProjectRecord | None:
        """<summary>Update a project.</summary>"""
        existing = await self.get_project(project_id)
        if existing is None:
            return None

        updated = ProjectRecord(
            id=existing.id,
            name=name or existing.name,
            path=existing.path,
            created_at=existing.created_at,
            last_accessed_at=existing.last_accessed_at,
            session_count=existing.session_count,
            metadata=metadata if metadata is not None else existing.metadata,
        )

        await self._cache.set_json(self._project_key(project_id), updated.__dict__)
        return updated

    async def delete_project(self, project_id: str) -> bool:
        """<summary>Delete a project.</summary>"""
        await self._cache.remove_from_set(self._INDEX_KEY, project_id)
        return await self._cache.delete(self._project_key(project_id))
