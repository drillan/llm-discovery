"""Cache service for TOML persistence."""

import tomllib
from datetime import UTC, datetime
from pathlib import Path

import tomli_w

from llm_discovery.constants import TOML_CACHE_VERSION
from llm_discovery.exceptions import CacheCorruptedError, CacheNotFoundError
from llm_discovery.models import Cache, CacheMetadata, DataSourceInfo, Model, ProviderSnapshot


class CacheService:
    """Service for managing TOML cache."""

    def __init__(self, cache_dir: Path):
        """Initialize CacheService.

        Args:
            cache_dir: Cache directory path
        """
        self.cache_dir = cache_dir
        self.cache_file = cache_dir / "models_cache.toml"

    def save_cache(
        self,
        providers: list[ProviderSnapshot],
        data_source_type: str | None = None,
        data_source_timestamp: datetime | None = None,
    ) -> None:
        """Save cache to TOML file.

        Args:
            providers: List of provider snapshots to cache
            data_source_type: Data source type (api or prebuilt)
            data_source_timestamp: Data source timestamp

        Raises:
            IOError: If cache file cannot be written
        """
        # Create cache directory if it doesn't exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Create cache metadata
        now = datetime.now(UTC)

        # Preserve created_at if cache already exists
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "rb") as f:
                    existing_cache = tomllib.load(f)
                created_at = datetime.fromisoformat(
                    existing_cache["metadata"]["created_at"]
                )
            except (tomllib.TOMLDecodeError, KeyError, ValueError):
                # If we can't read the existing cache, use current time
                created_at = now
        else:
            created_at = now

        metadata = CacheMetadata(
            version=TOML_CACHE_VERSION,
            created_at=created_at,
            last_updated=now,
            data_source_type=data_source_type,
            data_source_timestamp=data_source_timestamp,
        )

        # Create cache object
        cache = Cache(metadata=metadata, providers=providers)

        # Convert to dict for TOML serialization
        metadata_dict = {
            "version": cache.metadata.version,
            "created_at": cache.metadata.created_at.isoformat(),
            "last_updated": cache.metadata.last_updated.isoformat(),
        }

        # Add optional data source fields
        if cache.metadata.data_source_type is not None:
            metadata_dict["data_source_type"] = cache.metadata.data_source_type
        if cache.metadata.data_source_timestamp is not None:
            metadata_dict["data_source_timestamp"] = (
                cache.metadata.data_source_timestamp.isoformat()
            )

        cache_dict = {
            "metadata": metadata_dict,
            "providers": [
                {
                    "provider_name": p.provider_name,
                    "fetch_status": p.fetch_status.value,
                    "fetched_at": p.fetched_at.isoformat(),
                    "error_message": p.error_message or "",
                    "models": [
                        {
                            "model_id": m.model_id,
                            "model_name": m.model_name,
                            "provider_name": m.provider_name,
                            "source": m.source.value,
                            "fetched_at": m.fetched_at.isoformat(),
                            "metadata": m.metadata,
                        }
                        for m in p.models
                    ],
                }
                for p in cache.providers
            ],
        }

        # Write to TOML file
        with open(self.cache_file, "wb") as f:
            tomli_w.dump(cache_dict, f)

    def load_cache(self) -> list[ProviderSnapshot]:
        """Load cache from TOML file.

        Returns:
            List of cached provider snapshots

        Raises:
            CacheNotFoundError: If cache file doesn't exist
            CacheCorruptedError: If cache file is corrupted
        """
        if not self.cache_file.exists():
            raise CacheNotFoundError(f"Cache file not found: {self.cache_file}")

        try:
            with open(self.cache_file, "rb") as f:
                cache_dict = tomllib.load(f)

            # Reconstruct ProviderSnapshot objects
            providers = []
            for provider_data in cache_dict.get("providers", []):
                models = []
                for model_data in provider_data.get("models", []):
                    from llm_discovery.models import ModelSource

                    models.append(
                        Model(
                            model_id=model_data["model_id"],
                            model_name=model_data["model_name"],
                            provider_name=model_data["provider_name"],
                            source=ModelSource(model_data["source"]),
                            fetched_at=datetime.fromisoformat(model_data["fetched_at"]),
                            metadata=model_data.get("metadata", {}),
                        )
                    )

                from llm_discovery.models import FetchStatus

                providers.append(
                    ProviderSnapshot(
                        provider_name=provider_data["provider_name"],
                        models=models,
                        fetch_status=FetchStatus(provider_data["fetch_status"]),
                        fetched_at=datetime.fromisoformat(provider_data["fetched_at"]),
                        error_message=provider_data.get("error_message"),
                    )
                )

            return providers

        except tomllib.TOMLDecodeError as e:
            raise CacheCorruptedError(
                cache_path=str(self.cache_file), parse_error=str(e)
            ) from e
        except (KeyError, ValueError, TypeError) as e:
            raise CacheCorruptedError(
                cache_path=str(self.cache_file),
                parse_error=f"Invalid cache structure: {str(e)}",
            ) from e

    def get_cached_models(self) -> list[Model]:
        """Get all cached models from all providers.

        Returns:
            List of all cached models

        Raises:
            CacheNotFoundError: If cache doesn't exist
            CacheCorruptedError: If cache is corrupted
        """
        providers = self.load_cache()
        models = []
        for provider in providers:
            models.extend(provider.models)
        return models

    def get_data_source_info(self) -> "DataSourceInfo | None":
        """Get data source information from cache metadata.

        Returns:
            DataSourceInfo object if available, None otherwise

        Raises:
            CacheNotFoundError: If cache doesn't exist
            CacheCorruptedError: If cache is corrupted
        """
        if not self.cache_file.exists():
            raise CacheNotFoundError(f"Cache file not found: {self.cache_file}")

        try:
            with open(self.cache_file, "rb") as f:
                cache_dict = tomllib.load(f)

            metadata = cache_dict.get("metadata", {})
            data_source_type = metadata.get("data_source_type")
            data_source_timestamp = metadata.get("data_source_timestamp")

            # Return None if data source info not available (backward compatibility)
            if data_source_type is None or data_source_timestamp is None:
                return None

            from llm_discovery.models import DataSourceInfo, DataSourceType

            return DataSourceInfo(
                source_type=DataSourceType(data_source_type),
                timestamp=datetime.fromisoformat(data_source_timestamp),
                provider_name="cache",
            )

        except tomllib.TOMLDecodeError as e:
            raise CacheCorruptedError(
                cache_path=str(self.cache_file), parse_error=str(e)
            ) from e
        except (KeyError, ValueError, TypeError) as e:
            raise CacheCorruptedError(
                cache_path=str(self.cache_file),
                parse_error=f"Invalid cache structure: {str(e)}",
            ) from e
