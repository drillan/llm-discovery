"""Tests for change detection service."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from llm_discovery.models import (
    ChangeType,
    FetchStatus,
    Model,
    ModelSource,
    ProviderSnapshot,
    Snapshot,
)
from llm_discovery.services.change_detector import ChangeDetector


class TestChangeDetector:
    """Tests for ChangeDetector class."""

    @pytest.fixture
    def detector(self):
        """Create a ChangeDetector instance."""
        return ChangeDetector()

    @pytest.fixture
    def previous_snapshot(self):
        """Create a previous snapshot."""
        models = [
            Model(
                model_id="gpt-4",
                model_name="GPT-4",
                provider_name="openai",
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
        providers = [
            ProviderSnapshot(
                provider_name="openai",
                models=[models[0]],
                fetch_status=FetchStatus.SUCCESS,
                fetched_at=datetime.now(UTC),
                error_message=None,
            ),
            ProviderSnapshot(
                provider_name="anthropic",
                models=[models[1]],
                fetch_status=FetchStatus.SUCCESS,
                fetched_at=datetime.now(UTC),
                error_message=None,
            ),
        ]
        return Snapshot(snapshot_id=uuid4(), providers=providers)

    @pytest.fixture
    def current_snapshot(self):
        """Create a current snapshot with changes."""
        models = [
            Model(
                model_id="gpt-4",
                model_name="GPT-4",
                provider_name="openai",
                source=ModelSource.API,
                fetched_at=datetime.now(UTC),
            ),
            Model(
                model_id="gpt-4-turbo",
                model_name="GPT-4 Turbo",
                provider_name="openai",
                source=ModelSource.API,
                fetched_at=datetime.now(UTC),
            ),
        ]
        providers = [
            ProviderSnapshot(
                provider_name="openai",
                models=models,
                fetch_status=FetchStatus.SUCCESS,
                fetched_at=datetime.now(UTC),
                error_message=None,
            ),
        ]
        return Snapshot(snapshot_id=uuid4(), providers=providers)

    def test_detect_added_models(self, detector, previous_snapshot, current_snapshot):
        """Test detecting added models."""
        changes = detector.detect_changes(previous_snapshot, current_snapshot)

        added_changes = [c for c in changes if c.change_type == ChangeType.ADDED]
        assert len(added_changes) == 1
        assert added_changes[0].model_id == "openai/gpt-4-turbo"

    def test_detect_removed_models(self, detector, previous_snapshot, current_snapshot):
        """Test detecting removed models."""
        changes = detector.detect_changes(previous_snapshot, current_snapshot)

        removed_changes = [c for c in changes if c.change_type == ChangeType.REMOVED]
        assert len(removed_changes) == 1
        assert removed_changes[0].model_id == "anthropic/claude-3-opus"

    def test_no_changes_detected(self, detector, previous_snapshot):
        """Test when there are no changes."""
        # Create identical current snapshot
        current_snapshot = Snapshot(
            snapshot_id=uuid4(), providers=previous_snapshot.providers
        )

        changes = detector.detect_changes(previous_snapshot, current_snapshot)
        assert len(changes) == 0

    def test_change_snapshot_ids(self, detector, previous_snapshot, current_snapshot):
        """Test that changes contain correct snapshot IDs."""
        changes = detector.detect_changes(previous_snapshot, current_snapshot)

        for change in changes:
            assert change.previous_snapshot_id == previous_snapshot.snapshot_id
            assert change.current_snapshot_id == current_snapshot.snapshot_id
