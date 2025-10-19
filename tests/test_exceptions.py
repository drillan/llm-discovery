"""Tests for custom exceptions."""


from llm_discovery.exceptions import (
    AuthenticationError,
    CacheCorruptedError,
    CacheNotFoundError,
    ConfigurationError,
    PartialFetchError,
    ProviderFetchError,
    SnapshotNotFoundError,
)


class TestExceptions:
    """Tests for custom exception classes."""

    def test_provider_fetch_error(self):
        """Test ProviderFetchError creation and attributes."""
        error = ProviderFetchError(provider_name="openai", cause="API timeout")
        assert error.provider_name == "openai"
        assert error.cause == "API timeout"
        assert "openai" in str(error)
        assert "API timeout" in str(error)

    def test_partial_fetch_error(self):
        """Test PartialFetchError creation and attributes."""
        error = PartialFetchError(
            successful_providers=["openai"],
            failed_providers=["google", "anthropic"],
        )
        assert error.successful_providers == ["openai"]
        assert error.failed_providers == ["google", "anthropic"]
        assert "openai" in str(error)
        assert "google" in str(error)

    def test_authentication_error(self):
        """Test AuthenticationError creation and attributes."""
        error = AuthenticationError(
            provider_name="google",
            details="Invalid API key",
        )
        assert error.provider_name == "google"
        assert error.details == "Invalid API key"
        assert "google" in str(error)
        assert "Invalid API key" in str(error)

    def test_cache_not_found_error(self):
        """Test CacheNotFoundError creation."""
        error = CacheNotFoundError("Cache file not found")
        assert "not found" in str(error).lower()

    def test_cache_corrupted_error(self):
        """Test CacheCorruptedError creation and attributes."""
        error = CacheCorruptedError(
            cache_path="/path/to/cache.toml",
            parse_error="Invalid TOML syntax",
        )
        assert error.cache_path == "/path/to/cache.toml"
        assert error.parse_error == "Invalid TOML syntax"
        assert "/path/to/cache.toml" in str(error)
        assert "Invalid TOML syntax" in str(error)

    def test_configuration_error(self):
        """Test ConfigurationError creation and attributes."""
        error = ConfigurationError(
            variable_name="OPENAI_API_KEY",
            suggestion="Set OPENAI_API_KEY environment variable",
        )
        assert error.variable_name == "OPENAI_API_KEY"
        assert error.suggestion == "Set OPENAI_API_KEY environment variable"
        assert "OPENAI_API_KEY" in str(error)

    def test_snapshot_not_found_error(self):
        """Test SnapshotNotFoundError creation."""
        from uuid import uuid4

        snapshot_id = uuid4()
        error = SnapshotNotFoundError(f"Snapshot {snapshot_id} not found")
        assert str(snapshot_id) in str(error)
