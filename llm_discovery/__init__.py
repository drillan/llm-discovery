"""llm-discovery: LLM model discovery and tracking system."""

from importlib.metadata import PackageNotFoundError, version

# Expose __version__ attribute using importlib.metadata
# This complies with Primary Data Non-Assumption Principle by retrieving
# version from pyproject.toml dynamically
try:
    __version__ = version("llm-discovery")
except PackageNotFoundError as e:
    raise PackageNotFoundError(
        "Package 'llm-discovery' not found. "
        "Please ensure it is properly installed: "
        "uv pip install llm-discovery"
    ) from e

# Expose public API
from llm_discovery.models import Model, ModelSource
from llm_discovery.services.discovery import DiscoveryService as DiscoveryClient
from llm_discovery.services.exporters import (
    export_csv,
    export_json,
    export_markdown,
    export_toml,
    export_yaml,
)

__all__ = [
    "__version__",
    # Client
    "DiscoveryClient",
    # Models
    "Model",
    "ModelSource",
    # Export functions
    "export_json",
    "export_csv",
    "export_yaml",
    "export_markdown",
    "export_toml",
]
