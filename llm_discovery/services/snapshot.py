"""Snapshot service for change tracking."""

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

from llm_discovery.exceptions import SnapshotNotFoundError
from llm_discovery.models import ProviderSnapshot, Snapshot


class SnapshotService:
    """Service for managing model snapshots."""

    def __init__(self, cache_dir: Path, retention_days: int = 30):
        """Initialize SnapshotService.

        Args:
            cache_dir: Cache directory path
            retention_days: Snapshot retention period in days
        """
        self.cache_dir = cache_dir
        self.snapshots_dir = cache_dir / "snapshots"
        self.retention_days = retention_days

        # Create snapshots directory
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)

    def save_snapshot(self, providers: list[ProviderSnapshot]) -> UUID:
        """Save snapshot to file.

        Args:
            providers: Provider snapshots

        Returns:
            Snapshot ID (UUID)
        """
        snapshot = Snapshot(providers=providers)

        # Convert to dict for JSON serialization
        snapshot_dict = {
            "snapshot_id": str(snapshot.snapshot_id),
            "timestamp": snapshot.timestamp.isoformat(),
            "providers": [
                {
                    "provider_name": p.provider_name,
                    "fetch_status": p.fetch_status.value,
                    "fetched_at": p.fetched_at.isoformat(),
                    "error_message": p.error_message,
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
                for p in snapshot.providers
            ],
        }

        # Save to file
        snapshot_file = self.snapshots_dir / f"{snapshot.snapshot_id}.json"
        snapshot_file.write_text(json.dumps(snapshot_dict, indent=2), encoding="utf-8")

        return snapshot.snapshot_id

    def load_snapshot(self, snapshot_id: UUID | str) -> Snapshot:
        """Load snapshot by ID.

        Args:
            snapshot_id: Snapshot UUID

        Returns:
            Snapshot object

        Raises:
            SnapshotNotFoundError: If snapshot not found
        """
        snapshot_id_str = str(snapshot_id)
        snapshot_file = self.snapshots_dir / f"{snapshot_id_str}.json"

        if not snapshot_file.exists():
            raise SnapshotNotFoundError(snapshot_id_str)

        # Load from JSON
        snapshot_dict = json.loads(snapshot_file.read_text(encoding="utf-8"))

        # Reconstruct Snapshot object
        from llm_discovery.models import FetchStatus, Model, ModelSource

        providers = []
        for provider_data in snapshot_dict["providers"]:
            models = []
            for model_data in provider_data["models"]:
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

            providers.append(
                ProviderSnapshot(
                    provider_name=provider_data["provider_name"],
                    models=models,
                    fetch_status=FetchStatus(provider_data["fetch_status"]),
                    fetched_at=datetime.fromisoformat(provider_data["fetched_at"]),
                    error_message=provider_data.get("error_message"),
                )
            )

        return Snapshot(
            snapshot_id=UUID(snapshot_dict["snapshot_id"]),
            timestamp=datetime.fromisoformat(snapshot_dict["timestamp"]),
            providers=providers,
        )

    def list_snapshots(self) -> list[tuple[UUID, datetime]]:
        """List all snapshots.

        Returns:
            List of (snapshot_id, timestamp) tuples
        """
        snapshots = []
        for snapshot_file in self.snapshots_dir.glob("*.json"):
            try:
                snapshot_dict = json.loads(snapshot_file.read_text(encoding="utf-8"))
                snapshots.append(
                    (
                        UUID(snapshot_dict["snapshot_id"]),
                        datetime.fromisoformat(snapshot_dict["timestamp"]),
                    )
                )
            except (json.JSONDecodeError, KeyError, ValueError):
                # Skip corrupted files
                continue

        # Sort by timestamp (newest first)
        snapshots.sort(key=lambda x: x[1], reverse=True)
        return snapshots

    def cleanup_old_snapshots(self) -> int:
        """Remove snapshots older than retention period.

        Returns:
            Number of snapshots deleted
        """
        cutoff_date = datetime.now(UTC) - timedelta(days=self.retention_days)
        deleted_count = 0

        for snapshot_id, timestamp in self.list_snapshots():
            if timestamp < cutoff_date:
                snapshot_file = self.snapshots_dir / f"{snapshot_id}.json"
                snapshot_file.unlink(missing_ok=True)
                deleted_count += 1

        return deleted_count
