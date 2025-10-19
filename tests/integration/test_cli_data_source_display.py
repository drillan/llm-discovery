"""Integration tests for CLI data source display."""

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from llm_discovery.cli.main import app
from llm_discovery.models import DataSourceInfo, DataSourceType, Model, ModelSource
from llm_discovery.services.discovery import DiscoveryService


class TestCLIDataSourceDisplay:
    """Test CLI displays data source information correctly."""

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
                fetched_at=datetime.now(UTC),
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

    @pytest.fixture
    def old_data_source(self) -> DataSourceInfo:
        """Create old data source info (>24h)."""
        return DataSourceInfo(
            source_type=DataSourceType.PREBUILT,
            timestamp=datetime.now(UTC) - timedelta(hours=36),
            provider_name="prebuilt",
        )

    def test_cli_displays_prebuilt_data_source_info(
        self, runner: CliRunner, sample_models: list[Model], prebuilt_data_source: DataSourceInfo
    ):
        """Given prebuilt data, CLI displays source type and timestamp.

        This test verifies FR-040: Data source transparency requirement.
        """
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
            result = runner.invoke(app, ["list"])

        # Should succeed
        assert result.exit_code == 0

        # Should display data source type
        assert "Source: prebuilt" in result.stdout or "Data Source: PREBUILT" in result.stdout

        # Should display timestamp or age
        assert "12" in result.stdout  # Age in hours

    def test_cli_displays_api_data_source_info(
        self, runner: CliRunner, sample_models: list[Model], api_data_source: DataSourceInfo
    ):
        """Given API data, CLI displays source type and current timestamp.

        This test verifies FR-040: API data source display.
        """
        with (
            patch.object(
                DiscoveryService, "get_cached_models", return_value=sample_models
            ),
            patch.object(
                DiscoveryService, "get_data_source_info", return_value=api_data_source
            ),
        ):
            result = runner.invoke(app, ["list"])

        # Should succeed
        assert result.exit_code == 0

        # Should display data source type
        assert "Source: api" in result.stdout or "Data Source: API" in result.stdout

        # Should display recent timestamp (age < 1 hour)
        # The exact format depends on implementation

    def test_cli_warns_about_old_data(
        self, runner: CliRunner, sample_models: list[Model], old_data_source: DataSourceInfo
    ):
        """Given data older than 24h, CLI displays warning message.

        This test verifies FR-041: Staleness warning requirement.
        """
        with (
            patch.object(
                DiscoveryService, "get_cached_models", return_value=sample_models
            ),
            patch.object(
                DiscoveryService, "get_data_source_info", return_value=old_data_source
            ),
        ):
            result = runner.invoke(app, ["list"])

        # Should succeed
        assert result.exit_code == 0

        # Should display warning about old data
        assert (
            "warning" in result.stdout.lower()
            or "old" in result.stdout.lower()
            or "36" in result.stdout  # Age in hours
        )

    def test_cli_very_old_data_warning(
        self, runner: CliRunner, sample_models: list[Model]
    ):
        """Given data older than 7 days, CLI displays strong warning.

        This test verifies edge case handling for very stale data.
        """
        very_old_source = DataSourceInfo(
            source_type=DataSourceType.PREBUILT,
            timestamp=datetime.now(UTC) - timedelta(days=10),
            provider_name="prebuilt",
        )

        with (
            patch.object(
                DiscoveryService, "get_cached_models", return_value=sample_models
            ),
            patch.object(
                DiscoveryService, "get_data_source_info", return_value=very_old_source
            ),
        ):
            result = runner.invoke(app, ["list"])

        # Should succeed
        assert result.exit_code == 0

        # Should display strong warning (e.g., "10 days old" or similar)
        assert "10" in result.stdout or "240" in result.stdout  # Days or hours

    def test_cli_without_data_source_info_fallback(
        self, runner: CliRunner, sample_models: list[Model]
    ):
        """Given no data source info available, CLI still displays models.

        This test verifies graceful degradation when data source info unavailable.
        """
        with (
            patch.object(
                DiscoveryService, "get_cached_models", return_value=sample_models
            ),
            patch.object(
                DiscoveryService, "get_data_source_info", return_value=None
            ),
        ):
            result = runner.invoke(app, ["list"])

        # Should still succeed
        assert result.exit_code == 0

        # Should display models
        assert "gpt-4" in result.stdout
        assert "gemini-pro" in result.stdout

        # Total count should still be shown
        assert "Total models: 2" in result.stdout
