"""Unit tests for DiscoveryService."""

from unittest.mock import patch

import pytest


class TestDiscoveryServiceAPIKeys:
    """Test API key detection and data source selection."""

    def test_has_api_keys_returns_true_when_openai_key_set(self):
        """Given OpenAI API key set, has_api_keys returns True."""
        from llm_discovery.models.config import Config
        from llm_discovery.services.discovery import DiscoveryService

        config = Config(
            openai_api_key="sk-test-key",
            google_api_key=None,
            google_genai_use_vertexai=False,
            google_application_credentials=None,
            llm_discovery_cache_dir="/tmp/test-cache",
            llm_discovery_retention_days=30,
        )

        service = DiscoveryService(config)
        assert service.has_api_keys() is True

    def test_has_api_keys_returns_true_when_google_key_set(self):
        """Given Google API key set, has_api_keys returns True."""
        from llm_discovery.models.config import Config
        from llm_discovery.services.discovery import DiscoveryService

        config = Config(
            openai_api_key=None,
            google_api_key="AIza-test-key",
            google_genai_use_vertexai=False,
            google_application_credentials=None,
            llm_discovery_cache_dir="/tmp/test-cache",
            llm_discovery_retention_days=30,
        )

        service = DiscoveryService(config)
        assert service.has_api_keys() is True

    def test_has_api_keys_returns_false_when_no_keys_set(self):
        """Given no API keys set, has_api_keys returns False."""
        from llm_discovery.models.config import Config
        from llm_discovery.services.discovery import DiscoveryService

        config = Config(
            openai_api_key=None,
            google_api_key=None,
            google_genai_use_vertexai=False,
            google_application_credentials=None,
            llm_discovery_cache_dir="/tmp/test-cache",
            llm_discovery_retention_days=30,
        )

        service = DiscoveryService(config)
        assert service.has_api_keys() is False

    @patch("llm_discovery.services.prebuilt_loader.PrebuiltDataLoader.is_available")
    @patch("llm_discovery.services.prebuilt_loader.PrebuiltDataLoader.load_models")
    def test_fetch_or_load_models_uses_prebuilt_when_no_keys(
        self, mock_load, mock_available
    ):
        """Given no API keys, fetch_or_load_models loads from prebuilt data."""
        from llm_discovery.models import Model, ModelSource
        from llm_discovery.models.config import Config
        from llm_discovery.services.discovery import DiscoveryService

        config = Config(
            openai_api_key=None,
            google_api_key=None,
            google_genai_use_vertexai=False,
            google_application_credentials=None,
            llm_discovery_cache_dir="/tmp/test-cache",
            llm_discovery_retention_days=30,
        )

        mock_available.return_value = True
        mock_load.return_value = [
            Model(
                model_id="test",
                model_name="Test",
                provider_name="test",
                source=ModelSource.API,
                fetched_at="2025-10-19T00:00:00Z",
                metadata={},
            )
        ]

        service = DiscoveryService(config)
        models = service.fetch_or_load_models()

        assert len(models) == 1
        mock_load.assert_called_once()

    @pytest.mark.asyncio
    @patch("llm_discovery.services.discovery.DiscoveryService.fetch_all_models")
    async def test_fetch_or_load_models_async_uses_api_when_keys_set(self, mock_fetch):
        """Given API keys set, fetch_or_load_models_async fetches from API."""
        from llm_discovery.models import FetchStatus, Model, ModelSource, ProviderSnapshot
        from llm_discovery.models.config import Config
        from llm_discovery.services.discovery import DiscoveryService

        config = Config(
            openai_api_key="sk-test",
            google_api_key=None,
            google_genai_use_vertexai=False,
            google_application_credentials=None,
            llm_discovery_cache_dir="/tmp/test-cache",
            llm_discovery_retention_days=30,
        )

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
        models = await service.fetch_or_load_models_async()

        assert len(models) == 1
        assert models[0].model_id == "gpt-4"
        mock_fetch.assert_called_once()
