"""Agent management endpoints."""

from typing import cast

from fastapi import APIRouter, Request

from apps.api.dependencies import AgentConfigSvc, ApiKey
from apps.api.exceptions import APIError
from apps.api.schemas.requests.agents import AgentCreateRequest, AgentUpdateRequest
from apps.api.schemas.responses import AgentDefinitionResponse, AgentListResponse

router = APIRouter(prefix="/agents", tags=["Agents"])


@router.get("", response_model=AgentListResponse)
async def list_agents(
    _api_key: ApiKey,
    agent_service: AgentConfigSvc,
) -> AgentListResponse:
    """<summary>List all agents.</summary>"""
    agents = await agent_service.list_agents()
    return AgentListResponse(
        agents=[
            AgentDefinitionResponse.model_validate(a, from_attributes=True)
            for a in agents
        ]
    )


@router.post("", response_model=AgentDefinitionResponse, status_code=201)
async def create_agent(
    request: AgentCreateRequest,
    _api_key: ApiKey,
    agent_service: AgentConfigSvc,
) -> AgentDefinitionResponse:
    """<summary>Create a new agent.</summary>"""
    agent = await agent_service.create_agent(
        name=request.name,
        description=request.description,
        prompt=request.prompt,
        tools=request.tools,
        model=request.model,
    )
    return AgentDefinitionResponse.model_validate(agent, from_attributes=True)


@router.get("/{agent_id}", response_model=AgentDefinitionResponse)
async def get_agent(
    agent_id: str,
    _api_key: ApiKey,
    agent_service: AgentConfigSvc,
) -> AgentDefinitionResponse:
    """<summary>Get agent details.</summary>"""
    agent = await agent_service.get_agent(agent_id)
    if agent is None:
        raise APIError(
            message="Agent not found",
            code="AGENT_NOT_FOUND",
            status_code=404,
        )
    return AgentDefinitionResponse.model_validate(agent, from_attributes=True)


@router.put("/{agent_id}", response_model=AgentDefinitionResponse)
async def update_agent(
    agent_id: str,
    request: AgentUpdateRequest,
    _api_key: ApiKey,
    agent_service: AgentConfigSvc,
) -> AgentDefinitionResponse:
    """<summary>Update an agent.</summary>"""
    agent = await agent_service.update_agent(
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
    return AgentDefinitionResponse.model_validate(agent, from_attributes=True)


@router.delete("/{agent_id}", status_code=204)
async def delete_agent(
    agent_id: str,
    _api_key: ApiKey,
    agent_service: AgentConfigSvc,
) -> None:
    """<summary>Delete an agent.</summary>"""
    deleted = await agent_service.delete_agent(agent_id)
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
    agent_service: AgentConfigSvc,
    request: Request,
) -> dict[str, str]:
    """<summary>Generate a shareable link for an agent.</summary>"""
    base_url = str(request.base_url).rstrip("/")
    share_url = f"{base_url}/share/agents/{agent_id}"
    agent = await agent_service.share_agent(agent_id, share_url)
    if agent is None:
        raise APIError(
            message="Agent not found",
            code="AGENT_NOT_FOUND",
            status_code=404,
        )
    if not hasattr(agent, "share_token") or not agent.share_token:
        raise APIError(
            message="Agent share token generation failed",
            code="AGENT_SHARE_FAILED",
            status_code=500,
        )

    # Type checker needs help here - protocol returns object but we know it has these attributes
    share_url_value = cast("str", getattr(agent, "share_url", share_url) or share_url)
    share_token_value = cast("str", agent.share_token)
    return {"share_url": share_url_value, "share_token": share_token_value}
