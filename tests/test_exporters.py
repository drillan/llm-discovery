"""Tests for export functionality."""

import csv
import json
import tomllib
from io import StringIO

import pytest
import yaml

from llm_discovery.services.exporters import (
    export_csv,
    export_json,
    export_markdown,
    export_toml,
    export_yaml,
)


class TestJsonExporter:
    """Tests for JSON exporter."""

    def test_export_json_valid(self, sample_models):
        """Test exporting models to JSON."""
        result = export_json(sample_models)
        data = json.loads(result)

        assert "metadata" in data
        assert "models" in data
        assert data["metadata"]["total_models"] == 3
        assert "openai" in data["models"]
        assert "google" in data["models"]
        assert "anthropic" in data["models"]

    def test_export_json_empty_models_raises_error(self):
        """Test that empty models list raises ValueError."""
        with pytest.raises(ValueError, match="models cannot be empty"):
            export_json([])

    def test_export_json_custom_indent(self, sample_models):
        """Test JSON export with custom indentation."""
        result = export_json(sample_models, indent=4)
        assert result.startswith("{")
        # Check that indentation is present
        assert "\n    " in result


class TestCsvExporter:
    """Tests for CSV exporter."""

    def test_export_csv_valid(self, sample_models):
        """Test exporting models to CSV."""
        result = export_csv(sample_models)
        reader = csv.DictReader(StringIO(result))
        rows = list(reader)

        assert len(rows) == 3
        assert rows[0]["model_id"] == "gpt-4"
        assert rows[0]["provider"] == "openai"

    def test_export_csv_empty_models_raises_error(self):
        """Test that empty models list raises ValueError."""
        with pytest.raises(ValueError, match="models cannot be empty"):
            export_csv([])

    def test_export_csv_headers(self, sample_models):
        """Test that CSV has correct headers."""
        result = export_csv(sample_models)
        lines = result.strip().split("\n")
        headers = lines[0]

        assert "model_id" in headers
        assert "model_name" in headers
        assert "provider" in headers
        assert "source" in headers
        assert "fetched_at" in headers


class TestYamlExporter:
    """Tests for YAML exporter."""

    def test_export_yaml_valid(self, sample_models):
        """Test exporting models to YAML."""
        result = export_yaml(sample_models)
        data = yaml.safe_load(result)

        assert "llm_models" in data
        assert "providers" in data["llm_models"]
        assert "total_count" in data["llm_models"]
        assert data["llm_models"]["total_count"] == 3

    def test_export_yaml_empty_models_raises_error(self):
        """Test that empty models list raises ValueError."""
        with pytest.raises(ValueError, match="models cannot be empty"):
            export_yaml([])

    def test_export_yaml_structure(self, sample_models):
        """Test YAML structure is correct."""
        result = export_yaml(sample_models)
        data = yaml.safe_load(result)

        providers = data["llm_models"]["providers"]
        assert "openai" in providers
        assert len(providers["openai"]) == 1
        assert providers["openai"][0]["id"] == "gpt-4"


class TestMarkdownExporter:
    """Tests for Markdown exporter."""

    def test_export_markdown_valid(self, sample_models):
        """Test exporting models to Markdown."""
        result = export_markdown(sample_models)

        assert "# LLM Models" in result
        assert "## Openai" in result
        assert "## Google" in result
        assert "## Anthropic" in result
        assert "gpt-4" in result

    def test_export_markdown_empty_models_raises_error(self):
        """Test that empty models list raises ValueError."""
        with pytest.raises(ValueError, match="models cannot be empty"):
            export_markdown([])

    def test_export_markdown_table_format(self, sample_models):
        """Test that Markdown contains table formatting."""
        result = export_markdown(sample_models)

        # Check for table headers
        assert "| Model ID |" in result
        assert "| Model Name |" in result
        # Check for table separator (actual separator has full dashes)
        assert "|----------|" in result


class TestTomlExporter:
    """Tests for TOML exporter."""

    def test_export_toml_valid(self, sample_models):
        """Test exporting models to TOML."""
        result = export_toml(sample_models)
        data = tomllib.loads(result)

        assert "llm_models" in data
        assert "providers" in data
        assert data["llm_models"]["total_count"] == 3

    def test_export_toml_empty_models_raises_error(self):
        """Test that empty models list raises ValueError."""
        with pytest.raises(ValueError, match="models cannot be empty"):
            export_toml([])

    def test_export_toml_structure(self, sample_models):
        """Test TOML structure is correct."""
        result = export_toml(sample_models)
        data = tomllib.loads(result)

        providers = data["providers"]
        assert len(providers) == 3
        assert providers[0]["name"] == "openai"
        assert len(providers[0]["models"]) == 1
