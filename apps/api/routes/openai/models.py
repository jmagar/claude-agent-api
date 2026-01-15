"""OpenAI-compatible models endpoint."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from apps.api.routes.openai.dependencies import get_model_mapper
from apps.api.schemas.openai.responses import OpenAIModelInfo, OpenAIModelList
from apps.api.services.openai.models import ModelMapper

router = APIRouter()


@router.get("/models", response_model=None)
async def list_models(
    model_mapper: Annotated[ModelMapper, Depends(get_model_mapper)]
) -> OpenAIModelList:
    """List all available OpenAI-compatible models.

    Returns:
        OpenAI-formatted list of available models with metadata
    """
    models = model_mapper.list_models()
    return OpenAIModelList(
        object="list",
        data=models,
    )


@router.get("/models/{model_id}", response_model=None)
async def get_model(
    model_id: str,
    model_mapper: Annotated[ModelMapper, Depends(get_model_mapper)]
) -> OpenAIModelInfo:
    """Get information about a specific model.

    Args:
        model_id: The OpenAI model ID (e.g., "gpt-4", "gpt-3.5-turbo")
        model_mapper: Model mapper service for validation

    Returns:
        OpenAI-formatted model information

    Raises:
        HTTPException: 404 if model ID is not recognized
    """
    # Validate model exists by attempting to translate
    try:
        model_mapper.to_claude(model_id)
    except ValueError as exc:
        # Raise HTTPException with 404 - will be caught by exception handler
        # and converted to OpenAI error format
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    # If valid, return model info
    models = model_mapper.list_models()
    for model in models:
        if model["id"] == model_id:
            return model

    # Should never reach here if model_mapper is consistent
    raise HTTPException(
        status_code=404,
        detail=f"Model {model_id} not found",
    )
