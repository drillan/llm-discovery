"""Prebuilt data loader service.

Loads model data from remote GitHub repository.
"""

import json
import urllib.error
import urllib.request
from datetime import UTC, datetime

from pydantic import ValidationError

from llm_discovery.exceptions import (
    PrebuiltDataCorruptedError,
    PrebuiltDataNotFoundError,
    PrebuiltDataValidationError,
)
from llm_discovery.models import (
    DataSourceInfo,
    DataSourceType,
    Model,
    PrebuiltDataMetadata,
    PrebuiltModelData,
)


class PrebuiltDataLoader:
    """Service to load prebuilt model data from remote URL."""

    # Remote URL for prebuilt data
    REMOTE_URL = "https://raw.githubusercontent.com/drillan/llm-discovery/main/data/prebuilt/models.json"

    def __init__(self) -> None:
        """Initialize PrebuiltDataLoader with remote URL."""
        self.remote_url = self.REMOTE_URL

    def is_available(self) -> bool:
        """Check if prebuilt data is accessible via remote URL.

        Returns:
            True if remote URL is accessible (HTTP 200), False otherwise.
        """
        try:
            req = urllib.request.Request(self.remote_url, method="HEAD")
            with urllib.request.urlopen(req, timeout=3) as response:
                status: int = response.status
                return status == 200
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError):
            return False

    def load_models(self) -> list[Model]:
        """Load models from prebuilt data file.

        Returns:
            List of Model objects loaded from prebuilt data.

        Raises:
            PrebuiltDataNotFoundError: If prebuilt data file does not exist.
            PrebuiltDataCorruptedError: If file is corrupted or invalid JSON.
            PrebuiltDataValidationError: If data does not match expected schema.
        """
        try:
            with urllib.request.urlopen(self.remote_url, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            raise PrebuiltDataNotFoundError(
                f"Prebuilt data not accessible (HTTP {e.code}). "
                "Please check network or set API keys."
            ) from e
        except urllib.error.URLError as e:
            raise PrebuiltDataCorruptedError(
                f"Network error: {e.reason}. Please check your connection.",
                original_error=e,
            ) from e
        except json.JSONDecodeError as e:
            raise PrebuiltDataCorruptedError(
                f"Prebuilt data is corrupted: {e}. Please report this issue.",
                original_error=e,
            ) from e

        # Validate with pydantic
        try:
            prebuilt_data = PrebuiltModelData(**data)
        except ValidationError as e:
            validation_errors = [str(err) for err in e.errors()]
            raise PrebuiltDataValidationError(
                "Prebuilt data validation failed",
                validation_errors=validation_errors,
            ) from e

        # Extract all models from provider snapshots
        models: list[Model] = []
        for provider_snapshot in prebuilt_data.providers:
            models.extend(provider_snapshot.models)

        return models

    def get_metadata(self) -> PrebuiltDataMetadata:
        """Get metadata about prebuilt data.

        Returns:
            Metadata object containing generation info.

        Raises:
            PrebuiltDataNotFoundError: If prebuilt data file does not exist.
            PrebuiltDataCorruptedError: If file is corrupted.
        """
        try:
            with urllib.request.urlopen(self.remote_url, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            raise PrebuiltDataNotFoundError(
                f"Prebuilt data not accessible (HTTP {e.code})."
            ) from e
        except urllib.error.URLError as e:
            raise PrebuiltDataCorruptedError(
                f"Network error: {e.reason}.",
                original_error=e,
            ) from e
        except json.JSONDecodeError as e:
            raise PrebuiltDataCorruptedError(
                f"Prebuilt data is corrupted: {e}.",
                original_error=e,
            ) from e

        # Validate and extract metadata
        try:
            prebuilt_data = PrebuiltModelData(**data)
        except ValidationError as e:
            raise PrebuiltDataCorruptedError(
                "Metadata validation failed",
                original_error=e,
            ) from e

        return prebuilt_data.metadata

    def get_age_hours(self) -> float:
        """Get age of prebuilt data in hours.

        Returns:
            Age in hours since data generation.

        Raises:
            PrebuiltDataNotFoundError: If prebuilt data file does not exist.
            PrebuiltDataCorruptedError: If HTTP error or JSON parse error occurs.
        """
        metadata = self.get_metadata()
        return (datetime.now(UTC) - metadata.generated_at).total_seconds() / 3600

    def get_data_source_info(self, provider_name: str) -> DataSourceInfo:
        """Get data source information for a provider.

        Args:
            provider_name: Provider name (e.g., "openai", "google", "anthropic")

        Returns:
            DataSourceInfo object for the provider.

        Raises:
            PrebuiltDataNotFoundError: If prebuilt data file does not exist.
            PrebuiltDataCorruptedError: If HTTP error or JSON parse error occurs.
            ValueError: If provider not found in prebuilt data.
        """
        try:
            with urllib.request.urlopen(self.remote_url, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            raise PrebuiltDataNotFoundError(
                f"Prebuilt data not accessible (HTTP {e.code})."
            ) from e
        except urllib.error.URLError as e:
            raise PrebuiltDataCorruptedError(
                f"Network error: {e.reason}.",
                original_error=e,
            ) from e
        except json.JSONDecodeError as e:
            raise PrebuiltDataCorruptedError(
                f"Prebuilt data is corrupted: {e}.",
                original_error=e,
            ) from e

        # Validate data
        try:
            prebuilt_data = PrebuiltModelData(**data)
        except ValidationError as e:
            raise PrebuiltDataCorruptedError(
                "Data validation failed",
                original_error=e,
            ) from e

        # Find provider snapshot
        for provider_snapshot in prebuilt_data.providers:
            if provider_snapshot.provider_name.lower() == provider_name.lower():
                return DataSourceInfo(
                    source_type=DataSourceType.PREBUILT,
                    timestamp=provider_snapshot.fetched_at,
                    provider_name=provider_name,
                )

        # Provider not found
        available_providers = [p.provider_name for p in prebuilt_data.providers]
        msg = f"Provider '{provider_name}' not found in prebuilt data. Available: {available_providers}"
        raise ValueError(msg)
