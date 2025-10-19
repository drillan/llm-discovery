"""Tests for configuration."""

from pathlib import Path

import pytest

from llm_discovery.models.config import Config


class TestConfig:
    """Tests for Config class."""

    def test_config_from_env_defaults(self, monkeypatch, tmp_path):
        """Test loading config with defaults."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        monkeypatch.setenv("LLM_DISCOVERY_CACHE_DIR", str(tmp_path))

        config = Config.from_env()
        assert config.openai_api_key is None
        assert config.google_api_key is None
        assert config.llm_discovery_cache_dir == tmp_path

    def test_config_openai_api_key(self, monkeypatch, tmp_path):
        """Test OpenAI API key configuration."""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
        monkeypatch.setenv("LLM_DISCOVERY_CACHE_DIR", str(tmp_path))

        config = Config.from_env()
        assert config.openai_api_key == "sk-test-key"

    def test_config_google_api_key(self, monkeypatch, tmp_path):
        """Test Google API key configuration."""
        monkeypatch.setenv("GOOGLE_API_KEY", "test-google-key")
        monkeypatch.setenv("LLM_DISCOVERY_CACHE_DIR", str(tmp_path))

        config = Config.from_env()
        assert config.google_api_key == "test-google-key"

    def test_config_vertex_ai_enabled(self, monkeypatch, tmp_path):
        """Test Vertex AI configuration."""
        # Create a fake credentials file
        creds_file = tmp_path / "creds.json"
        creds_file.write_text("{}", encoding="utf-8")

        monkeypatch.setenv("GOOGLE_GENAI_USE_VERTEXAI", "true")
        monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", str(creds_file))
        monkeypatch.setenv("LLM_DISCOVERY_CACHE_DIR", str(tmp_path))

        config = Config.from_env()
        assert config.google_genai_use_vertexai is True
        assert config.google_application_credentials == creds_file

    def test_config_vertex_ai_requires_credentials(self, monkeypatch, tmp_path):
        """Test that Vertex AI requires credentials."""
        monkeypatch.setenv("GOOGLE_GENAI_USE_VERTEXAI", "true")
        monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
        monkeypatch.setenv("LLM_DISCOVERY_CACHE_DIR", str(tmp_path))

        with pytest.raises(
            ValueError,
            match="GOOGLE_GENAI_USE_VERTEXAI is set to 'true'.*GOOGLE_APPLICATION_CREDENTIALS is not set",
        ):
            Config.from_env()

    def test_config_cache_dir_created(self, monkeypatch, tmp_path):
        """Test that cache directory is created if it doesn't exist."""
        cache_dir = tmp_path / "new_cache"
        monkeypatch.setenv("LLM_DISCOVERY_CACHE_DIR", str(cache_dir))

        config = Config.from_env()
        assert cache_dir.exists()
        assert config.llm_discovery_cache_dir == cache_dir

    def test_config_retention_days_default(self, monkeypatch, tmp_path):
        """Test default retention days."""
        monkeypatch.setenv("LLM_DISCOVERY_CACHE_DIR", str(tmp_path))

        config = Config.from_env()
        assert config.llm_discovery_retention_days == 30

    def test_config_retention_days_custom(self, monkeypatch, tmp_path):
        """Test custom retention days."""
        monkeypatch.setenv("LLM_DISCOVERY_RETENTION_DAYS", "7")
        monkeypatch.setenv("LLM_DISCOVERY_CACHE_DIR", str(tmp_path))

        config = Config.from_env()
        assert config.llm_discovery_retention_days == 7

    def test_config_default_cache_dir_platformdirs(self, monkeypatch):
        """Test that default cache dir uses platformdirs."""
        monkeypatch.delenv("LLM_DISCOVERY_CACHE_DIR", raising=False)

        config = Config.from_env()
        # Should use platformdirs default
        assert config.llm_discovery_cache_dir.exists()
        assert "llm-discovery" in str(config.llm_discovery_cache_dir)
