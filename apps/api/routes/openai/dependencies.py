"""Dependency injection helpers for OpenAI routes."""

from typing import Annotated

from fastapi import Depends

from apps.api.protocols import ModelMapper, RequestTranslator, ResponseTranslator
from apps.api.services.assistants import (
    AssistantService,
    MessageService,
    RunService,
    ThreadService,
)
from apps.api.services.openai.models import (
    CLAUDE_MODELS,
)
from apps.api.services.openai.models import (
    ModelMapper as ModelMapperImpl,
)
from apps.api.services.openai.translator import (
    RequestTranslator as RequestTranslatorImpl,
)
from apps.api.services.openai.translator import (
    ResponseTranslator as ResponseTranslatorImpl,
)


def get_model_mapper() -> ModelMapper:
    """Get ModelMapper instance with Claude models.

    Returns:
        ModelMapper instance for Claude model name handling
    """
    # Include OpenAI-compatible aliases for chat completion requests.
    openai_models = {**CLAUDE_MODELS, "gpt-4": "sonnet"}
    return ModelMapperImpl(openai_models)


def get_request_translator(
    model_mapper: Annotated[ModelMapper, Depends(get_model_mapper)],
) -> RequestTranslator:
    """Get RequestTranslator instance.

    Args:
        model_mapper: ModelMapper for model name translation

    Returns:
        RequestTranslator for OpenAI → Claude request translation
    """
    return RequestTranslatorImpl(model_mapper)


def get_response_translator() -> ResponseTranslator:
    """Get ResponseTranslator instance.

    Returns:
        ResponseTranslator for Claude → OpenAI response translation
    """
    return ResponseTranslatorImpl()


def get_assistant_service() -> AssistantService:
    """Get AssistantService instance.

    Returns:
        AssistantService for assistant CRUD operations.
    """
    return AssistantService()


def get_thread_service() -> ThreadService:
    """Get ThreadService instance.

    Returns:
        ThreadService for thread CRUD operations.
    """
    return ThreadService()


def get_message_service() -> MessageService:
    """Get MessageService instance.

    Returns:
        MessageService for message CRUD operations.
    """
    return MessageService()


def get_run_service() -> RunService:
    """Get RunService instance.

    Returns:
        RunService for run CRUD operations.
    """
    return RunService()


# Type aliases for dependency injection
ModelMapperDep = Annotated[ModelMapper, Depends(get_model_mapper)]
RequestTranslatorDep = Annotated[RequestTranslator, Depends(get_request_translator)]
ResponseTranslatorDep = Annotated[ResponseTranslator, Depends(get_response_translator)]
AssistantSvcDep = Annotated[AssistantService, Depends(get_assistant_service)]
ThreadSvcDep = Annotated[ThreadService, Depends(get_thread_service)]
MessageSvcDep = Annotated[MessageService, Depends(get_message_service)]
RunSvcDep = Annotated[RunService, Depends(get_run_service)]
