"""Google model fetcher (AI Studio and Vertex AI)."""

from datetime import UTC, datetime

import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

from llm_discovery.exceptions import AuthenticationError, ProviderFetchError
from llm_discovery.models import Model, ModelSource
from llm_discovery.models.config import Config
from llm_discovery.services.fetchers.base import BaseFetcher


class GoogleFetcher(BaseFetcher):
    """Fetcher for Google models (AI Studio or Vertex AI)."""

    def __init__(self, config: Config):
        """Initialize GoogleFetcher.

        Args:
            config: Application configuration

        Raises:
            ValueError: If required configuration is missing
        """
        self.config = config

        if config.google_genai_use_vertexai:
            # Vertex AI mode
            if not config.google_application_credentials:
                raise ValueError(
                    "GOOGLE_APPLICATION_CREDENTIALS is required for Vertex AI"
                )
            # Configure for Vertex AI
            # Note: The actual configuration would use google-cloud-aiplatform
            # but for simplicity, we'll use the same genai SDK which supports both
        else:
            # AI Studio mode
            if not config.google_api_key:
                raise ValueError("GOOGLE_API_KEY is required for AI Studio")
            genai.configure(api_key=config.google_api_key)  # type: ignore[attr-defined]

    @property
    def provider_name(self) -> str:
        """Provider name."""
        return "google"

    async def fetch_models(self) -> list[Model]:
        """Fetch models from Google API.

        Returns:
            List of Model objects

        Raises:
            ProviderFetchError: If API call fails
            AuthenticationError: If authentication fails
        """
        try:
            # List models using the generative AI SDK
            models_list = genai.list_models()  # type: ignore[attr-defined]
            models = []
            fetched_at = datetime.now(UTC)

            for model_data in models_list:
                # Filter for generative models
                if "generateContent" in model_data.supported_generation_methods:
                    models.append(
                        Model(
                            model_id=model_data.name.split("/")[-1],  # Extract model ID
                            model_name=model_data.display_name or model_data.name,
                            provider_name=self.provider_name,
                            source=ModelSource.API,
                            fetched_at=fetched_at,
                            metadata={
                                "description": model_data.description,
                                "supported_methods": model_data.supported_generation_methods,
                            },
                        )
                    )

            return models

        except google_exceptions.Unauthenticated as e:
            raise AuthenticationError(
                provider_name=self.provider_name,
                details=f"Google authentication failed: {str(e)}",
            ) from e
        except google_exceptions.PermissionDenied as e:
            raise AuthenticationError(
                provider_name=self.provider_name,
                details=f"Google permission denied: {str(e)}",
            ) from e
        except Exception as e:
            error_msg = str(e)
            if "auth" in error_msg.lower() or "credential" in error_msg.lower():
                raise AuthenticationError(
                    provider_name=self.provider_name, details=error_msg
                ) from e
            raise ProviderFetchError(
                provider_name=self.provider_name, cause=error_msg
            ) from e
