"""Agent persistence service."""

import secrets
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import cast
from uuid import uuid4

from apps.api.protocols import Cache


@dataclass
class AgentRecord:
    """<summary>Agent record stored in cache.</summary>"""

    id: str
    name: str
    description: str
    prompt: str
    tools: list[str] | None
    model: str | None
    created_at: str
    updated_at: str | None
    is_shared: bool | None
    share_url: str | None
    share_token: str | None


class AgentService:
    """<summary>Service for managing agents in cache.</summary>"""

    _INDEX_KEY = "agents:index"

    def __init__(self, cache: Cache) -> None:
        """<summary>Initialize agent service.</summary>"""
        self._cache = cache

    def _agent_key(self, agent_id: str) -> str:
        """<summary>Build cache key for an agent.</summary>"""
        return f"agent:{agent_id}"

    def _parse_tools(
        self,
        raw_tools: object,
    ) -> list[str] | None:
        """Normalize cached tools payload to optional list[str]."""
        if raw_tools is None:
            return None
        if not isinstance(raw_tools, list):
            return None
        tools: list[str] = []
        for tool in raw_tools:
            if isinstance(tool, str):
                tools.append(tool)
        return tools or None

    async def list_agents(self) -> list[AgentRecord]:
        """<summary>List all agents.</summary>"""
        ids = await self._cache.set_members(self._INDEX_KEY)
        if not ids:
            return []

        keys = [self._agent_key(agent_id) for agent_id in ids]
        raw_agents = await self._cache.get_many_json(keys)
        agents: list[AgentRecord] = []

        for agent_id, raw in zip(ids, raw_agents, strict=True):
            if raw is None:
                await self._cache.remove_from_set(self._INDEX_KEY, agent_id)
                continue
            agents.append(
                AgentRecord(
                    id=str(raw.get("id", agent_id)),
                    name=str(raw.get("name", "")),
                    description=str(raw.get("description", "")),
                    prompt=str(raw.get("prompt", "")),
                    tools=self._parse_tools(raw.get("tools")),
                    model=cast("str | None", raw.get("model")),
                    created_at=str(raw.get("created_at", "")),
                    updated_at=cast("str | None", raw.get("updated_at")),
                    is_shared=cast("bool | None", raw.get("is_shared")),
                    share_url=cast("str | None", raw.get("share_url")),
                    share_token=cast("str | None", raw.get("share_token")),
                )
            )

        return agents

    async def create_agent(
        self,
        name: str,
        description: str,
        prompt: str,
        tools: list[str] | None,
        model: str | None,
    ) -> AgentRecord:
        """<summary>Create a new agent.</summary>"""
        agent_id = str(uuid4())
        now = datetime.now(UTC).isoformat()
        agent = AgentRecord(
            id=agent_id,
            name=name,
            description=description,
            prompt=prompt,
            tools=tools,
            model=model,
            created_at=now,
            updated_at=None,
            is_shared=False,
            share_url=None,
            share_token=None,
        )

        await self._cache.set_json(self._agent_key(agent_id), agent.__dict__)
        await self._cache.add_to_set(self._INDEX_KEY, agent_id)
        return agent

    async def get_agent(self, agent_id: str) -> AgentRecord | None:
        """<summary>Get an agent by ID.</summary>"""
        raw = await self._cache.get_json(self._agent_key(agent_id))
        if raw is None:
            return None
        return AgentRecord(
            id=str(raw.get("id", agent_id)),
            name=str(raw.get("name", "")),
            description=str(raw.get("description", "")),
            prompt=str(raw.get("prompt", "")),
            tools=self._parse_tools(raw.get("tools")),
            model=cast("str | None", raw.get("model")),
            created_at=str(raw.get("created_at", "")),
            updated_at=cast("str | None", raw.get("updated_at")),
            is_shared=cast("bool | None", raw.get("is_shared")),
            share_url=cast("str | None", raw.get("share_url")),
            share_token=cast("str | None", raw.get("share_token")),
        )

    async def update_agent(
        self,
        agent_id: str,
        name: str,
        description: str,
        prompt: str,
        tools: list[str] | None,
        model: str | None,
    ) -> AgentRecord | None:
        """<summary>Update an agent.</summary>"""
        existing = await self.get_agent(agent_id)
        if existing is None:
            return None

        updated = AgentRecord(
            id=existing.id,
            name=name,
            description=description,
            prompt=prompt,
            tools=tools,
            model=model,
            created_at=existing.created_at,
            updated_at=datetime.now(UTC).isoformat(),
            is_shared=existing.is_shared,
            share_url=existing.share_url,
            share_token=existing.share_token,
        )

        await self._cache.set_json(self._agent_key(agent_id), updated.__dict__)
        return updated

    async def delete_agent(self, agent_id: str) -> bool:
        """<summary>Delete an agent.</summary>"""
        await self._cache.remove_from_set(self._INDEX_KEY, agent_id)
        return await self._cache.delete(self._agent_key(agent_id))

    async def share_agent(self, agent_id: str, share_url: str) -> AgentRecord | None:
        """<summary>Mark an agent as shared and assign a token.</summary>"""
        existing = await self.get_agent(agent_id)
        if existing is None:
            return None

        token = secrets.token_urlsafe(24)
        updated = AgentRecord(
            id=existing.id,
            name=existing.name,
            description=existing.description,
            prompt=existing.prompt,
            tools=existing.tools,
            model=existing.model,
            created_at=existing.created_at,
            updated_at=existing.updated_at,
            is_shared=True,
            share_url=share_url,
            share_token=token,
        )

        await self._cache.set_json(self._agent_key(agent_id), updated.__dict__)
        return updated
