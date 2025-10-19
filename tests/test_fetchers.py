"""Tests for model fetchers."""

import pytest

from llm_discovery.models import ModelSource
from llm_discovery.services.fetchers.anthropic import AnthropicFetcher


class TestAnthropicFetcher:
    """Tests for Anthropic fetcher (manual data)."""

    @pytest.fixture
    def fetcher(self):
        """Create an AnthropicFetcher instance."""
        return AnthropicFetcher()

    def test_provider_name(self, fetcher):
        """Test provider name."""
        assert fetcher.provider_name == "anthropic"

    @pytest.mark.asyncio
    async def test_fetch_models(self, fetcher):
        """Test fetching models from TOML data."""
        models = await fetcher.fetch_models()

        assert len(models) > 0
        assert all(m.provider_name == "anthropic" for m in models)
        assert all(m.source == ModelSource.MANUAL for m in models)

    @pytest.mark.asyncio
    async def test_fetch_models_includes_known_models(self, fetcher):
        """Test that known Anthropic models are included."""
        models = await fetcher.fetch_models()
        model_ids = [m.model_id for m in models]

        # Check for some known Claude models
        assert any("claude" in mid.lower() for mid in model_ids)
