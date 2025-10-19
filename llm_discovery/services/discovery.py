"""Discovery service for fetching models from multiple providers."""

import asyncio
from datetime import UTC, datetime

from llm_discovery.exceptions import PartialFetchError, ProviderFetchError
from llm_discovery.models import FetchStatus, Model, ProviderSnapshot
from llm_discovery.models.config import Config
from llm_discovery.services.cache import CacheService
from llm_discovery.services.change_detector import ChangeDetector
from llm_discovery.services.fetchers.anthropic import AnthropicFetcher
from llm_discovery.services.fetchers.google import GoogleFetcher
from llm_discovery.services.fetchers.openai import OpenAIFetcher
from llm_discovery.services.snapshot import SnapshotService


class DiscoveryService:
    """Service for discovering models from multiple providers."""

    def __init__(self, config: Config):
        """Initialize DiscoveryService.

        Args:
            config: Application configuration
        """
        self.config = config
        self.cache_service = CacheService(config.llm_discovery_cache_dir)
        self.snapshot_service = SnapshotService(
            config.llm_discovery_cache_dir, config.llm_discovery_retention_days
        )
        self.change_detector = ChangeDetector()

    async def fetch_all_models(self) -> list[ProviderSnapshot]:
        """Fetch models from all providers in parallel.

        Returns:
            List of provider snapshots

        Raises:
            PartialFetchError: If some providers fail (fail-fast)
            ProviderFetchError: If all providers fail
        """
        # Create fetcher tasks
        tasks = []
        provider_names = []

        # OpenAI
        if self.config.openai_api_key:
            tasks.append(self._fetch_from_provider(OpenAIFetcher(self.config.openai_api_key)))
            provider_names.append("openai")

        # Google
        if self.config.google_api_key or self.config.google_genai_use_vertexai:
            tasks.append(self._fetch_from_provider(GoogleFetcher(self.config)))
            provider_names.append("google")

        # Anthropic (always available - manual data)
        tasks.append(self._fetch_from_provider(AnthropicFetcher()))
        provider_names.append("anthropic")

        # Execute all fetches in parallel
        results: list[ProviderSnapshot | BaseException] = await asyncio.gather(
            *tasks, return_exceptions=True
        )

        # Process results
        snapshots: list[ProviderSnapshot] = []
        successful_providers = []
        failed_providers = []

        for provider_name, result in zip(provider_names, results, strict=False):
            if isinstance(result, BaseException):
                failed_providers.append(provider_name)
            else:
                snapshots.append(result)
                successful_providers.append(provider_name)

        # Fail-fast on partial failure
        if failed_providers:
            if successful_providers:
                raise PartialFetchError(
                    successful_providers=successful_providers,
                    failed_providers=failed_providers,
                )
            else:
                raise ProviderFetchError(
                    provider_name="all", cause="All providers failed"
                )

        return snapshots

    async def _fetch_from_provider(
        self, fetcher: AnthropicFetcher | GoogleFetcher | OpenAIFetcher
    ) -> ProviderSnapshot:
        """Fetch models from a single provider.

        Args:
            fetcher: Provider fetcher instance

        Returns:
            ProviderSnapshot with fetch results
        """
        try:
            models = await fetcher.fetch_models()
            return ProviderSnapshot(
                provider_name=fetcher.provider_name,
                models=models,
                fetch_status=FetchStatus.SUCCESS,
                fetched_at=datetime.now(UTC),
                error_message=None,
            )
        except Exception as e:
            # Re-raise to be caught by gather
            raise e

    def get_cached_models(self) -> list[Model]:
        """Get models from cache.

        Returns:
            List of cached models

        Raises:
            CacheNotFoundError: If cache doesn't exist
            CacheCorruptedError: If cache is corrupted
        """
        return self.cache_service.get_cached_models()

    def save_to_cache(self, providers: list[ProviderSnapshot]) -> None:
        """Save provider snapshots to cache.

        Args:
            providers: Provider snapshots to cache
        """
        self.cache_service.save_cache(providers)
