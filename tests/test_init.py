"""Tests for package initialization."""



class TestPackageInit:
    """Tests for llm_discovery.__init__."""

    def test_version_attribute_exists(self):
        """Test that __version__ is defined."""
        import llm_discovery

        assert hasattr(llm_discovery, "__version__")
        assert isinstance(llm_discovery.__version__, str)

    def test_discovery_client_exported(self):
        """Test that DiscoveryClient is exported."""
        from llm_discovery import DiscoveryClient

        assert DiscoveryClient is not None

    def test_export_functions_exported(self):
        """Test that export functions are exported."""
        from llm_discovery import (
            export_csv,
            export_json,
            export_markdown,
            export_toml,
            export_yaml,
        )

        assert callable(export_csv)
        assert callable(export_json)
        assert callable(export_markdown)
        assert callable(export_toml)
        assert callable(export_yaml)
