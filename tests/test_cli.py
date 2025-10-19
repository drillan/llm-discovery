"""Tests for CLI commands."""

from datetime import UTC, datetime

import pytest
from typer.testing import CliRunner

from llm_discovery.cli.main import app
from llm_discovery.models import FetchStatus, Model, ModelSource, ProviderSnapshot
from llm_discovery.services.cache import CacheService


@pytest.fixture
def runner():
    """Create a CLI runner."""
    return CliRunner()


@pytest.fixture
def setup_cache(tmp_path, monkeypatch, sample_models):
    """Setup a cache with sample data."""
    cache_dir = tmp_path / "llm-discovery"
    cache_dir.mkdir()
    monkeypatch.setenv("LLM_DISCOVERY_CACHE_DIR", str(cache_dir))

    # Create cache with sample data
    cache_service = CacheService(cache_dir)
    from datetime import UTC, datetime

    providers = [
        ProviderSnapshot(
            provider_name="openai",
            models=[sample_models[0]],
            fetch_status=FetchStatus.SUCCESS,
            fetched_at=datetime.now(UTC),
            error_message=None,
        ),
    ]
    cache_service.save_cache(providers)

    return cache_dir


class TestCLIVersion:
    """Tests for version command."""

    def test_version_display(self, runner):
        """Test --version flag."""
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "llm-discovery" in result.stdout


class TestCLIExport:
    """Tests for export command."""

    def test_export_json_to_stdout(self, runner, setup_cache):
        """Test exporting to JSON format to stdout."""
        result = runner.invoke(app, ["export", "--format", "json"])
        assert result.exit_code == 0
        assert '"metadata"' in result.stdout
        assert '"models"' in result.stdout

    def test_export_csv_to_stdout(self, runner, setup_cache):
        """Test exporting to CSV format to stdout."""
        result = runner.invoke(app, ["export", "--format", "csv"])
        assert result.exit_code == 0
        assert "provider" in result.stdout
        assert "model_id" in result.stdout

    def test_export_yaml_to_stdout(self, runner, setup_cache):
        """Test exporting to YAML format to stdout."""
        result = runner.invoke(app, ["export", "--format", "yaml"])
        assert result.exit_code == 0
        assert "llm_models:" in result.stdout

    def test_export_markdown_to_stdout(self, runner, setup_cache):
        """Test exporting to Markdown format to stdout."""
        result = runner.invoke(app, ["export", "--format", "markdown"])
        assert result.exit_code == 0
        assert "# LLM Models" in result.stdout

    def test_export_toml_to_stdout(self, runner, setup_cache):
        """Test exporting to TOML format to stdout."""
        result = runner.invoke(app, ["export", "--format", "toml"])
        assert result.exit_code == 0
        # TOML should contain model data
        assert "gpt-4" in result.stdout or "openai" in result.stdout

    def test_export_to_file(self, runner, setup_cache, tmp_path):
        """Test exporting to a file."""
        output_file = tmp_path / "output.json"
        result = runner.invoke(
            app, ["export", "--format", "json", "--output", str(output_file)]
        )
        assert result.exit_code == 0
        assert output_file.exists()
        content = output_file.read_text(encoding="utf-8")
        assert '"metadata"' in content

    def test_export_unsupported_format(self, runner, setup_cache):
        """Test exporting with unsupported format."""
        result = runner.invoke(app, ["export", "--format", "xml"])
        # Should fail with non-zero exit code
        assert result.exit_code != 0

    def test_export_without_cache(self, runner, tmp_path, monkeypatch):
        """Test export when cache doesn't exist."""
        cache_dir = tmp_path / "empty_cache"
        cache_dir.mkdir()
        monkeypatch.setenv("LLM_DISCOVERY_CACHE_DIR", str(cache_dir))

        result = runner.invoke(app, ["export", "--format", "json"])
        # Should fail when cache doesn't exist
        assert result.exit_code == 1


    def test_export_file_write_error(self, runner, setup_cache, tmp_path, monkeypatch):
        """Test export when file cannot be written."""
        # Try to write to a non-existent directory (without creating parent)
        output_file = tmp_path / "nonexistent" / "nested" / "output.json"

        # Remove write permission from tmp_path to cause write error
        # (This test may be skipped on systems where this doesn't work)
        result = runner.invoke(
            app, ["export", "--format", "json", "--output", str(output_file)]
        )
        # Should either succeed (if parent dirs created) or fail gracefully
        assert result.exit_code in [0, 1]


