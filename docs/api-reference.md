---
title: Python API Reference
description: Complete Python API documentation for llm-discovery
---

# Python API Reference

Complete reference for using llm-discovery as a Python library.

## Package Version

Get the installed version of llm-discovery:

```python
from llm_discovery import __version__

print(__version__)  # Example: "0.1.0"
```

The version is dynamically retrieved from package metadata using `importlib.metadata`.

:::{note}
The version attribute uses Pydantic v2 for data validation throughout the library.
All model classes inherit from `pydantic.BaseModel` for automatic validation and serialization.
:::

## DiscoveryClient Class

The main interface for fetching and managing LLM model information.

### Import

```python
from llm_discovery import DiscoveryClient
```

### Constructor

```python
class DiscoveryClient:
    def __init__(
        self,
        *,
        config: Config | None = None
    ):
        """
        Initialize DiscoveryClient.

        Args:
            config: Configuration object (auto-generated from environment variables if None)

        Raises:
            ConfigurationError: Required environment variables not set
            RuntimeError: Configuration validation failed
        """
```

**Example**:

```python
from llm_discovery import DiscoveryClient

# Auto-configuration from environment variables
client = DiscoveryClient()

# Custom configuration
from llm_discovery.models import Config
custom_config = Config.from_env()
client = DiscoveryClient(config=custom_config)
```

### fetch_models()

Fetch model list from all providers concurrently.

```python
async def fetch_models(self) -> list[Model]:
    """
    Fetch model list from all providers.

    Returns:
        List of Model objects

    Raises:
        ProviderFetchError: API fetch failed (fail-fast behavior)
        PartialFetchError: Partial fetch failure
        AuthenticationError: Invalid credentials
        ConfigurationError: Environment variables not set
    """
```

**Example**:

```python
import asyncio
from llm_discovery import DiscoveryClient
from llm_discovery.exceptions import ProviderFetchError, PartialFetchError

async def main():
    client = DiscoveryClient()

    try:
        models = await client.fetch_models()
        print(f"Fetched {len(models)} models")

        for model in models:
            print(f"{model.provider_name}/{model.model_id}: {model.model_name}")

    except ProviderFetchError as e:
        print(f"API fetch failed: {e}")
        # External retry management (cron, CI/CD, etc.)

    except PartialFetchError as e:
        print(f"Partial failure: {e}")
        print(f"Successful providers: {e.successful_providers}")
        print(f"Failed providers: {e.failed_providers}")

asyncio.run(main())
```

:::{tip}
Use `asyncio.run()` for async best practices. The library is fully async-native using modern Python async/await patterns.
:::

### get_cached_models()

Retrieve models from local cache without API calls.

```python
def get_cached_models(self) -> list[Model]:
    """
    Retrieve models from local cache.

    Returns:
        List of cached Model objects

    Raises:
        CacheNotFoundError: Cache file does not exist
        CacheCorruptedError: Cache file is corrupted or invalid
    """
```

**Example**:

```python
from llm_discovery import DiscoveryClient
from llm_discovery.exceptions import CacheNotFoundError

client = DiscoveryClient()

try:
    models = client.get_cached_models()
    print(f"Loaded {len(models)} models from cache")
except CacheNotFoundError:
    print("No cache found. Run 'update' command first.")
```

## Config Class

Configuration management for llm-discovery.

### Import

```python
from llm_discovery.models.config import Config
```

### from_env()

Create configuration from environment variables.

```python
@classmethod
def from_env(cls) -> Config:
    """
    Create Config from environment variables.

    Returns:
        Config object

    Raises:
        ConfigurationError: Required environment variables not set
        ValueError: Invalid environment variable values
    """
```

**Example**:

```python
from llm_discovery.models.config import Config

# Load from environment variables
config = Config.from_env()

print(config.openai_api_key)  # Masked: "sk-...***"
print(config.cache_dir)       # Path to cache directory
```

**Environment Variables**:

