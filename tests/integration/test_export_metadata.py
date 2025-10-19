"""Integration tests for export with metadata."""

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from llm_discovery.cli.main import app
from llm_discovery.models import DataSourceInfo, DataSourceType, Model, ModelSource
from llm_discovery.services.discovery import DiscoveryService


class TestExportMetadata:
    """Test export commands include data source metadata."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create CLI test runner."""
        return CliRunner()

    @pytest.fixture
    def sample_models(self) -> list[Model]:
        """Create sample models for testing."""
        return [
            Model(
                model_id="gpt-4",
                model_name="GPT-4",
                provider_name="openai",
                source=ModelSource.API,
                fetched_at=datetime.now(UTC),
                metadata={"created": 1234567890, "owned_by": "openai"},
            ),
            Model(
                model_id="gemini-pro",
                model_name="Gemini Pro",
                provider_name="google",
                source=ModelSource.API,
                fetched_at=datetime.now(UTC) - timedelta(hours=12),
                metadata={"version": "1.0"},
            ),
        ]

    @pytest.fixture
    def prebuilt_data_source(self) -> DataSourceInfo:
        """Create prebuilt data source info."""
        return DataSourceInfo(
            source_type=DataSourceType.PREBUILT,
            timestamp=datetime.now(UTC) - timedelta(hours=12),
            provider_name="prebuilt",
        )

    @pytest.fixture
    def api_data_source(self) -> DataSourceInfo:
        """Create API data source info."""
        return DataSourceInfo(
            source_type=DataSourceType.API,
            timestamp=datetime.now(UTC),
            provider_name="openai",
        )

    def test_json_export_includes_data_source_metadata(
        self,
        runner: CliRunner,
        tmp_path: Path,
        sample_models: list[Model],
        prebuilt_data_source: DataSourceInfo,
    ):
        """Given prebuilt data, JSON export includes data source metadata.

        This test verifies FR-042: Export transparency requirement.
        """
        output_file = tmp_path / "export.json"

        with (
            patch.object(
                DiscoveryService, "get_cached_models", return_value=sample_models
            ),
            patch.object(
                DiscoveryService,
                "get_data_source_info",
                return_value=prebuilt_data_source,
            ),
        ):
            result = runner.invoke(
                app, ["export", "--format", "json", "--output", str(output_file)]
            )

        # Should succeed
        assert result.exit_code == 0

        # Verify file exists
        assert output_file.exists()

        # Parse JSON
        data = json.loads(output_file.read_text())

        # Should include data_source metadata
        assert "metadata" in data
        metadata = data["metadata"]

        # Should include data source type
        assert "data_source" in metadata or "source_type" in metadata

        # Should include timestamp
        assert "generated_at" in metadata or "timestamp" in metadata

    def test_json_export_includes_api_data_source(
        self,
        runner: CliRunner,
        tmp_path: Path,
        sample_models: list[Model],
        api_data_source: DataSourceInfo,
    ):
        """Given API data, JSON export includes API source metadata."""
        output_file = tmp_path / "export.json"

        with (
            patch.object(
                DiscoveryService, "get_cached_models", return_value=sample_models
            ),
            patch.object(
                DiscoveryService, "get_data_source_info", return_value=api_data_source
            ),
        ):
            result = runner.invoke(
                app, ["export", "--format", "json", "--output", str(output_file)]
            )

        # Should succeed
        assert result.exit_code == 0

        # Parse JSON
        data = json.loads(output_file.read_text())

        # Should indicate API source
        metadata = data["metadata"]
        source_field = metadata.get("data_source") or metadata.get("source_type")
        assert source_field in ["api", "API", DataSourceType.API.value]

    def test_csv_export_includes_data_source_column(
        self,
        runner: CliRunner,
        tmp_path: Path,
        sample_models: list[Model],
        prebuilt_data_source: DataSourceInfo,
    ):
        """Given prebuilt data, CSV export includes data_source column.

        This test verifies FR-043: CSV transparency requirement.
        """
        output_file = tmp_path / "export.csv"

        with (
            patch.object(
                DiscoveryService, "get_cached_models", return_value=sample_models
            ),
            patch.object(
                DiscoveryService,
                "get_data_source_info",
                return_value=prebuilt_data_source,
            ),
        ):
            result = runner.invoke(
                app, ["export", "--format", "csv", "--output", str(output_file)]
            )

        # Should succeed
        assert result.exit_code == 0

        # Verify file exists
        assert output_file.exists()

        # Parse CSV
        csv_content = output_file.read_text()

        # Should include data_source column in header
        assert "data_source" in csv_content or "source_type" in csv_content

        # Should include prebuilt values
        assert "prebuilt" in csv_content.lower() or "PREBUILT" in csv_content

    def test_markdown_export_includes_source_header(
        self,
        runner: CliRunner,
        tmp_path: Path,
        sample_models: list[Model],
        prebuilt_data_source: DataSourceInfo,
    ):
        """Given prebuilt data, Markdown export includes source information.

        This test verifies FR-044: Markdown transparency requirement.
        """
        output_file = tmp_path / "export.md"

        with (
            patch.object(
                DiscoveryService, "get_cached_models", return_value=sample_models
            ),
            patch.object(
                DiscoveryService,
                "get_data_source_info",
                return_value=prebuilt_data_source,
            ),
        ):
            result = runner.invoke(
                app, ["export", "--format", "markdown", "--output", str(output_file)]
            )

        # Should succeed
        assert result.exit_code == 0

        # Verify file exists
        assert output_file.exists()

        # Parse Markdown
        md_content = output_file.read_text()

        # Should include source information in header or metadata section
        assert (
            "source" in md_content.lower()
            or "prebuilt" in md_content.lower()
            or "Data Source" in md_content
        )

        # Should include timestamp information
        assert (
            "generated" in md_content.lower()
            or "timestamp" in md_content.lower()
            or "updated" in md_content.lower()
        )

    def test_export_without_data_source_info_graceful_degradation(
        self, runner: CliRunner, tmp_path: Path, sample_models: list[Model]
    ):
        """Given no data source info, export still succeeds with models.

        This test verifies graceful degradation for exports.
        """
        output_file = tmp_path / "export.json"

        with (
            patch.object(
                DiscoveryService, "get_cached_models", return_value=sample_models
            ),
            patch.object(DiscoveryService, "get_data_source_info", return_value=None),
        ):
            result = runner.invoke(
                app, ["export", "--format", "json", "--output", str(output_file)]
            )

        # Should still succeed
        assert result.exit_code == 0

        # Verify file exists
        assert output_file.exists()

        # Parse JSON
        data = json.loads(output_file.read_text())

        # Should still include models
        assert "models" in data
        assert len(data["models"]) > 0
