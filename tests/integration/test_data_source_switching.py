"""Integration tests for data source switching based on API keys."""

from unittest.mock import patch

import pytest


class TestDataSourceSwitching:
    """Test automatic switching between prebuilt data and API data."""

    @patch("llm_discovery.services.prebuilt_loader.PrebuiltDataLoader.is_available")
    @patch("llm_discovery.services.prebuilt_loader.PrebuiltDataLoader.load_models")
    def test_no_api_keys_uses_prebuilt_data(self, mock_load, mock_available):
        """Given no API keys configured, fetch_or_load_models uses prebuilt data."""
        from llm_discovery.models import Model, ModelSource
        from llm_discovery.models.config import Config
        from llm_discovery.services.discovery import DiscoveryService

        # Create config with no API keys
        config = Config(
            openai_api_key=None,
            google_api_key=None,
            google_genai_use_vertexai=False,
            google_application_credentials=None,
            llm_discovery_cache_dir="/tmp/test-cache",
            llm_discovery_retention_days=30,
        )

        # Mock prebuilt data availability
        mock_available.return_value = True
        mock_load.return_value = [
            Model(
                model_id="test-model",
                model_name="Test Model",
                provider_name="test",
                source=ModelSource.API,
                fetched_at="2025-10-19T00:00:00Z",
                metadata={},
            )
        ]

        service = DiscoveryService(config)

        # Should use prebuilt data
        models = service.fetch_or_load_models()

        assert len(models) == 1
        assert models[0].model_id == "test-model"
        mock_load.assert_called_once()

    @pytest.mark.asyncio
    @patch("llm_discovery.services.discovery.DiscoveryService.fetch_all_models")
    async def test_api_keys_set_uses_api_data(self, mock_fetch):
        """Given API keys configured, fetch_or_load_models fetches from API."""
        from llm_discovery.models import FetchStatus, Model, ModelSource, ProviderSnapshot
        from llm_discovery.models.config import Config
        from llm_discovery.services.discovery import DiscoveryService

        # Create config with API key
        config = Config(
            openai_api_key="sk-test-key",
            google_api_key=None,
            google_genai_use_vertexai=False,
            google_application_credentials=None,
            llm_discovery_cache_dir="/tmp/test-cache",
            llm_discovery_retention_days=30,
        )

        # Mock API fetch
        mock_fetch.return_value = [
            ProviderSnapshot(
                provider_name="openai",
                models=[
                    Model(
                        model_id="gpt-4",
                        model_name="GPT-4",
                        provider_name="openai",
                        source=ModelSource.API,
                        fetched_at="2025-10-19T00:00:00Z",
                        metadata={},
                    )
                ],
                fetch_status=FetchStatus.SUCCESS,
                fetched_at="2025-10-19T00:00:00Z",
                error_message=None,
            )
        ]

        service = DiscoveryService(config)

        # Should fetch from API
        models = await service.fetch_or_load_models_async()

        assert len(models) == 1
        assert models[0].model_id == "gpt-4"
        mock_fetch.assert_called_once()

    @pytest.mark.asyncio
    @patch("llm_discovery.services.discovery.DiscoveryService.fetch_all_models")
    @patch("llm_discovery.services.prebuilt_loader.PrebuiltDataLoader.is_available")
    @patch("llm_discovery.services.prebuilt_loader.PrebuiltDataLoader.load_models")
    async def test_invalid_api_key_falls_back_to_prebuilt(
        self, mock_load, mock_available, mock_fetch
    ):
        """Given invalid API key, fetch_or_load_models falls back to prebuilt data with error message."""
        from llm_discovery.exceptions import ProviderFetchError
        from llm_discovery.models import Model, ModelSource
        from llm_discovery.models.config import Config
        from llm_discovery.services.discovery import DiscoveryService

        # Create config with API key
        config = Config(
            openai_api_key="sk-invalid-key",
            google_api_key=None,
            google_genai_use_vertexai=False,
            google_application_credentials=None,
            llm_discovery_cache_dir="/tmp/test-cache",
            llm_discovery_retention_days=30,
        )

        # Mock API fetch failure
        mock_fetch.side_effect = ProviderFetchError(
            provider_name="openai", cause="Invalid API key"
        )

        # Mock prebuilt data availability
        mock_available.return_value = True
        mock_load.return_value = [
            Model(
                model_id="fallback-model",
                model_name="Fallback Model",
                provider_name="test",
                source=ModelSource.API,
                fetched_at="2025-10-19T00:00:00Z",
                metadata={},
            )
        ]

        service = DiscoveryService(config)

        # Should fall back to prebuilt data
        models = await service.fetch_or_load_models_async()

        assert len(models) == 1
        assert models[0].model_id == "fallback-model"
        mock_load.assert_called_once()
