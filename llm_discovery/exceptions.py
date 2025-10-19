"""Exception hierarchy for llm-discovery."""


class LLMDiscoveryError(Exception):
    """Base exception for llm-discovery."""

    pass


class ProviderFetchError(LLMDiscoveryError):
    """API fetch failure (fail-fast principle)."""

    def __init__(self, provider_name: str, cause: str):
        """Initialize ProviderFetchError.

        Args:
            provider_name: Failed provider name
            cause: Failure cause
        """
        self.provider_name = provider_name
        self.cause = cause
        super().__init__(f"Failed to fetch from {provider_name}: {cause}")


class PartialFetchError(LLMDiscoveryError):
    """Partial fetch failure."""

    def __init__(self, successful_providers: list[str], failed_providers: list[str]):
        """Initialize PartialFetchError.

        Args:
            successful_providers: List of successful provider names
            failed_providers: List of failed provider names
        """
        self.successful_providers = successful_providers
        self.failed_providers = failed_providers
        super().__init__(
            f"Partial failure. Successful: {successful_providers}, "
            f"Failed: {failed_providers}"
        )


class AuthenticationError(LLMDiscoveryError):
    """Authentication failure (API key, GCP credentials, etc.)."""

    def __init__(self, provider_name: str, details: str):
        """Initialize AuthenticationError.

        Args:
            provider_name: Provider name with auth failure
            details: Detailed error information
        """
        self.provider_name = provider_name
        self.details = details
        super().__init__(f"Authentication failed for {provider_name}: {details}")


class ConfigurationError(LLMDiscoveryError):
    """Configuration error (environment variable not set, etc.)."""

    def __init__(self, variable_name: str, suggestion: str):
        """Initialize ConfigurationError.

        Args:
            variable_name: Invalid or missing environment variable name
            suggestion: Suggested resolution
        """
        self.variable_name = variable_name
        self.suggestion = suggestion
        super().__init__(f"Configuration error for {variable_name}. {suggestion}")


class CacheNotFoundError(LLMDiscoveryError):
    """Cache file not found."""

    pass


class CacheCorruptedError(LLMDiscoveryError):
    """Cache file corrupted."""

    def __init__(self, cache_path: str, parse_error: str):
        """Initialize CacheCorruptedError.

        Args:
            cache_path: Path to corrupted cache file
            parse_error: Parse error details
        """
        self.cache_path = cache_path
        self.parse_error = parse_error
        super().__init__(f"Cache file corrupted at {cache_path}: {parse_error}")


class SnapshotNotFoundError(LLMDiscoveryError):
    """Snapshot with specified ID not found."""

    def __init__(self, snapshot_id: str):
        """Initialize SnapshotNotFoundError.

        Args:
            snapshot_id: Snapshot ID that was not found
        """
        self.snapshot_id = snapshot_id
        super().__init__(f"Snapshot not found: {snapshot_id}")
