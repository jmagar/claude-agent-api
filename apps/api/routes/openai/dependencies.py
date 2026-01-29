"""Dependency injection helpers for OpenAI routes."""

from typing import Annotated

from fastapi import Depends

from apps.api.protocols import ModelMapper, RequestTranslator, ResponseTranslator
from apps.api.services.openai.models import ModelMapper as ModelMapperImpl
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
    return ModelMapperImpl()


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
