"""Shared test fixtures for llm-discovery."""

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest

from llm_discovery.models import (
    FetchStatus,
    Model,
    ModelSource,
    ProviderSnapshot,
    Snapshot,
)


@pytest.fixture
def sample_models() -> list[Model]:
    """Sample models for testing."""
    return [
        Model(
            model_id="gpt-4",
            model_name="GPT-4",
            provider_name="openai",
            source=ModelSource.API,
            fetched_at=datetime.now(UTC),
        ),
        Model(
            model_id="gemini-1.5-pro",
            model_name="Gemini 1.5 Pro",
            provider_name="google",
            source=ModelSource.API,
            fetched_at=datetime.now(UTC),
        ),
        Model(
            model_id="claude-3-opus",
            model_name="Claude 3 Opus",
            provider_name="anthropic",
            source=ModelSource.MANUAL,
            fetched_at=datetime.now(UTC),
        ),
    ]


@pytest.fixture
def sample_provider_snapshots(sample_models: list[Model]) -> list[ProviderSnapshot]:
    """Sample provider snapshots for testing."""
    fetched_at = datetime.now(UTC)
    return [
        ProviderSnapshot(
            provider_name="openai",
            models=[sample_models[0]],
            fetch_status=FetchStatus.SUCCESS,
            fetched_at=fetched_at,
            error_message=None,
        ),
        ProviderSnapshot(
            provider_name="google",
            models=[sample_models[1]],
            fetch_status=FetchStatus.SUCCESS,
            fetched_at=fetched_at,
            error_message=None,
        ),
        ProviderSnapshot(
            provider_name="anthropic",
            models=[sample_models[2]],
            fetch_status=FetchStatus.SUCCESS,
            fetched_at=fetched_at,
            error_message=None,
        ),
    ]


@pytest.fixture
def sample_snapshot(sample_provider_snapshots: list[ProviderSnapshot]) -> Snapshot:
    """Sample snapshot for testing."""
    return Snapshot(
        snapshot_id=uuid4(),
        timestamp=datetime.now(UTC),
        providers=sample_provider_snapshots,
    )


@pytest.fixture
def temp_cache_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Temporary cache directory for testing."""
    cache_dir = tmp_path / "llm-discovery"
    cache_dir.mkdir()
    monkeypatch.setenv("LLM_DISCOVERY_CACHE_DIR", str(cache_dir))
    return cache_dir
