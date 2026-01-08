"""User interaction endpoints (answer questions from agent)."""

from fastapi import APIRouter

from apps.api.dependencies import AgentSvc, ApiKey
from apps.api.exceptions import SessionNotFoundError
from apps.api.schemas.requests import AnswerRequest

router = APIRouter(prefix="/sessions", tags=["Interactions"])


@router.post("/{session_id}/answer")
async def answer_question(
    session_id: str,
    answer: AnswerRequest,
    _api_key: ApiKey,
    agent_service: AgentSvc,
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