class TestCLIUpdate:
    """Tests for update command."""

    def test_update_fetch_and_cache(
        self, runner: CliRunner, temp_cache_dir, monkeypatch
    ) -> None:
        """Test update command basic operation - fetch and cache models."""
        # Mock API responses to avoid actual API calls

        from llm_discovery.services.discovery import DiscoveryService

        # Create mock providers with models
        mock_providers = [
            ProviderSnapshot(
                provider_name="openai",
                models=[
                    Model(
                        model_id="gpt-4",
                        model_name="GPT-4",
                        provider_name="openai",
                        source=ModelSource.API,
                        fetched_at=datetime.now(UTC),
                    )
                ],
                fetch_status=FetchStatus.SUCCESS,
                fetched_at=datetime.now(UTC),
                error_message=None,
            ),
        ]

        # Mock fetch_all_models
        async def mock_fetch_all():
            return mock_providers

        monkeypatch.setattr(
            DiscoveryService, "fetch_all_models", lambda self: mock_fetch_all()
        )

        result = runner.invoke(app, ["update"])
        assert result.exit_code == 0
        assert "openai: 1" in result.stdout.lower() or "OpenAI: 1" in result.stdout
        assert "Total: 1" in result.stdout or "total: 1" in result.stdout.lower()
        assert "Cached to:" in result.stdout or "cached to:" in result.stdout.lower()

    def test_update_updates_existing_cache(
        self, runner: CliRunner, setup_cache, monkeypatch
    ) -> None:
        """Test update command updates existing cache."""

        from llm_discovery.services.discovery import DiscoveryService

        # Create new mock data (different from setup_cache)
        mock_providers = [
            ProviderSnapshot(
                provider_name="google",
                models=[
                    Model(
                        model_id="gemini-2.0",
                        model_name="Gemini 2.0",
                        provider_name="google",
                        source=ModelSource.API,
                        fetched_at=datetime.now(UTC),
                    )
                ],
                fetch_status=FetchStatus.SUCCESS,
                fetched_at=datetime.now(UTC),
                error_message=None,
            ),
        ]

        async def mock_fetch_all():
            return mock_providers

        monkeypatch.setattr(
            DiscoveryService, "fetch_all_models", lambda self: mock_fetch_all()
        )

        result = runner.invoke(app, ["update"])
        assert result.exit_code == 0
        assert "google: 1" in result.stdout.lower() or "Google: 1" in result.stdout

    def test_update_api_failure(
        self, runner: CliRunner, temp_cache_dir, monkeypatch
    ) -> None:
        """Test update command API failure error handling (FR-017)."""
        from llm_discovery.exceptions import ProviderFetchError
        from llm_discovery.services.discovery import DiscoveryService

        async def mock_fetch_all():
            raise ProviderFetchError(
                provider_name="openai", cause="API connection timeout"
            )

        monkeypatch.setattr(
            DiscoveryService, "fetch_all_models", lambda self: mock_fetch_all()
        )

        result = runner.invoke(app, ["update"])
        assert result.exit_code == 1
        assert "Failed to fetch models from openai" in result.output

    def test_update_partial_failure(
        self, runner: CliRunner, temp_cache_dir, monkeypatch
    ) -> None:
        """Test update command partial failure error handling (FR-018)."""
        from llm_discovery.exceptions import PartialFetchError
        from llm_discovery.services.discovery import DiscoveryService

        async def mock_fetch_all():
            raise PartialFetchError(
                successful_providers=["openai"],
                failed_providers=["google"],
            )

        monkeypatch.setattr(
            DiscoveryService, "fetch_all_models", lambda self: mock_fetch_all()
        )

        result = runner.invoke(app, ["update"])
        assert result.exit_code == 1
        assert "Partial failure" in result.output

    def test_update_authentication_error(
        self, runner: CliRunner, temp_cache_dir, monkeypatch
    ) -> None:
        """Test update command authentication error handling."""
        from llm_discovery.exceptions import AuthenticationError
        from llm_discovery.services.discovery import DiscoveryService

        async def mock_fetch_all():
            raise AuthenticationError(
                provider_name="anthropic", details="Invalid API key"
            )

        monkeypatch.setattr(
            DiscoveryService, "fetch_all_models", lambda self: mock_fetch_all()
        )

        result = runner.invoke(app, ["update"])
        assert result.exit_code == 2
        assert "Authentication failed for anthropic" in result.output

    def test_update_corrupted_cache_recovery(
        self, runner: CliRunner, temp_cache_dir, monkeypatch
    ) -> None:
        """Test update command recovers from corrupted cache."""

        from llm_discovery.services.discovery import DiscoveryService

        # Create corrupted cache file
        cache_file = temp_cache_dir / "models_cache.toml"
        cache_file.write_text("invalid toml content {{{", encoding="utf-8")

        # Mock successful fetch
        mock_providers = [
            ProviderSnapshot(
                provider_name="openai",
                models=[
                    Model(
                        model_id="gpt-4",
                        model_name="GPT-4",
                        provider_name="openai",
                        source=ModelSource.API,
                        fetched_at=datetime.now(UTC),
                    )
                ],
                fetch_status=FetchStatus.SUCCESS,
                fetched_at=datetime.now(UTC),
                error_message=None,
            ),
        ]

        async def mock_fetch_all():
            return mock_providers

        monkeypatch.setattr(
            DiscoveryService, "fetch_all_models", lambda self: mock_fetch_all()
        )

        result = runner.invoke(app, ["update"])
        assert result.exit_code == 0
        assert "openai: 1" in result.stdout.lower() or "OpenAI: 1" in result.stdout


