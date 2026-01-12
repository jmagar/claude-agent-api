"""Slash command persistence service."""

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

from apps.api.protocols import Cache


@dataclass
class SlashCommandRecord:
    """<summary>Slash command record stored in cache.</summary>"""

    id: str
    name: str
    description: str
    content: str
    enabled: bool
    created_at: str
    updated_at: str | None


class SlashCommandService:
    """<summary>Service for managing slash commands in cache.</summary>"""

    _INDEX_KEY = "slash_commands:index"

    def __init__(self, cache: Cache) -> None:
        """<summary>Initialize slash command service.</summary>"""
        self._cache = cache

    def _command_key(self, command_id: str) -> str:
        """<summary>Build cache key for a slash command.</summary>"""
        return f"slash_command:{command_id}"

    async def list_commands(self) -> list[SlashCommandRecord]:
        """<summary>List all slash commands.</summary>"""
        ids = await self._cache.set_members(self._INDEX_KEY)
        if not ids:
            return []

        keys = [self._command_key(command_id) for command_id in ids]
        raw_commands = await self._cache.get_many_json(keys)
        commands: list[SlashCommandRecord] = []

        for command_id, raw in zip(ids, raw_commands):
            if raw is None:
                await self._cache.remove_from_set(self._INDEX_KEY, command_id)
                continue
            commands.append(
                SlashCommandRecord(
                    id=str(raw.get("id", command_id)),
                    name=str(raw.get("name", "")),
                    description=str(raw.get("description", "")),
                    content=str(raw.get("content", "")),
                    enabled=bool(raw.get("enabled", True)),
                    created_at=str(raw.get("created_at", "")),
                    updated_at=raw.get("updated_at"),
                )
            )

        return commands

    async def create_command(
        self,
        name: str,
        description: str,
        content: str,
        enabled: bool,
    ) -> SlashCommandRecord:
        """<summary>Create a slash command.</summary>"""
        command_id = str(uuid4())
        now = datetime.now(UTC).isoformat()
        command = SlashCommandRecord(
            id=command_id,
            name=name,
            description=description,
            content=content,
            enabled=enabled,
            created_at=now,
            updated_at=None,
        )

        await self._cache.set_json(self._command_key(command_id), command.__dict__)
        await self._cache.add_to_set(self._INDEX_KEY, command_id)
        return command

    async def get_command(self, command_id: str) -> SlashCommandRecord | None:
        """<summary>Get a slash command by ID.</summary>"""
        raw = await self._cache.get_json(self._command_key(command_id))
        if raw is None:
            return None
        return SlashCommandRecord(
            id=str(raw.get("id", command_id)),
            name=str(raw.get("name", "")),
            description=str(raw.get("description", "")),
            content=str(raw.get("content", "")),
            enabled=bool(raw.get("enabled", True)),
            created_at=str(raw.get("created_at", "")),
            updated_at=raw.get("updated_at"),
        )

    async def update_command(
        self,
        command_id: str,
        name: str,
        description: str,
        content: str,
        enabled: bool,
    ) -> SlashCommandRecord | None:
        """<summary>Update a slash command.</summary>"""
        existing = await self.get_command(command_id)
        if existing is None:
            return None

        updated = SlashCommandRecord(
            id=existing.id,
            name=name,
            description=description,
            content=content,
            enabled=enabled,
            created_at=existing.created_at,
            updated_at=datetime.now(UTC).isoformat(),
        )

        await self._cache.set_json(self._command_key(command_id), updated.__dict__)
        return updated

    async def delete_command(self, command_id: str) -> bool:
        """<summary>Delete a slash command.</summary>"""
        await self._cache.remove_from_set(self._INDEX_KEY, command_id)
        return await self._cache.delete(self._command_key(command_id))
