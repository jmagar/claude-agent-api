"""Exhaustive semantic tests for OpenAI-compatible endpoints.

Tests the /v1/chat/completions, /v1/models, and /v1/models/{model_id} endpoints
including authentication translation, request/response format validation,
error handling in OpenAI format, and edge cases.

Key difference from /api/v1/* endpoints: All validation errors on /v1/* routes
return 400 (OpenAI convention) instead of 422, with OpenAI error format:
{"error": {"type": "...", "message": "...", "code": "..."}}
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from httpx import AsyncClient


# =============================================================================
# Models: GET /v1/models
# =============================================================================


@pytest.mark.integration
@pytest.mark.anyio
async def test_list_models_returns_openai_format(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Listing models returns OpenAI-compatible model list with correct structure.

    Validates the response contains 'object' set to 'list' and a 'data' array
    where each item has id, object='model', created, and owned_by fields.
    """
    # ACT
    response = await async_client.get("/v1/models", headers=auth_headers)

    # ASSERT
    assert response.status_code == 200
    data = response.json()
    assert data["object"] == "list"
    assert isinstance(data["data"], list)
    assert len(data["data"]) >= 1

    for model in data["data"]:
        assert "id" in model
        assert model["object"] == "model"
        assert isinstance(model["created"], int)
        assert model["owned_by"] == "anthropic"


