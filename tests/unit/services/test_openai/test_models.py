"""Unit tests for Claude model mapping service."""

import pytest

from apps.api.services.openai.models import CLAUDE_MODELS, ModelMapper


@pytest.fixture
def mapper() -> ModelMapper:
    """Fixture returning ModelMapper with default Claude models."""
    return ModelMapper()


@pytest.fixture
def custom_mapper() -> ModelMapper:
    """Fixture returning ModelMapper with custom test models."""
    return ModelMapper(
        {
            "claude-test-model-20250101": "test",
            "claude-another-model-20250102": "another",
        }
    )


class TestModelMapper:
    """Test suite for ModelMapper."""

    def test_to_claude_maps_full_name_to_alias(self, mapper: ModelMapper) -> None:
        """Assert mapper.to_claude with full name returns alias."""
        assert mapper.to_claude("claude-sonnet-4-5-20250929") == "sonnet"
        assert mapper.to_claude("claude-opus-4-5-20251101") == "opus"
        assert mapper.to_claude("claude-haiku-4-5-20251001") == "haiku"

    def test_to_claude_returns_alias_unchanged(self, mapper: ModelMapper) -> None:
        """Assert mapper.to_claude with alias returns same alias."""
        assert mapper.to_claude("sonnet") == "sonnet"
        assert mapper.to_claude("opus") == "opus"
        assert mapper.to_claude("haiku") == "haiku"

    def test_to_claude_raises_on_unknown_model(self, mapper: ModelMapper) -> None:
        """Assert to_claude raises ValueError for unknown model."""
        with pytest.raises(ValueError, match="Unknown model"):
            mapper.to_claude("unknown-model")
        with pytest.raises(ValueError, match="Unknown model"):
            mapper.to_claude("gpt-4")  # OpenAI names not supported

    def test_to_full_name_maps_alias_to_full_name(self, mapper: ModelMapper) -> None:
        """Assert mapper.to_full_name with alias returns full name."""
        assert mapper.to_full_name("sonnet") == "claude-sonnet-4-5-20250929"
        assert mapper.to_full_name("opus") == "claude-opus-4-5-20251101"
        assert mapper.to_full_name("haiku") == "claude-haiku-4-5-20251001"

    def test_to_full_name_returns_full_name_unchanged(self, mapper: ModelMapper) -> None:
        """Assert mapper.to_full_name with full name returns same name."""
        assert mapper.to_full_name("claude-sonnet-4-5-20250929") == "claude-sonnet-4-5-20250929"
        assert mapper.to_full_name("claude-opus-4-5-20251101") == "claude-opus-4-5-20251101"

    def test_to_full_name_raises_on_unknown_model(self, mapper: ModelMapper) -> None:
        """Assert to_full_name raises ValueError for unknown model."""
        with pytest.raises(ValueError, match="Unknown model"):
            mapper.to_full_name("unknown-model")

    def test_list_models_returns_correct_count(self, mapper: ModelMapper) -> None:
        """Assert len(models) matches default Claude models."""
        models = mapper.list_models()
        assert len(models) == len(CLAUDE_MODELS)
        assert len(models) == 3  # sonnet, opus, haiku

    def test_list_models_has_correct_format(self, mapper: ModelMapper) -> None:
        """Assert each model has id, object, created, owned_by fields."""
        models = mapper.list_models()
        for model in models:
            assert "id" in model
            assert "object" in model
            assert "created" in model
            assert "owned_by" in model
            assert model["object"] == "model"
            assert model["owned_by"] == "anthropic"

    def test_list_models_returns_full_names(self, mapper: ModelMapper) -> None:
        """Assert list_models returns full Claude model names."""
        models = mapper.list_models()
        model_ids = {m["id"] for m in models}
        assert "claude-sonnet-4-5-20250929" in model_ids
        assert "claude-opus-4-5-20251101" in model_ids
        assert "claude-haiku-4-5-20251001" in model_ids

    def test_get_model_info_returns_model_by_alias(self, mapper: ModelMapper) -> None:
        """Assert get_model_info accepts alias and returns full name."""
        info = mapper.get_model_info("sonnet")
        assert info["id"] == "claude-sonnet-4-5-20250929"
        assert info["object"] == "model"
        assert info["owned_by"] == "anthropic"

    def test_get_model_info_returns_model_by_full_name(self, mapper: ModelMapper) -> None:
        """Assert get_model_info accepts full name."""
        info = mapper.get_model_info("claude-opus-4-5-20251101")
        assert info["id"] == "claude-opus-4-5-20251101"
        assert info["object"] == "model"

    def test_get_model_info_raises_on_unknown(self, mapper: ModelMapper) -> None:
        """Assert get_model_info raises ValueError for unknown model."""
        with pytest.raises(ValueError, match="Unknown model"):
            mapper.get_model_info("unknown-model")

    def test_custom_model_mapping(self, custom_mapper: ModelMapper) -> None:
        """Assert custom model mapping works correctly."""
        assert custom_mapper.to_claude("claude-test-model-20250101") == "test"
        assert custom_mapper.to_claude("test") == "test"
        assert custom_mapper.to_full_name("test") == "claude-test-model-20250101"

    def test_custom_mapper_does_not_have_default_models(
        self, custom_mapper: ModelMapper
    ) -> None:
        """Assert custom mapper only has custom models."""
        with pytest.raises(ValueError, match="Unknown model"):
            custom_mapper.to_claude("sonnet")
        with pytest.raises(ValueError, match="Unknown model"):
            custom_mapper.to_full_name("sonnet")
