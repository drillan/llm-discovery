"""Tests for Pydantic models."""

from datetime import UTC, datetime
from uuid import UUID

import pytest
from pydantic import ValidationError

from llm_discovery.models import (
    Cache,
    CacheMetadata,
    Change,
    ChangeType,
    FetchStatus,
    Model,
    ModelSource,
    Provider,
    ProviderSnapshot,
    ProviderType,
    Snapshot,
)


class TestModel:
    """Tests for Model class."""

    def test_valid_model_creation(self):
        """Test creating a valid model."""
        model = Model(
            model_id="gpt-4",
            model_name="GPT-4",
            provider_name="openai",
            source=ModelSource.API,
            fetched_at=datetime.now(UTC),
        )
        assert model.model_id == "gpt-4"
        assert model.model_name == "GPT-4"
        assert model.provider_name == "openai"
        assert model.source == ModelSource.API

    def test_model_strips_whitespace(self):
        """Test that string fields are stripped."""
        model = Model(
            model_id="  gpt-4  ",
            model_name="  GPT-4  ",
            provider_name="  openai  ",
            source=ModelSource.API,
            fetched_at=datetime.now(UTC),
        )
        assert model.model_id == "gpt-4"
        assert model.model_name == "GPT-4"
        assert model.provider_name == "openai"

    def test_model_empty_string_validation(self):
        """Test that empty strings are rejected."""
        with pytest.raises(ValidationError, match="Field cannot be empty"):
            Model(
                model_id="",
                model_name="GPT-4",
                provider_name="openai",
                source=ModelSource.API,
                fetched_at=datetime.now(UTC),
            )

    def test_model_utc_timezone_enforcement(self):
        """Test that datetime is converted to UTC."""
        naive_dt = datetime(2024, 1, 1, 12, 0, 0)
        model = Model(
            model_id="gpt-4",
            model_name="GPT-4",
            provider_name="openai",
            source=ModelSource.API,
            fetched_at=naive_dt,
        )
        assert model.fetched_at.tzinfo is not None
        assert model.fetched_at.tzinfo == UTC

    def test_model_immutability(self):
        """Test that models are frozen."""
        model = Model(
            model_id="gpt-4",
            model_name="GPT-4",
            provider_name="openai",
            source=ModelSource.API,
            fetched_at=datetime.now(UTC),
        )
        with pytest.raises(ValidationError):
            model.model_id = "gpt-3.5"  # type: ignore[misc]


class TestProviderSnapshot:
    """Tests for ProviderSnapshot class."""

    def test_valid_snapshot_creation(self, sample_models):
        """Test creating a valid provider snapshot."""
        snapshot = ProviderSnapshot(
            provider_name="openai",
            models=sample_models,
            fetch_status=FetchStatus.SUCCESS,
            fetched_at=datetime.now(UTC),
            error_message=None,
        )
        assert snapshot.provider_name == "openai"
        assert len(snapshot.models) == 3
        assert snapshot.fetch_status == FetchStatus.SUCCESS


class TestSnapshot:
    """Tests for Snapshot class."""

    def test_valid_snapshot_creation(self, sample_provider_snapshots):
        """Test creating a valid snapshot."""
        snapshot = Snapshot(providers=sample_provider_snapshots)
        assert len(snapshot.providers) == 3
        assert isinstance(snapshot.snapshot_id, UUID)

    def test_snapshot_empty_providers_validation(self):
        """Test that empty providers list is rejected."""
        with pytest.raises(
            ValidationError, match="Snapshot must contain at least one provider"
        ):
            Snapshot(providers=[])


class TestChange:
    """Tests for Change class."""

    def test_valid_change_creation(self):
        """Test creating a valid change."""
        prev_id = UUID("12345678-1234-5678-1234-567812345678")
        curr_id = UUID("87654321-4321-8765-4321-876543218765")

        change = Change(
            change_type=ChangeType.ADDED,
            model_id="gpt-4",
            model_name="GPT-4",
            provider_name="openai",
            previous_snapshot_id=prev_id,
            current_snapshot_id=curr_id,
        )
        assert change.change_type == ChangeType.ADDED
        assert change.model_id == "gpt-4"
        assert isinstance(change.change_id, UUID)


class TestCacheMetadata:
    """Tests for CacheMetadata class."""

    def test_valid_semantic_version(self):
        """Test valid semantic versioning."""
        metadata = CacheMetadata(
            version="1.0.0",
            created_at=datetime.now(UTC),
            last_updated=datetime.now(UTC),
        )
        assert metadata.version == "1.0.0"

    def test_invalid_semantic_version(self):
        """Test that invalid version format is rejected."""
        with pytest.raises(
            ValidationError, match="Version must be in semantic versioning format"
        ):
            CacheMetadata(
                version="1.0",
                created_at=datetime.now(UTC),
                last_updated=datetime.now(UTC),
            )

    def test_non_numeric_version_parts(self):
        """Test that non-numeric version parts are rejected."""
        with pytest.raises(ValidationError, match="Version parts must be numeric"):
            CacheMetadata(
                version="1.0.x",
                created_at=datetime.now(UTC),
                last_updated=datetime.now(UTC),
            )


class TestCache:
    """Tests for Cache class."""

    def test_valid_cache_creation(self, sample_provider_snapshots):
        """Test creating a valid cache."""
        metadata = CacheMetadata(
            version="1.0.0",
            created_at=datetime.now(UTC),
            last_updated=datetime.now(UTC),
        )
        cache = Cache(metadata=metadata, providers=sample_provider_snapshots)
        assert cache.metadata.version == "1.0.0"
        assert len(cache.providers) == 3

    def test_duplicate_provider_names_validation(self, sample_models):
        """Test that duplicate provider names are rejected."""
        metadata = CacheMetadata(
            version="1.0.0",
            created_at=datetime.now(UTC),
            last_updated=datetime.now(UTC),
        )
        duplicate_snapshots = [
            ProviderSnapshot(
                provider_name="openai",
                models=[sample_models[0]],
                fetch_status=FetchStatus.SUCCESS,
                fetched_at=datetime.now(UTC),
                error_message=None,
            ),
            ProviderSnapshot(
                provider_name="openai",
                models=[sample_models[1]],
                fetch_status=FetchStatus.SUCCESS,
                fetched_at=datetime.now(UTC),
                error_message=None,
            ),
        ]
        with pytest.raises(ValidationError, match="Duplicate provider names in cache"):
            Cache(metadata=metadata, providers=duplicate_snapshots)


class TestProvider:
    """Tests for Provider class."""

    def test_google_provider_requires_backend(self):
        """Test that Google provider requires google_backend."""
        with pytest.raises(
            ValidationError, match="Google provider must specify google_backend"
        ):
            Provider(
                name=ProviderType.GOOGLE,
                fetch_method=ModelSource.API,
                google_backend=None,
            )

    def test_non_google_provider_cannot_have_backend(self):
        """Test that non-Google providers cannot have google_backend."""
        from llm_discovery.models import GoogleBackend

        with pytest.raises(
            ValidationError, match="google_backend can only be set for Google provider"
        ):
            Provider(
                name=ProviderType.OPENAI,
                fetch_method=ModelSource.API,
                google_backend=GoogleBackend.AI_STUDIO,
            )
