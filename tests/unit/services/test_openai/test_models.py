"""Unit tests for OpenAI model mapping service."""

import pytest

from apps.api.services.openai.models import ModelMapper


@pytest.fixture
def mapper() -> ModelMapper:
    """Fixture returning ModelMapper with test configuration."""
    return ModelMapper(
        {
            "gpt-4": "sonnet",
            "gpt-3.5-turbo": "haiku",
            "gpt-4o": "opus",
        }
    )


class TestModelMapper:
    """Test suite for ModelMapper."""

    def test_to_claude_maps_gpt4_to_sonnet(self, mapper: ModelMapper) -> None:
        """Assert mapper.to_claude('gpt-4') returns 'sonnet'."""
        assert mapper.to_claude("gpt-4") == "sonnet"

    def test_to_claude_raises_on_unknown_model(self, mapper: ModelMapper) -> None:
        """Assert to_claude raises ValueError for unknown model."""
        with pytest.raises(ValueError):
            mapper.to_claude("unknown-model")

    def test_to_openai_maps_sonnet_to_gpt4(self, mapper: ModelMapper) -> None:
        """Assert mapper.to_openai('sonnet') returns 'gpt-4'."""
        assert mapper.to_openai("sonnet") == "gpt-4"

    def test_to_openai_raises_on_unknown_model(self, mapper: ModelMapper) -> None:
        """Assert to_openai raises ValueError for unknown model."""
        with pytest.raises(ValueError):
            mapper.to_openai("unknown-claude-model")

    def test_list_models_returns_correct_count(self, mapper: ModelMapper) -> None:
        """Assert len(models) == 3 for default mapping."""
        models = mapper.list_models()
        assert len(models) == 3

    def test_list_models_has_correct_format(self, mapper: ModelMapper) -> None:
        """Assert each model has id, object, created, owned_by fields."""
        models = mapper.list_models()
        for model in models:
            assert "id" in model
            assert "object" in model
            assert "created" in model
            assert "owned_by" in model
            assert model["object"] == "model"

    def test_get_model_info_returns_model(self, mapper: ModelMapper) -> None:
        """Assert get_model_info returns OpenAI model info for valid model."""
        info = mapper.get_model_info("gpt-4")
        assert info["id"] == "gpt-4"
        assert info["object"] == "model"

    def test_get_model_info_raises_on_unknown(self, mapper: ModelMapper) -> None:
        """Assert get_model_info raises ValueError for unknown model."""
        with pytest.raises(ValueError):
            mapper.get_model_info("unknown-model")

    def test_init_raises_on_duplicate_claude_models(self) -> None:
        """Assert duplicate Claude model mappings raise ValueError."""
        with pytest.raises(ValueError):
            ModelMapper({"gpt-4": "sonnet", "gpt-4-turbo": "sonnet"})
