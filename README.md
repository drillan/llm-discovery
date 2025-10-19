# llm-discovery

LLM model discovery and tracking system for real-time monitoring of available models across multiple providers (OpenAI, Google AI Studio/Vertex AI, Anthropic).

## Features

- **Real-time Model Discovery**: Fetch available models from multiple LLM providers
- **Multi-format Export**: Export model data in JSON, CSV, YAML, Markdown, and TOML formats
- **Change Detection**: Track model additions and removals over time
- **CI/CD Integration**: Easy integration with GitHub Actions and other CI/CD systems
- **Python API**: Use as a library in your Python applications
- **Offline Mode**: Cache-first operation for offline usage

## Installation

### Method 1: uvx (No Installation Required - Recommended)

```bash
uvx llm-discovery list
```

### Method 2: pip

```bash
pip install llm-discovery
```

## Quick Start

### Environment Variables

Set up API keys for the providers you want to use:

```bash
# OpenAI
export OPENAI_API_KEY="sk-..."

# Google AI Studio
export GOOGLE_API_KEY="AIza..."

# Google Vertex AI (alternative to AI Studio)
export GOOGLE_GENAI_USE_VERTEXAI=true
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/gcp-credentials.json"
```

### Basic Usage

```bash
# List all models
uvx llm-discovery list

# Export to JSON
uvx llm-discovery export --format json --output models.json

# Detect changes
uvx llm-discovery list --detect-changes
```

### Python API

```python
import asyncio
from llm_discovery import DiscoveryClient
from llm_discovery.models.config import Config

async def main():
    # Load configuration from environment variables
    config = Config.from_env()
    client = DiscoveryClient(config)

    # Fetch models from all providers
    provider_snapshots = await client.fetch_all_models()

    # Display all models
    for provider in provider_snapshots:
        for model in provider.models:
            print(f"{model.provider_name}/{model.model_id}: {model.model_name}")

asyncio.run(main())
```

## Documentation

For detailed documentation, see:

- [Quickstart Guide](specs/001-llm-model-discovery/quickstart.md)
- [API Reference](specs/001-llm-model-discovery/contracts/python-api.md)
- [CLI Reference](specs/001-llm-model-discovery/contracts/cli-interface.md)

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/drillan/llm-discovery.git
cd llm-discovery

# Install with development dependencies
uv sync --all-extras

# Run tests
pytest

# Run linting
ruff check .

# Run type checking
mypy llm_discovery/
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.
