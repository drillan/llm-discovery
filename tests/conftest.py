"""Shared test fixtures for llm-discovery."""

from datetime import datetime, timezone
from pathlib import Path

import pytest

from llm_discovery.models import Model, ModelSource


@pytest.fixture
def sample_models() -> list[Model]:
    """Sample models for testing."""
    return [
        Model(
            model_id="gpt-4",
            model_name="GPT-4",
            provider_name="openai",
            source=ModelSource.API,
            fetched_at=datetime.now(timezone.utc),
        ),
        Model(
            model_id="gemini-1.5-pro",
            model_name="Gemini 1.5 Pro",
            provider_name="google",
            source=ModelSource.API,
            fetched_at=datetime.now(timezone.utc),
        ),
        Model(
            model_id="claude-3-opus",
            model_name="Claude 3 Opus",
            provider_name="anthropic",
            source=ModelSource.MANUAL,
            fetched_at=datetime.now(timezone.utc),
        ),
    ]


@pytest.fixture
def temp_cache_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Temporary cache directory for testing."""
    cache_dir = tmp_path / "llm-discovery"
    cache_dir.mkdir()
    monkeypatch.setenv("LLM_DISCOVERY_CACHE_DIR", str(cache_dir))
    return cache_dir
