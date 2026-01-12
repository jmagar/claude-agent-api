"""Tool preset persistence service."""

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

import structlog

from apps.api.protocols import Cache

logger = structlog.get_logger(__name__)


@dataclass
class ToolPreset:
    """Tool preset stored in cache."""

    id: str
    name: str
    description: str | None
    allowed_tools: list[str]
    disallowed_tools: list[str]
    is_system: bool
    created_at: str


class ToolPresetService:
    """Service for managing tool presets in cache."""

    _INDEX_KEY = "tool_presets:index"

    def __init__(self, cache: Cache) -> None:
        """Initialize the tool preset service.

        Args:
            cache: Cache backend.
        """
        self._cache = cache

    def _preset_key(self, preset_id: str) -> str:
        """Generate cache key for a tool preset."""
        return f"tool_preset:{preset_id}"

    async def create_preset(
        self,
        name: str,
        description: str | None,
        allowed_tools: list[str],
        disallowed_tools: list[str],
        is_system: bool = False,
    ) -> ToolPreset:
        """Create and store a tool preset."""
        preset = ToolPreset(
            id=str(uuid4()),
            name=name,
            description=description,
            allowed_tools=allowed_tools,
            disallowed_tools=disallowed_tools,
            is_system=is_system,
            created_at=datetime.now(UTC).isoformat(),
        )

        await self._cache.set_json(self._preset_key(preset.id), preset.__dict__)
        await self._cache.add_to_set(self._INDEX_KEY, preset.id)
        return preset

    async def list_presets(self) -> list[ToolPreset]:
        """List all stored tool presets."""
        ids = await self._cache.set_members(self._INDEX_KEY)
        if not ids:
            return []

        keys = [self._preset_key(preset_id) for preset_id in ids]
        raw_presets = await self._cache.get_many_json(keys)
        presets: list[ToolPreset] = []

        for preset_id, raw in zip(ids, raw_presets):
            if raw is None:
                await self._cache.remove_from_set(self._INDEX_KEY, preset_id)
                continue
            presets.append(
                ToolPreset(
                    id=str(raw.get("id", preset_id)),
                    name=str(raw.get("name", "")),
                    description=raw.get("description"),
                    allowed_tools=list(raw.get("allowed_tools", [])),
                    disallowed_tools=list(raw.get("disallowed_tools", [])),
                    is_system=bool(raw.get("is_system", False)),
                    created_at=str(raw.get("created_at", "")),
                )
            )

        return presets

    async def get_preset(self, preset_id: str) -> ToolPreset | None:
        """Get a tool preset by ID."""
        raw = await self._cache.get_json(self._preset_key(preset_id))
        if raw is None:
            return None
        return ToolPreset(
            id=str(raw.get("id", preset_id)),
            name=str(raw.get("name", "")),
            description=raw.get("description"),
            allowed_tools=list(raw.get("allowed_tools", [])),
            disallowed_tools=list(raw.get("disallowed_tools", [])),
            is_system=bool(raw.get("is_system", False)),
            created_at=str(raw.get("created_at", "")),
        )

    async def update_preset(
        self,
        preset_id: str,
        name: str,
        description: str | None,
        allowed_tools: list[str],
        disallowed_tools: list[str],
    ) -> ToolPreset | None:
        """Update a tool preset by ID."""
        existing = await self.get_preset(preset_id)
        if existing is None:
            return None

        updated = ToolPreset(
            id=existing.id,
            name=name,
            description=description,
            allowed_tools=allowed_tools,
            disallowed_tools=disallowed_tools,
            is_system=existing.is_system,
            created_at=existing.created_at,
        )

        await self._cache.set_json(self._preset_key(preset_id), updated.__dict__)
        return updated

    async def delete_preset(self, preset_id: str) -> bool:
        """Delete a tool preset by ID."""
        await self._cache.remove_from_set(self._INDEX_KEY, preset_id)
        return await self._cache.delete(self._preset_key(preset_id))
