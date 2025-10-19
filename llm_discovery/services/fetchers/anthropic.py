"""Anthropic model fetcher (manual data)."""

import tomllib
from datetime import UTC, datetime
from pathlib import Path

from llm_discovery.exceptions import ProviderFetchError
from llm_discovery.models import Model, ModelSource
from llm_discovery.services.fetchers.base import BaseFetcher


class AnthropicFetcher(BaseFetcher):
    """Fetcher for Anthropic models (manual data from TOML)."""

    @property
    def provider_name(self) -> str:
        """Provider name."""
        return "anthropic"

    async def fetch_models(self) -> list[Model]:
        """Load models from static TOML file.

        Returns:
            List of Model objects

        Raises:
            ProviderFetchError: If TOML file cannot be read
        """
        try:
            # Get path to anthropic_models.toml
            data_dir = Path(__file__).parent.parent.parent / "data"
            toml_path = data_dir / "anthropic_models.toml"

            if not toml_path.exists():
                raise ProviderFetchError(
                    provider_name=self.provider_name,
                    cause=f"Anthropic data file not found: {toml_path}",
                )

            # Load TOML data
            with open(toml_path, "rb") as f:
                data = tomllib.load(f)

            models = []
            fetched_at = datetime.now(UTC)

            for model_data in data.get("models", []):
                models.append(
                    Model(
                        model_id=model_data["name"],
                        model_name=model_data["display_name"],
                        provider_name=self.provider_name,
                        source=ModelSource.MANUAL,
                        fetched_at=fetched_at,
                        metadata={
                            "release_date": model_data.get("release_date"),
                            "description": model_data.get("description"),
                            "input_price_per_million": model_data.get(
                                "input_price_per_million"
                            ),
                            "output_price_per_million": model_data.get(
                                "output_price_per_million"
                            ),
                        },
                    )
                )

            return models

        except Exception as e:
            raise ProviderFetchError(
                provider_name=self.provider_name, cause=str(e)
            ) from e
