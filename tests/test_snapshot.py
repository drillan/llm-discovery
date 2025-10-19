"""Tests for snapshot service."""

from datetime import UTC, datetime, timedelta

import pytest

from llm_discovery.exceptions import SnapshotNotFoundError
from llm_discovery.models import FetchStatus, Model, ModelSource, ProviderSnapshot
from llm_discovery.services.snapshot import SnapshotService


class TestSnapshotService:
    """Tests for SnapshotService class."""

    @pytest.fixture
    def snapshot_service(self, temp_cache_dir):
        """Create a SnapshotService instance with temporary directory."""
        # Use default retention of 30 days
        return SnapshotService(temp_cache_dir, retention_days=30)

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

    def test_save_snapshot(self, snapshot_service, sample_provider_snapshots):
        """Test saving a snapshot."""
        snapshot_id = snapshot_service.save_snapshot(sample_provider_snapshots)
        assert snapshot_id is not None

    def test_load_snapshot(self, snapshot_service, sample_provider_snapshots):
        """Test loading a snapshot."""
        snapshot_id = snapshot_service.save_snapshot(sample_provider_snapshots)
        snapshot = snapshot_service.load_snapshot(snapshot_id)

        assert snapshot.snapshot_id == snapshot_id
        assert len(snapshot.providers) == 1

    def test_snapshot_not_found(self, snapshot_service):
        """Test that SnapshotNotFoundError is raised for non-existent snapshot."""
        from uuid import uuid4

        fake_id = uuid4()
        with pytest.raises(SnapshotNotFoundError):
            snapshot_service.load_snapshot(fake_id)

    def test_list_snapshots(self, snapshot_service, sample_provider_snapshots):
        """Test listing snapshots."""
        # Save multiple snapshots
        id1 = snapshot_service.save_snapshot(sample_provider_snapshots)
        id2 = snapshot_service.save_snapshot(sample_provider_snapshots)

        snapshots = snapshot_service.list_snapshots()

        # Should be ordered by timestamp descending (newest first)
        assert len(snapshots) >= 2
        assert snapshots[0][0] == id2  # Newest first
        assert snapshots[1][0] == id1

    def test_cleanup_old_snapshots(self, snapshot_service, sample_provider_snapshots, temp_cache_dir):
        """Test cleaning up old snapshots."""
        # Create a snapshot service with 1-day retention
        short_retention_service = SnapshotService(temp_cache_dir, retention_days=1)

        # Save a snapshot
        snapshot_id = short_retention_service.save_snapshot(sample_provider_snapshots)

        # Manually modify the timestamp to make it old
        snapshot_file = temp_cache_dir / "snapshots" / f"{snapshot_id}.json"
        old_time = datetime.now(UTC) - timedelta(days=2)
        snapshot = short_retention_service.load_snapshot(snapshot_id)

        # Create a new snapshot with old timestamp
        import json

        from llm_discovery.models import Snapshot

        old_snapshot = Snapshot(
            snapshot_id=snapshot_id, timestamp=old_time, providers=snapshot.providers
        )
        snapshot_file.write_text(
            json.dumps(
                {
                    "snapshot_id": str(old_snapshot.snapshot_id),
                    "timestamp": old_snapshot.timestamp.isoformat(),
                    "providers": [
                        {
                            "provider_name": p.provider_name,
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
                            "fetch_status": p.fetch_status.value,
                            "fetched_at": p.fetched_at.isoformat(),
                            "error_message": p.error_message,
                        }
                        for p in old_snapshot.providers
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        # Cleanup should delete the old snapshot
        deleted_count = short_retention_service.cleanup_old_snapshots()
        assert deleted_count == 1
        assert not snapshot_file.exists()

    def test_snapshot_directory_created(self, snapshot_service, sample_provider_snapshots, temp_cache_dir):
        """Test that snapshots directory is created."""
        snapshot_service.save_snapshot(sample_provider_snapshots)

        snapshots_dir = temp_cache_dir / "snapshots"
        assert snapshots_dir.exists()
        assert snapshots_dir.is_dir()