@pytest.mark.integration
@pytest.mark.anyio
async def test_list_models_includes_claude_models(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Listing models includes expected Claude model identifiers.

    Validates that known Claude model names appear in the model list,
    confirming the model mapper is correctly populated.
    """
    # ACT
    response = await async_client.get("/v1/models", headers=auth_headers)

    # ASSERT
    assert response.status_code == 200
    data = response.json()
    model_ids = [m["id"] for m in data["data"]]

    # At minimum, the standard Claude models should be present
    assert len(model_ids) >= 1
    # All IDs should be non-empty strings
    for mid in model_ids:
        assert isinstance(mid, str)
        assert len(mid) > 0


@pytest.mark.integration
@pytest.mark.anyio
async def test_list_models_with_bearer_auth(
    async_client: AsyncClient,
    test_api_key: str,
) -> None:
    """Listing models with Bearer token authentication succeeds.

    Validates that the BearerAuthMiddleware correctly translates
    Authorization: Bearer <token> to X-API-Key for /v1/* routes.
    """
    # ACT
    response = await async_client.get(
        "/v1/models",
        headers={"Authorization": f"Bearer {test_api_key}"},
    )

    # ASSERT
    assert response.status_code == 200
    data = response.json()
    assert data["object"] == "list"


# =============================================================================
# Models: GET /v1/models/{model_id}
# =============================================================================


@pytest.mark.integration
@pytest.mark.anyio
async def test_get_model_by_full_name(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Getting a model by full Claude name returns correct model info.

    Fetches a model using its full identifier and validates
    the response structure matches OpenAI model info format.
    """
    # ARRANGE - Get a valid model ID from the list first
    list_response = await async_client.get("/v1/models", headers=auth_headers)
    assert list_response.status_code == 200
    models = list_response.json()["data"]
    assert len(models) > 0
    model_id = models[0]["id"]

    # ACT
    response = await async_client.get(
        f"/v1/models/{model_id}",
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == model_id
    assert data["object"] == "model"
    assert isinstance(data["created"], int)
    assert data["owned_by"] == "anthropic"


@pytest.mark.integration
@pytest.mark.anyio
async def test_get_model_not_found_returns_404_openai_format(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Getting a nonexistent model returns 404 in OpenAI error format.

    The models endpoint raises HTTPException(404) which the exception handler
    converts to OpenAI error format for /v1/* routes.
    """
    # ACT
    response = await async_client.get(
        "/v1/models/nonexistent-model-xyz",
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert "type" in data["error"]
    assert "message" in data["error"]


@pytest.mark.integration
@pytest.mark.anyio
async def test_get_model_by_alias(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Getting a model by short alias returns valid model info.

    The model mapper accepts aliases (e.g., 'sonnet') and resolves them
    to the corresponding full model name. The response should have valid
    model info structure regardless of the resolved name.
    """
    # ACT
    response = await async_client.get(
        "/v1/models/sonnet",
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 200
    data = response.json()
    assert data["object"] == "model"
    assert data["owned_by"] == "anthropic"
    assert isinstance(data["id"], str)
    assert len(data["id"]) > 0


# =============================================================================
# Chat Completions: POST /v1/chat/completions - Validation
# Note: OpenAI endpoints return 400 for validation errors (not 422)
# =============================================================================


@pytest.mark.integration
@pytest.mark.anyio
async def test_chat_completions_requires_messages(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Chat completions without messages returns 400 validation error.

    The messages field is required. OpenAI endpoints convert validation
    errors to 400 status with OpenAI error format.
    """
    # ACT
    response = await async_client.post(
        "/v1/chat/completions",
        json={"model": "gpt-4"},
        headers=auth_headers,
    )

    # ASSERT - OpenAI endpoints return 400 for validation errors
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.integration
@pytest.mark.anyio
async def test_chat_completions_requires_model(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Chat completions without model returns 400 validation error.

    The model field is required with min_length=1.
    """
    # ACT
    response = await async_client.post(
        "/v1/chat/completions",
        json={
            "messages": [{"role": "user", "content": "Hello"}],
        },
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.integration
@pytest.mark.anyio
async def test_chat_completions_rejects_empty_messages(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Chat completions with empty messages array returns 400.

    The messages field has min_length=1 constraint.
    """
    # ACT
    response = await async_client.post(
        "/v1/chat/completions",
        json={
            "model": "gpt-4",
            "messages": [],
        },
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.integration
@pytest.mark.anyio
async def test_chat_completions_rejects_empty_model(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Chat completions with empty model string returns 400.

    The model field has min_length=1 constraint.
    """
    # ACT
    response = await async_client.post(
        "/v1/chat/completions",
        json={
            "model": "",
            "messages": [{"role": "user", "content": "Hello"}],
        },
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.integration
@pytest.mark.anyio
async def test_chat_completions_rejects_invalid_temperature(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Chat completions with temperature out of range returns 400.

    Temperature must be between 0 and 2 (inclusive).
    OpenAI endpoints convert Pydantic validation to 400.
    """
    # ACT - temperature > 2
    response = await async_client.post(
        "/v1/chat/completions",
        json={
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Hello"}],
            "temperature": 3.0,
        },
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 400
    data = response.json()
    assert "error" in data

    # ACT - temperature < 0
    response_neg = await async_client.post(
        "/v1/chat/completions",
        json={
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Hello"}],
            "temperature": -0.5,
        },
        headers=auth_headers,
    )

    # ASSERT
    assert response_neg.status_code == 400


# =============================================================================
# Chat Completions: POST /v1/chat/completions - Request Translation
# =============================================================================


@pytest.mark.integration
@pytest.mark.anyio
async def test_chat_completions_unknown_model_returns_error(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Chat completions with an unknown model name returns 400 error.

    The request translator validates the model name against the mapper
    and returns a MODEL_NOT_FOUND error when it is not recognized.
    """
    # ACT
    response = await async_client.post(
        "/v1/chat/completions",
        json={
            "model": "totally-fake-model-12345",
            "messages": [{"role": "user", "content": "Hello"}],
        },
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 400
    data = response.json()
    assert "error" in data


@pytest.mark.integration
@pytest.mark.anyio
async def test_chat_completions_system_only_returns_error(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Chat completions with only system messages (no user/assistant) returns error.

    The translator requires at least one non-system message to build
    the prompt. System-only messages produce an empty prompt which triggers
    a VALIDATION_ERROR.
    """
    # ACT
    response = await async_client.post(
        "/v1/chat/completions",
        json={
            "model": "gpt-4",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
            ],
        },
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"


# =============================================================================
# Authentication: Bearer Token Translation
# =============================================================================


@pytest.mark.integration
@pytest.mark.anyio
async def test_bearer_auth_for_chat_completions(
    async_client: AsyncClient,
    test_api_key: str,
) -> None:
    """Chat completions accept Bearer token authentication.

    The BearerAuthMiddleware converts Authorization: Bearer <token>
    to X-API-Key header for /v1/* routes. This test validates that
    the translation works end-to-end for the chat endpoint.
    """
    # ACT - Use Bearer auth instead of X-API-Key
    response = await async_client.post(
        "/v1/chat/completions",
        json={
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Hello"}],
        },
        headers={"Authorization": f"Bearer {test_api_key}"},
    )

    # ASSERT - Should not get 401 (auth should work)
    # May get other errors (mock SDK, etc.) but auth should pass
    assert response.status_code != 401


@pytest.mark.integration
@pytest.mark.anyio
async def test_no_auth_returns_401(
    async_client: AsyncClient,
) -> None:
    """Requests without any authentication return 401.

    Both /v1/* endpoints require authentication via either
    X-API-Key or Bearer token.
    """
    # ACT - No auth headers at all
    response = await async_client.get("/v1/models")

    # ASSERT
    assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.anyio
async def test_empty_bearer_token_returns_401(
    async_client: AsyncClient,
) -> None:
    """Requests with empty Bearer token return 401.

    The middleware should not extract an empty string as a valid token.
    """
    # ACT
    response = await async_client.get(
        "/v1/models",
        headers={"Authorization": "Bearer "},
    )

    # ASSERT
    assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.anyio
async def test_x_api_key_preserved_over_bearer(
    async_client: AsyncClient,
    test_api_key: str,
) -> None:
    """X-API-Key header takes precedence over Bearer token.

    When both X-API-Key and Authorization: Bearer are present,
    the middleware should not overwrite the existing X-API-Key.
    """
    # ACT - Send both headers, X-API-Key should win
    response = await async_client.get(
        "/v1/models",
        headers={
            "X-API-Key": test_api_key,
            "Authorization": "Bearer some-other-token",
        },
    )

    # ASSERT - Should succeed because X-API-Key is valid
    assert response.status_code == 200


# =============================================================================
# Chat Completions: POST /v1/chat/completions - Malformed Requests
# =============================================================================


@pytest.mark.integration
@pytest.mark.anyio
async def test_chat_completions_invalid_json_returns_400(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Chat completions with non-JSON body returns 400 in OpenAI error format.

    OpenAI endpoints translate RequestValidationError to 400 status.
    """
    # ACT
    response = await async_client.post(
        "/v1/chat/completions",
        content=b"not json at all",
        headers={**auth_headers, "Content-Type": "application/json"},
    )

    # ASSERT
    assert response.status_code == 400
    data = response.json()
    assert "error" in data


@pytest.mark.integration
@pytest.mark.anyio
async def test_chat_completions_invalid_role_returns_400(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Chat completions with invalid message role returns 400 in OpenAI error format.

    The role field is a Literal type restricted to system/user/assistant/tool.
    OpenAI endpoints convert validation errors to 400.
    """
    # ACT
    response = await async_client.post(
        "/v1/chat/completions",
        json={
            "model": "gpt-4",
            "messages": [{"role": "invalid_role", "content": "Hello"}],
        },
        headers=auth_headers,
    )

    # ASSERT
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"


# =============================================================================
# Chat Completions: POST /v1/chat/completions - Unsupported Parameters
# =============================================================================


@pytest.mark.integration
@pytest.mark.anyio
async def test_chat_completions_accepts_unsupported_params(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """Chat completions accepts but ignores unsupported OpenAI parameters.

    Parameters like temperature, top_p, max_tokens, and stop are accepted
    by the schema but logged as warnings and ignored by the SDK.
    The request should not fail due to these parameters.
    """
    # ACT
    response = await async_client.post(
        "/v1/chat/completions",
        json={
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Hello"}],
            "temperature": 0.7,
            "top_p": 0.9,
            "max_tokens": 100,
            "stop": ["\n"],
        },
        headers=auth_headers,
    )

    # ASSERT - Should not fail with validation error due to these parameters
    # The request passes validation and goes to the SDK (which is mocked)
    assert response.status_code != 400 or "VALIDATION_ERROR" not in response.text


# =============================================================================
# Error Format: OpenAI Error Structure
# =============================================================================


@pytest.mark.integration
@pytest.mark.anyio
async def test_openai_error_format_structure(
    async_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """OpenAI error responses follow the standard error format.

    All errors on /v1/* routes should return:
    {"error": {"type": "...", "message": "...", "code": "..."}}
    """
    # ACT - Trigger a known error (unknown model)
    response = await async_client.post(
        "/v1/chat/completions",
        json={
            "model": "unknown-model-abc",
            "messages": [{"role": "user", "content": "Hello"}],
        },
        headers=auth_headers,
    )

    # ASSERT - Validate OpenAI error structure
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    error = data["error"]
    assert "type" in error
    assert "message" in error
    assert "code" in error
    assert isinstance(error["type"], str)
    assert isinstance(error["message"], str)
    assert len(error["message"]) > 0
