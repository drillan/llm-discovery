"""Base provider fetcher."""

from abc import ABC, abstractmethod

from llm_discovery.models import Model


class BaseFetcher(ABC):
    """Base class for model fetchers."""

    @abstractmethod
    async def fetch_models(self) -> list[Model]:
        """Fetch models from provider.

        Returns:
            List of Model objects

        Raises:
            ProviderFetchError: If fetching fails
            AuthenticationError: If authentication fails
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Provider name."""
        pass