- `OPENAI_API_KEY`: OpenAI API key (optional)
- `GOOGLE_API_KEY`: Google AI Studio API key (optional)
- `GOOGLE_GENAI_USE_VERTEXAI`: Use Vertex AI instead of AI Studio (optional, default: false)
- `GOOGLE_APPLICATION_CREDENTIALS`: Path to GCP credentials JSON (required if using Vertex AI)
- `LLM_DISCOVERY_CACHE_DIR`: Custom cache directory (optional, default: `~/.cache/llm-discovery`)

## ProviderSnapshot Class

Represents a snapshot of models from a single provider.

### Import

```python
from llm_discovery.models.provider import ProviderSnapshot
```

### Attributes

```python
class ProviderSnapshot(BaseModel):
    provider_name: str          # Provider identifier (e.g., "openai", "google")
    models: list[Model]         # List of models from this provider
    fetched_at: datetime        # Timestamp when models were fetched (UTC)
    source: ModelSource         # Data source (API or CACHE)
```

**Example**:

```python
from llm_discovery import DiscoveryClient

async def main():
    client = DiscoveryClient()
    snapshots = await client.fetch_all_models()

    for snapshot in snapshots:
        print(f"Provider: {snapshot.provider_name}")
        print(f"Fetched at: {snapshot.fetched_at}")
        print(f"Models: {len(snapshot.models)}")
```

## Model Class

Represents a single LLM model.

### Import

```python
from llm_discovery.models.provider import Model
```

### Attributes

```python
class Model(BaseModel):
    model_id: str              # Unique model identifier
    model_name: str            # Human-readable model name
    provider_name: str         # Provider name
    source: ModelSource        # Data source (API or CACHE)
    fetched_at: datetime       # Timestamp (UTC)
    capabilities: list[str]    # Model capabilities (optional)
```

**Example**:

```python
from llm_discovery import DiscoveryClient

async def main():
    client = DiscoveryClient()
    models = await client.fetch_models()

    # Filter models by capability
    chat_models = [m for m in models if "chat" in m.capabilities]

    for model in chat_models:
        print(f"{model.provider_name}/{model.model_id}")
        print(f"  Name: {model.model_name}")
        print(f"  Capabilities: {', '.join(model.capabilities)}")
```

## Data Export Formats

Export model data in multiple formats.

### JSON Export

```python
from llm_discovery.services.exporters import JSONExporter

exporter = JSONExporter()
models = client.get_cached_models()
json_data = exporter.export(models)

# Save to file
with open("models.json", "w") as f:
    f.write(json_data)
```

**Output Format**:

```json
{
  "models": [
    {
      "model_id": "gpt-4",
      "model_name": "GPT-4",
      "provider_name": "openai",
      "source": "API",
      "fetched_at": "2025-10-19T12:00:00Z",
      "capabilities": ["chat", "completion"]
    }
  ],
  "metadata": {
    "total_count": 1,
    "fetched_at": "2025-10-19T12:00:00Z"
  }
}
```

### CSV Export

```python
from llm_discovery.services.exporters import CSVExporter

exporter = CSVExporter()
csv_data = exporter.export(models)

with open("models.csv", "w") as f:
    f.write(csv_data)
```

**Output Format**:

```
provider_name,model_id,model_name,source,fetched_at,capabilities
openai,gpt-4,GPT-4,API,2025-10-19T12:00:00Z,"chat,completion"
```

### YAML Export

```python
from llm_discovery.services.exporters import YAMLExporter

exporter = YAMLExporter()
yaml_data = exporter.export(models)

with open("models.yaml", "w") as f:
    f.write(yaml_data)
```

**Output Format**:

```yaml
models:
  - model_id: gpt-4
    model_name: GPT-4
    provider_name: openai
    source: API
    fetched_at: '2025-10-19T12:00:00Z'
    capabilities:
      - chat
      - completion
```

### Markdown Export

```python
from llm_discovery.services.exporters import MarkdownExporter

exporter = MarkdownExporter()
markdown_data = exporter.export(models)

with open("models.md", "w") as f:
    f.write(markdown_data)
```

**Output Format**:

