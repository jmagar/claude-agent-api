"""Integration tests for OpenAI models endpoint."""

import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_list_models_returns_list(async_client: AsyncClient) -> None:
    """Test GET /v1/models returns a list response."""
    headers = {"Authorization": "Bearer test-api-key-12345"}
    response = await async_client.get("/v1/models", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert isinstance(data["data"], list)
    assert len(data["data"]) > 0


@pytest.mark.anyio
async def test_list_models_has_openai_format(async_client: AsyncClient) -> None:
    """Test GET /v1/models response has correct OpenAI structure."""
    headers = {"Authorization": "Bearer test-api-key-12345"}
    response = await async_client.get("/v1/models", headers=headers)

    assert response.status_code == 200
    data = response.json()

    # Check top-level structure
    assert data["object"] == "list"
    assert "data" in data

    # Check first model structure
    models = data["data"]
    assert len(models) > 0

    first_model = models[0]
    assert "id" in first_model
    assert "object" in first_model
    assert first_model["object"] == "model"
    assert "created" in first_model
    assert "owned_by" in first_model
    assert isinstance(first_model["created"], int)


@pytest.mark.anyio
async def test_get_model_by_id_returns_model(async_client: AsyncClient) -> None:
    """Test GET /v1/models/{model_id} returns specific model."""
    headers = {"Authorization": "Bearer test-api-key-12345"}

    # First get list to find a valid model ID
    list_response = await async_client.get("/v1/models", headers=headers)
    models = list_response.json()["data"]
    model_id = models[0]["id"]

    # Get specific model
    response = await async_client.get(f"/v1/models/{model_id}", headers=headers)

    assert response.status_code == 200
    model = response.json()

    # Check structure
    assert model["id"] == model_id
    assert model["object"] == "model"
    assert "created" in model
    assert "owned_by" in model


@pytest.mark.anyio
async def test_get_invalid_model_returns_404(async_client: AsyncClient) -> None:
    """Test GET /v1/models/invalid returns 404."""
    headers = {"Authorization": "Bearer test-api-key-12345"}
    response = await async_client.get("/v1/models/invalid-model-name", headers=headers)

    assert response.status_code == 404


@pytest.mark.anyio
async def test_404_has_openai_error_format(async_client: AsyncClient) -> None:
    """Test 404 error response has OpenAI error format."""
    headers = {"Authorization": "Bearer test-api-key-12345"}
    response = await async_client.get("/v1/models/invalid-model-name", headers=headers)

    assert response.status_code == 404
    error_data = response.json()

    # Check OpenAI error structure
    assert "error" in error_data
    error = error_data["error"]
    assert "message" in error
    assert "type" in error
    assert "code" in error
    assert error["type"] == "invalid_request_error"
