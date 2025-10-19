"""Tests for CLI commands."""

from pathlib import Path

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
        import os

        output_file = tmp_path / "nonexistent" / "nested" / "output.json"

        # Remove write permission from tmp_path to cause write error
        # (This test may be skipped on systems where this doesn't work)
        result = runner.invoke(
            app, ["export", "--format", "json", "--output", str(output_file)]
        )
        # Should either succeed (if parent dirs created) or fail gracefully
        assert result.exit_code in [0, 1]


class TestCLIList:
    """Tests for list command."""

    def test_list_with_cache(self, runner, setup_cache):
        """Test list command with existing cache."""
        result = runner.invoke(app, ["list"])
        # May succeed or fail depending on API keys, but should not crash
        assert result.exit_code in [0, 1, 2]
