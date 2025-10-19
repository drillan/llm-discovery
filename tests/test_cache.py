"""Tests for cache service."""

from datetime import UTC, datetime

import pytest

from llm_discovery.exceptions import CacheCorruptedError, CacheNotFoundError
from llm_discovery.models import FetchStatus, Model, ModelSource, ProviderSnapshot
from llm_discovery.services.cache import CacheService


class TestCacheService:
    """Tests for CacheService class."""

    @pytest.fixture
    def cache_service(self, temp_cache_dir):
        """Create a CacheService instance with temporary directory."""
        return CacheService(temp_cache_dir)

    @pytest.fixture
    def sample_provider_snapshots(self):
        """Create sample provider snapshots."""
        models = [
            Model(
                model_id="gpt-4",
                model_name="GPT-4",
                provider_name="openai",
                source=ModelSource.API,
                fetched_at=datetime.now(UTC),
            ),
        ]
        return [
            ProviderSnapshot(
                provider_name="openai",
                models=models,
                fetch_status=FetchStatus.SUCCESS,
                fetched_at=datetime.now(UTC),
                error_message=None,
            ),
        ]

    def test_cache_not_found_on_first_read(self, cache_service):
        """Test that CacheNotFoundError is raised when cache doesn't exist."""
        with pytest.raises(CacheNotFoundError):
            cache_service.get_cached_models()

    def test_save_and_load_cache(self, cache_service, sample_provider_snapshots):
        """Test saving and loading cache."""
        cache_service.save_cache(sample_provider_snapshots)

        models = cache_service.get_cached_models()
        assert len(models) == 1
        assert models[0].model_id == "gpt-4"

    def test_cache_file_created(self, cache_service, sample_provider_snapshots, temp_cache_dir):
        """Test that cache file is created."""
        cache_service.save_cache(sample_provider_snapshots)

        cache_file = temp_cache_dir / "models_cache.toml"
        assert cache_file.exists()

    def test_cache_update_preserves_created_at(
        self, cache_service, sample_provider_snapshots, temp_cache_dir
    ):
        """Test that updating cache preserves created_at timestamp."""
        import tomllib

        # Save initial cache
        cache_service.save_cache(sample_provider_snapshots)

        # Read metadata from TOML file directly
        cache_file = temp_cache_dir / "models_cache.toml"
        with open(cache_file, "rb") as f:
            initial_data = tomllib.load(f)
        initial_created_at = initial_data["metadata"]["created_at"]

        # Update cache (with a small delay to ensure different timestamp)
        import time

        time.sleep(0.01)
        cache_service.save_cache(sample_provider_snapshots)

        with open(cache_file, "rb") as f:
            updated_data = tomllib.load(f)

        assert updated_data["metadata"]["created_at"] == initial_created_at
        assert updated_data["metadata"]["last_updated"] > initial_data["metadata"]["last_updated"]

    def test_corrupted_cache_raises_error(self, cache_service, temp_cache_dir):
        """Test that corrupted cache raises CacheCorruptedError."""
        cache_file = temp_cache_dir / "models_cache.toml"
        cache_file.write_text("invalid toml content {{{", encoding="utf-8")

        with pytest.raises(CacheCorruptedError):
            cache_service.get_cached_models()

    def test_cache_metadata_version(self, cache_service, sample_provider_snapshots, temp_cache_dir):
        """Test that cache has correct version metadata."""
        import tomllib

        cache_service.save_cache(sample_provider_snapshots)

        # Read metadata from TOML file directly
        cache_file = temp_cache_dir / "models_cache.toml"
        with open(cache_file, "rb") as f:
            cache_data = tomllib.load(f)

        assert cache_data["metadata"]["version"] == "1.0.0"
