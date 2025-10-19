"""Change detection service."""

from datetime import datetime, timezone
from uuid import UUID

from llm_discovery.models import Change, ChangeType, Snapshot


class ChangeDetector:
    """Service for detecting model changes between snapshots."""

    def detect_changes(
        self, previous: Snapshot, current: Snapshot
    ) -> list[Change]:
        """Detect changes between two snapshots.

        Args:
            previous: Previous snapshot
            current: Current snapshot

        Returns:
            List of Change objects
        """
        changes = []

        # Create model ID sets for comparison
        previous_models = self._get_model_dict(previous)
        current_models = self._get_model_dict(current)

        # Detect added models
        for model_id, model_info in current_models.items():
            if model_id not in previous_models:
                changes.append(
                    Change(
                        change_type=ChangeType.ADDED,
                        model_id=model_id,
                        model_name=model_info["name"],
                        provider_name=model_info["provider"],
                        previous_snapshot_id=previous.snapshot_id,
                        current_snapshot_id=current.snapshot_id,
                    )
                )

        # Detect removed models
        for model_id, model_info in previous_models.items():
            if model_id not in current_models:
                changes.append(
                    Change(
                        change_type=ChangeType.REMOVED,
                        model_id=model_id,
                        model_name=model_info["name"],
                        provider_name=model_info["provider"],
                        previous_snapshot_id=previous.snapshot_id,
                        current_snapshot_id=current.snapshot_id,
                    )
                )

        return changes

    def _get_model_dict(self, snapshot: Snapshot) -> dict[str, dict[str, str]]:
        """Extract model dictionary from snapshot.

        Args:
            snapshot: Snapshot object

        Returns:
            Dict mapping model_id to {name, provider}
        """
        models = {}
        for provider in snapshot.providers:
            for model in provider.models:
                # Use provider + model_id as unique key
                key = f"{model.provider_name}/{model.model_id}"
                models[key] = {
                    "name": model.model_name,
                    "provider": model.provider_name,
                }
        return models
