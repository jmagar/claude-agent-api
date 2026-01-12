"""Agent management endpoints."""

from fastapi import APIRouter, Request

from apps.api.dependencies import ApiKey, Cache
from apps.api.exceptions import APIError
from apps.api.schemas.requests.agents import AgentCreateRequest, AgentUpdateRequest
from apps.api.schemas.responses import AgentDefinitionResponse, AgentListResponse
from apps.api.services.agents import AgentService

router = APIRouter(prefix="/agents", tags=["Agents"])


@router.get("", response_model=AgentListResponse)
async def list_agents(
    _api_key: ApiKey,
    cache: Cache,
) -> AgentListResponse:
    """<summary>List all agents.</summary>"""
    service = AgentService(cache)
    agents = await service.list_agents()
    return AgentListResponse(agents=[AgentDefinitionResponse(**a.__dict__) for a in agents])


@router.post("", response_model=AgentDefinitionResponse, status_code=201)
async def create_agent(
    request: AgentCreateRequest,
    _api_key: ApiKey,
    cache: Cache,
) -> AgentDefinitionResponse:
    """<summary>Create a new agent.</summary>"""
    service = AgentService(cache)
    agent = await service.create_agent(
        name=request.name,
        description=request.description,
        prompt=request.prompt,
        tools=request.tools,
        model=request.model,
    )
    return AgentDefinitionResponse(**agent.__dict__)


@router.get("/{agent_id}", response_model=AgentDefinitionResponse)
async def get_agent(
    agent_id: str,
    _api_key: ApiKey,
    cache: Cache,
) -> AgentDefinitionResponse:
    """<summary>Get agent details.</summary>"""
    service = AgentService(cache)
    agent = await service.get_agent(agent_id)
    if agent is None:
        raise APIError(
            message="Agent not found",
            code="AGENT_NOT_FOUND",
            status_code=404,
        )
    return AgentDefinitionResponse(**agent.__dict__)


@router.put("/{agent_id}", response_model=AgentDefinitionResponse)
async def update_agent(
    agent_id: str,
    request: AgentUpdateRequest,
    _api_key: ApiKey,
    cache: Cache,
) -> AgentDefinitionResponse:
    """<summary>Update an agent.</summary>"""
    service = AgentService(cache)
    agent = await service.update_agent(
        agent_id=agent_id,
        name=request.name,
        description=request.description,
        prompt=request.prompt,
        tools=request.tools,
        model=request.model,
    )
    if agent is None:
        raise APIError(
            message="Agent not found",
            code="AGENT_NOT_FOUND",
            status_code=404,
        )
    return AgentDefinitionResponse(**agent.__dict__)


@router.delete("/{agent_id}", status_code=204)
async def delete_agent(
    agent_id: str,
    _api_key: ApiKey,
    cache: Cache,
) -> None:
    """<summary>Delete an agent.</summary>"""
    service = AgentService(cache)
    deleted = await service.delete_agent(agent_id)
    if not deleted:
        raise APIError(
            message="Agent not found",
            code="AGENT_NOT_FOUND",
            status_code=404,
        )


@router.post("/{agent_id}/share")
async def share_agent(
    agent_id: str,
    _api_key: ApiKey,
    cache: Cache,
    request: Request,
) -> dict[str, str]:
    """<summary>Generate a shareable link for an agent.</summary>"""
    service = AgentService(cache)
    base_url = str(request.base_url).rstrip("/")
    share_url = f"{base_url}/share/agents/{agent_id}"
    agent = await service.share_agent(agent_id, share_url)
    if agent is None or not agent.share_token:
        raise APIError(
            message="Agent not found",
            code="AGENT_NOT_FOUND",
            status_code=404,
        )
    return {"share_url": agent.share_url or share_url, "share_token": agent.share_token}