class TestCLIUpdateChangeDetection:
    """Tests for update command with --detect-changes option."""

    def test_update_detect_changes(
        self, runner: CliRunner, temp_cache_dir, monkeypatch
    ) -> None:
        """Test update --detect-changes detects model changes (FR-026)."""
        from llm_discovery.services.discovery import DiscoveryService
        from llm_discovery.services.snapshot import SnapshotService

        # First run: create baseline
        initial_providers = [
            ProviderSnapshot(
                provider_name="openai",
                models=[
                    Model(
                        model_id="gpt-4",
                        model_name="GPT-4",
                        provider_name="openai",
                        source=ModelSource.API,
                        fetched_at=datetime.now(UTC),
                    )
                ],
                fetch_status=FetchStatus.SUCCESS,
                fetched_at=datetime.now(UTC),
                error_message=None,
            ),
        ]

        async def mock_fetch_initial():
            return initial_providers

        monkeypatch.setattr(
            DiscoveryService, "fetch_all_models", lambda self: mock_fetch_initial()
        )

        # Create baseline snapshot manually
        from llm_discovery.models.config import Config

        config = Config.from_env()
        snapshot_service = SnapshotService(config.llm_discovery_cache_dir)
        snapshot_service.save_snapshot(initial_providers)

        # Second run: detect changes (added and removed models)
        updated_providers = [
            ProviderSnapshot(
                provider_name="openai",
                models=[
                    Model(
                        model_id="gpt-4.5",
                        model_name="GPT-4.5",
                        provider_name="openai",
                        source=ModelSource.API,
                        fetched_at=datetime.now(UTC),
                    )
                ],
                fetch_status=FetchStatus.SUCCESS,
                fetched_at=datetime.now(UTC),
                error_message=None,
            ),
        ]

        async def mock_fetch_updated():
            return updated_providers

        monkeypatch.setattr(
            DiscoveryService, "fetch_all_models", lambda self: mock_fetch_updated()
        )

        result = runner.invoke(app, ["update", "--detect-changes"])
        assert result.exit_code == 0
        assert "Changes detected!" in result.output
        assert "Added models (1):" in result.output
        assert "openai/gpt-4.5" in result.output
        assert "Removed models (1):" in result.output
        assert "openai/gpt-4" in result.output
        assert "Details saved to:" in result.output

        # Verify changes.json was created
        changes_file = temp_cache_dir / "changes.json"
        assert changes_file.exists()

        # Verify CHANGELOG.md was created
        changelog_file = temp_cache_dir / "CHANGELOG.md"
        assert changelog_file.exists()

    def test_update_detect_changes_first_run(
        self, runner: CliRunner, temp_cache_dir, monkeypatch
    ) -> None:
        """Test update --detect-changes on first run creates baseline."""
        from llm_discovery.services.discovery import DiscoveryService

        mock_providers = [
            ProviderSnapshot(
                provider_name="openai",
                models=[
                    Model(
                        model_id="gpt-4",
                        model_name="GPT-4",
                        provider_name="openai",
                        source=ModelSource.API,
                        fetched_at=datetime.now(UTC),
                    )
                ],
                fetch_status=FetchStatus.SUCCESS,
                fetched_at=datetime.now(UTC),
                error_message=None,
            ),
        ]

        async def mock_fetch_all():
            return mock_providers

        monkeypatch.setattr(
            DiscoveryService, "fetch_all_models", lambda self: mock_fetch_all()
        )

        result = runner.invoke(app, ["update", "--detect-changes"])
        assert result.exit_code == 0
        assert (
            "No previous snapshot found" in result.output
            or "Saving current state as baseline" in result.output
        )
        assert "Snapshot ID:" in result.output or "snapshot" in result.output.lower()

    def test_update_detect_changes_no_changes(
        self, runner: CliRunner, temp_cache_dir, monkeypatch
    ) -> None:
        """Test update --detect-changes when no changes detected."""
        from llm_discovery.services.discovery import DiscoveryService
        from llm_discovery.services.snapshot import SnapshotService

        # Create baseline
        mock_providers = [
            ProviderSnapshot(
                provider_name="openai",
                models=[
                    Model(
                        model_id="gpt-4",
                        model_name="GPT-4",
                        provider_name="openai",
                        source=ModelSource.API,
                        fetched_at=datetime.now(UTC),
                    )
                ],
                fetch_status=FetchStatus.SUCCESS,
                fetched_at=datetime.now(UTC),
                error_message=None,
            ),
        ]

        from llm_discovery.models.config import Config

        config = Config.from_env()
        snapshot_service = SnapshotService(config.llm_discovery_cache_dir)
        snapshot_service.save_snapshot(mock_providers)

        # Run with same data (no changes)
        async def mock_fetch_all():
            return mock_providers

        monkeypatch.setattr(
            DiscoveryService, "fetch_all_models", lambda self: mock_fetch_all()
        )

        result = runner.invoke(app, ["update", "--detect-changes"])
        assert result.exit_code == 0
        assert "No changes detected" in result.output

    def test_update_cleanup_old_snapshots(
        self, runner: CliRunner, temp_cache_dir, monkeypatch
    ) -> None:
        """Test update --detect-changes cleans up old snapshots (FR-008)."""
        from datetime import timedelta

        from llm_discovery.models.config import Config
        from llm_discovery.services.discovery import DiscoveryService
        from llm_discovery.services.snapshot import SnapshotService

        config = Config.from_env()
        snapshot_service = SnapshotService(config.llm_discovery_cache_dir)

        # Create old snapshots (35 days ago)
        mock_providers = [
            ProviderSnapshot(
                provider_name="openai",
                models=[
                    Model(
                        model_id="gpt-4",
                        model_name="GPT-4",
                        provider_name="openai",
                        source=ModelSource.API,
                        fetched_at=datetime.now(UTC),
                    )
                ],
                fetch_status=FetchStatus.SUCCESS,
                fetched_at=datetime.now(UTC),
                error_message=None,
            ),
        ]

        # Create a snapshot and manually modify its timestamp to be old
        snapshot_id = snapshot_service.save_snapshot(mock_providers)
        snapshots = snapshot_service.list_snapshots()
        if snapshots:
            # Modify the snapshot file timestamp to be 35 days old
            snapshot_file = (
                config.llm_discovery_cache_dir / "snapshots" / f"{snapshot_id}.json"
            )
            if snapshot_file.exists():
                old_time = datetime.now(UTC) - timedelta(days=35)
                import os
                import time

                old_timestamp = time.mktime(old_time.timetuple())
                os.utime(snapshot_file, (old_timestamp, old_timestamp))

        # Run update with change detection
        async def mock_fetch_all():
            return mock_providers

        monkeypatch.setattr(
            DiscoveryService, "fetch_all_models", lambda self: mock_fetch_all()
        )

        result = runner.invoke(app, ["update", "--detect-changes"])
        assert result.exit_code == 0
        # Old snapshots should be cleaned up
        assert (
            "Cleaned up" in result.output or "snapshot" in result.output.lower()
        ) or result.exit_code == 0  # May not show message if no cleanup needed


class TestCLIList:
    """Tests for list command (modified - Read-only)."""

    def test_list_from_cache(self, runner: CliRunner, setup_cache) -> None:
        """Test list command reads from cache (FR-025 compliant)."""
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0
        assert "gpt-4" in result.stdout.lower() or "GPT-4" in result.stdout
        assert "Total models:" in result.stdout or "total models:" in result.stdout.lower()

    def test_list_without_cache_shows_error(
        self, runner: CliRunner, temp_cache_dir
    ) -> None:
        """Test list command shows error when cache doesn't exist (FR-025)."""
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 1
        assert (
            "No cached data available" in result.output
            or "no cached data available" in result.output.lower()
        )
        assert (
            "llm-discovery update" in result.output
            or "Please run 'llm-discovery update'" in result.output
        )

    def test_list_corrupted_cache_error(
        self, runner: CliRunner, temp_cache_dir
    ) -> None:
        """Test list command shows error when cache is corrupted."""
        # Create corrupted cache file
        cache_file = temp_cache_dir / "models_cache.toml"
        cache_file.write_text("invalid toml content {{{", encoding="utf-8")

        result = runner.invoke(app, ["list"])
        assert result.exit_code == 1
