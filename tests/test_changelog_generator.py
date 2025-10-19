"""Tests for changelog generator."""

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest

from llm_discovery.models import Change, ChangeType
from llm_discovery.services.changelog_generator import ChangelogGenerator


class TestChangelogGenerator:
    """Tests for ChangelogGenerator class."""

    @pytest.fixture
    def changelog_file(self, tmp_path):
        """Create a temporary changelog file path."""
        return tmp_path / "CHANGELOG.md"

    @pytest.fixture
    def sample_changes(self):
        """Create sample changes."""
        prev_id = uuid4()
        curr_id = uuid4()

        return [
            Change(
                change_type=ChangeType.ADDED,
                model_id="gpt-4-turbo",
                model_name="GPT-4 Turbo",
                provider_name="openai",
                previous_snapshot_id=prev_id,
                current_snapshot_id=curr_id,
            ),
            Change(
                change_type=ChangeType.REMOVED,
                model_id="gpt-3.5",
                model_name="GPT-3.5",
                provider_name="openai",
                previous_snapshot_id=prev_id,
                current_snapshot_id=curr_id,
            ),
        ]

    def test_append_to_new_changelog(self, changelog_file, sample_changes):
        """Test appending to a new changelog file."""
        generator = ChangelogGenerator(changelog_file)
        timestamp = datetime.now(UTC)

        generator.append_to_changelog(sample_changes, timestamp)

        assert changelog_file.exists()
        content = changelog_file.read_text(encoding="utf-8")

        assert "# LLM Models CHANGELOG" in content
        assert "Added" in content
        assert "Removed" in content
        assert "gpt-4-turbo" in content
        assert "gpt-3.5" in content

    def test_append_to_existing_changelog(self, changelog_file, sample_changes):
        """Test appending to an existing changelog file."""
        # Create initial changelog
        changelog_file.write_text("# LLM Models CHANGELOG\n\nExisting content\n", encoding="utf-8")

        generator = ChangelogGenerator(changelog_file)
        timestamp = datetime.now(UTC)

        generator.append_to_changelog(sample_changes, timestamp)

        content = changelog_file.read_text(encoding="utf-8")

        # Should preserve existing content
        assert "Existing content" in content
        # Should add new changes
        assert "gpt-4-turbo" in content

    def test_changelog_format(self, changelog_file, sample_changes):
        """Test changelog format is correct."""
        generator = ChangelogGenerator(changelog_file)
        timestamp = datetime.now(UTC)

        generator.append_to_changelog(sample_changes, timestamp)

        content = changelog_file.read_text(encoding="utf-8")

        # Check for proper markdown formatting
        assert content.startswith("# LLM Models CHANGELOG")
        assert "##" in content  # Date headers
        assert "###" in content  # Change type headers

    def test_empty_changes_list(self, changelog_file):
        """Test with empty changes list."""
        generator = ChangelogGenerator(changelog_file)
        timestamp = datetime.now(UTC)

        # Should not create file or error with empty changes
        generator.append_to_changelog([], timestamp)

        # File may or may not exist depending on implementation
        # but should not error
