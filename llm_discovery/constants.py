"""Application constants for llm-discovery.

NOTE: Package version is NOT defined here. It is retrieved dynamically using
importlib.metadata to comply with Primary Data Non-Assumption Principle.
"""

# Cache settings
CACHE_DIR_NAME = "llm-discovery"
DEFAULT_RETENTION_DAYS = 30
TOML_CACHE_VERSION = "1.0.0"  # Cache format version, not package version

# Supported export formats
SUPPORTED_EXPORT_FORMATS = ["json", "csv", "yaml", "markdown", "toml"]

# Provider names
PROVIDER_OPENAI = "openai"
PROVIDER_GOOGLE = "google"
PROVIDER_ANTHROPIC = "anthropic"
