---
title: Installation
description: Installation guide for llm-discovery
---

# Installation

llm-discovery can be installed using multiple methods. Choose the one that best fits your workflow.

## Method 1: uvx (Recommended)

The simplest way to use llm-discovery without installation.

```bash
# Fetch and cache models
uvx llm-discovery update

# Display cached models
uvx llm-discovery list
```

:::{tip}
Using `uvx` requires no installation and automatically manages dependencies.
Each invocation runs the latest version of llm-discovery.
:::

## Method 2: pip

Install llm-discovery as a Python package.

```bash
pip install llm-discovery
```

After installation, the `llm-discovery` command will be available in your environment.

```bash
# Verify installation
llm-discovery --version

# Use the tool
llm-discovery update
llm-discovery list
```

## Method 3: From Source

For development or customization, install from source.

```bash
# Clone the repository
git clone https://github.com/drillan/llm-discovery.git
cd llm-discovery

# Install for general use
uv sync

# Or install with documentation dependencies (if you want to build docs)
uv sync --extra docs

# Or install with development dependencies (for contributors)
uv sync --all-extras --all-groups

# Run the tool
uv run llm-discovery update
```

:::{note}
Source installation is recommended for contributors and developers who need to modify the code.
See the Contributing Guide (`CONTRIBUTING.md` in the repository root) for more details.
:::

## Requirements

- Python 3.13 or higher
- Internet connection for initial model fetching
- API keys for desired LLM providers (see [Quick Start](quickstart.md))

## Versioning

llm-discovery follows [Semantic Versioning 2.0.0](https://semver.org/):

- **MAJOR**: Backward-incompatible changes
- **MINOR**: Backward-compatible feature additions
- **PATCH**: Backward-compatible bug fixes

Check your installed version:

```bash
llm-discovery --version
```

Expected output format:

```
llm-discovery, version 0.1.0
```

:::{important}
The version is dynamically retrieved from the package metadata.
If you encounter version-related errors, verify the package is correctly installed.
:::

## Next Steps

After installation, proceed to the [Quick Start Guide](quickstart.md) to set up API keys and run your first commands.
