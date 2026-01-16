"""Dependency injection helpers for OpenAI routes."""

from typing import Annotated

from fastapi import Depends

from apps.api.protocols import ModelMapper, RequestTranslator, ResponseTranslator
from apps.api.services.openai.models import ModelMapper as ModelMapperImpl
from apps.api.services.openai.translator import (
    RequestTranslator as RequestTranslatorImpl,
    ResponseTranslator as ResponseTranslatorImpl,
)


def get_model_mapper() -> ModelMapper:
    """Get ModelMapper instance with configured model mappings.

    Returns:
        ModelMapper instance for OpenAI ↔ Claude model name translation
    """
    # Default mapping if not configured
    # TODO: Make this configurable via settings in the future
    mapping = {"gpt-4": "sonnet", "gpt-3.5-turbo": "haiku", "gpt-4o": "opus"}
    return ModelMapperImpl(mapping)


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
