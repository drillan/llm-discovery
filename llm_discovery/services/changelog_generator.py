"""CHANGELOG generator for model changes."""

from datetime import datetime
from pathlib import Path

from llm_discovery.models import Change, ChangeType


class ChangelogGenerator:
    """Generator for CHANGELOG.md entries."""

    def __init__(self, changelog_path: Path):
        """Initialize ChangelogGenerator.

        Args:
            changelog_path: Path to CHANGELOG.md file
        """
        self.changelog_path = changelog_path

    def append_to_changelog(self, changes: list[Change], detected_at: datetime) -> None:
        """Append changes to CHANGELOG.md.

        Args:
            changes: List of changes to append
            detected_at: Detection timestamp
        """
        if not changes:
            return

        # Group changes by type
        added = [c for c in changes if c.change_type == ChangeType.ADDED]
        removed = [c for c in changes if c.change_type == ChangeType.REMOVED]

        # Create changelog entry
        lines = [
            f"\n## {detected_at.strftime('%Y-%m-%d %H:%M:%S UTC')}\n",
        ]

        if added:
            lines.append(f"\n### Added ({len(added)})\n\n")
            for change in added:
                lines.append(f"- **{change.provider_name}**: {change.model_name} (`{change.model_id}`)\n")

        if removed:
            lines.append(f"\n### Removed ({len(removed)})\n\n")
            for change in removed:
                lines.append(f"- **{change.provider_name}**: {change.model_name} (`{change.model_id}`)\n")

        # Append to file (or create if doesn't exist)
        if self.changelog_path.exists():
            content = self.changelog_path.read_text(encoding="utf-8")
        else:
            content = "# LLM Models CHANGELOG\n\nThis file tracks changes to available LLM models.\n"

        content += "".join(lines)
        self.changelog_path.write_text(content, encoding="utf-8")