```markdown
# LLM Models

| Provider | Model ID | Model Name | Source | Fetched At |
|----------|----------|------------|--------|------------|
| openai   | gpt-4    | GPT-4      | API    | 2025-10-19T12:00:00Z |
```

### TOML Export

```python
from llm_discovery.services.exporters import TOMLExporter

exporter = TOMLExporter()
toml_data = exporter.export(models)

with open("models.toml", "w") as f:
    f.write(toml_data)
```

**Output Format**:

```toml
[[models]]
model_id = "gpt-4"
model_name = "GPT-4"
provider_name = "openai"
source = "API"
fetched_at = "2025-10-19T12:00:00Z"
capabilities = ["chat", "completion"]
```

## Exception Handling

All exceptions inherit from `LLMDiscoveryError`.

### Exception Hierarchy

```
LLMDiscoveryError
├── ConfigurationError          # Configuration issues
├── ProviderFetchError          # API fetch failures
│   ├── AuthenticationError     # Invalid credentials
│   └── NetworkError            # Network connectivity issues
├── PartialFetchError           # Partial fetch failures
├── CacheError                  # Cache-related errors
│   ├── CacheNotFoundError      # Cache file not found
│   └── CacheCorruptedError     # Cache file corrupted
└── ExportError                 # Export format errors
```

### Example Error Handling

```python
from llm_discovery import DiscoveryClient
from llm_discovery.exceptions import (
    ConfigurationError,
    AuthenticationError,
    ProviderFetchError,
    CacheNotFoundError
)

async def fetch_with_error_handling():
    try:
        client = DiscoveryClient()
        models = await client.fetch_models()
        return models

    except ConfigurationError as e:
        print(f"Configuration error: {e}")
        print("Please check environment variables")

    except AuthenticationError as e:
        print(f"Authentication failed: {e}")
        print("Please verify API keys")

    except ProviderFetchError as e:
        print(f"Failed to fetch models: {e}")
        # Fallback to cache
        try:
            return client.get_cached_models()
        except CacheNotFoundError:
            print("No cache available")
            raise

    except Exception as e:
        print(f"Unexpected error: {e}")
        raise
```

## Complete Usage Example

```python
import asyncio
from datetime import UTC, datetime
from llm_discovery import DiscoveryClient
from llm_discovery.models.config import Config
from llm_discovery.services.exporters import JSONExporter
from llm_discovery.exceptions import (
    ProviderFetchError,
    CacheNotFoundError
)

async def main():
    # Load configuration
    config = Config.from_env()
    client = DiscoveryClient(config=config)

    # Fetch models from all providers
    try:
        models = await client.fetch_models()
        print(f"✓ Fetched {len(models)} models from APIs")
    except ProviderFetchError as e:
        print(f"✗ API fetch failed: {e}")
        # Fallback to cache
        try:
            models = client.get_cached_models()
            print(f"✓ Loaded {len(models)} models from cache")
        except CacheNotFoundError:
            print("✗ No cache available")
            return

    # Filter models by provider
    openai_models = [m for m in models if m.provider_name == "openai"]
    google_models = [m for m in models if m.provider_name == "google"]

    print(f"\nOpenAI models: {len(openai_models)}")
    print(f"Google models: {len(google_models)}")

    # Export to JSON
    exporter = JSONExporter()
    json_data = exporter.export(models)

    with open("models.json", "w") as f:
        f.write(json_data)
    print(f"\n✓ Exported to models.json")

    # Display recent models
    recent_models = sorted(
        models,
        key=lambda m: m.fetched_at,
        reverse=True
    )[:10]

    print("\nRecent models:")
    for model in recent_models:
        print(f"  {model.provider_name}/{model.model_id}: {model.model_name}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Next Steps

- **CLI Reference**: See technical contract at `specs/001-llm-model-discovery/contracts/cli-interface.md`
- **Error Handling**: See `specs/001-llm-model-discovery/contracts/error-handling.md`
- **Contributing**: See `CONTRIBUTING.md` in the repository root
