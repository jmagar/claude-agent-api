"""Session management endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends

from apps.api.dependencies import ApiKey
from apps.api.exceptions import SessionNotFoundError
from apps.api.schemas.requests import AnswerRequest
from apps.api.services.agent import AgentService

router = APIRouter(prefix="/sessions", tags=["Sessions"])


# Use the same service instance as query routes
_agent_service: AgentService | None = None


def get_agent_service() -> AgentService:
    """Get or create agent service instance."""
    global _agent_service
    if _agent_service is None:
        _agent_service = AgentService()
    return _agent_service


@router.post("/{session_id}/answer")
async def answer_question(
    session_id: str,
    answer: AnswerRequest,
    _api_key: ApiKey,
    agent_service: Annotated[AgentService, Depends(get_agent_service)],
) -> dict[str, str]:
    """Answer an AskUserQuestion from the agent.

    This endpoint is used to respond to questions posed by the agent
    during a streaming session via the AskUserQuestion tool.

    Args:
        session_id: Session ID that posed the question.
        answer: The user's answer to the question.
        _api_key: Validated API key (via dependency).
        agent_service: Agent service instance.

    Returns:
        Status response indicating the answer was received.

    Raises:
        SessionNotFoundError: If the session is not active or doesn't exist.
    """
    success = await agent_service.submit_answer(session_id, answer.answer)

    if not success:
        raise SessionNotFoundError(session_id)

    return {"status": "accepted", "session_id": session_id}
