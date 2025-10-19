"""OpenAI model fetcher."""

from datetime import datetime, timezone

from openai import AsyncOpenAI, OpenAIError

from llm_discovery.exceptions import AuthenticationError, ProviderFetchError
from llm_discovery.models import Model, ModelSource
from llm_discovery.services.fetchers.base import BaseFetcher


class OpenAIFetcher(BaseFetcher):
    """Fetcher for OpenAI models."""

    def __init__(self, api_key: str):
        """Initialize OpenAIFetcher.

        Args:
            api_key: OpenAI API key

        Raises:
            ValueError: If API key is not provided
        """
        if not api_key:
            raise ValueError("OpenAI API key is required")
        self.client = AsyncOpenAI(api_key=api_key)

    @property
    def provider_name(self) -> str:
        """Provider name."""
        return "openai"

    async def fetch_models(self) -> list[Model]:
        """Fetch models from OpenAI API.

        Returns:
            List of Model objects

        Raises:
            ProviderFetchError: If API call fails
            AuthenticationError: If authentication fails
        """
        try:
            response = await self.client.models.list()
            models = []
            fetched_at = datetime.now(timezone.utc)

            for model_data in response.data:
                models.append(
                    Model(
                        model_id=model_data.id,
                        model_name=model_data.id,  # OpenAI uses ID as name
                        provider_name=self.provider_name,
                        source=ModelSource.API,
                        fetched_at=fetched_at,
                        metadata={
                            "created": model_data.created,
                            "owned_by": model_data.owned_by,
                        },
                    )
                )

            return models

        except OpenAIError as e:
            error_msg = str(e)
            if "auth" in error_msg.lower() or "api" in error_msg.lower():
                raise AuthenticationError(
                    provider_name=self.provider_name,
                    details=f"Invalid API key or authentication failed: {error_msg}",
                ) from e
            raise ProviderFetchError(
                provider_name=self.provider_name, cause=error_msg
            ) from e
        except Exception as e:
            raise ProviderFetchError(
                provider_name=self.provider_name, cause=str(e)
            ) from e
