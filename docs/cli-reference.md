---
title: CLI Reference
description: Complete command-line interface reference for llm-discovery
---

# CLI Reference

Complete reference for the `llm-discovery` command-line interface.

## Global Command Structure

```bash
llm-discovery [GLOBAL_OPTIONS] [COMMAND] [COMMAND_OPTIONS]
```

## Global Options

### --version

Display package version information.

```bash
llm-discovery --version
```

**Output Format**:

```
llm-discovery, version 0.1.0
```

The version is dynamically retrieved from package metadata using `importlib.metadata`. No hardcoded version fallbacks are used.

:::{important}
All API keys and credentials must be set as environment variables before running commands.
Never pass API keys as command-line arguments.
:::

### --help

Display help message with available commands and options.

```bash
llm-discovery --help
```

## Commands

### update

Fetch models from all providers and update the local cache.

**Syntax**:

```bash
llm-discovery update [OPTIONS]
```

**Options**:

- `--detect-changes`: Detect and report model additions/removals from previous snapshot

**Behavior**:

**Normal execution** (`llm-discovery update`):
- Fetch models from all configured providers concurrently
- Save results to local cache (`~/.cache/llm-discovery/`)
- Display summary of fetched models

**With change detection** (`llm-discovery update --detect-changes`):
- Fetch models from all providers
- Compare with previous snapshot
- Detect new and removed models
- Generate `changes.json` and `CHANGELOG.md`
- Save current snapshot for future comparisons

**Example Output (Normal)**:

```
✓ Fetched models from all providers

Provider  | Model Count | Status
----------|-------------|--------
openai    | 15          | ✓
google    | 12          | ✓
anthropic | 8           | ✓

Total: 35 models
Cache updated: ~/.cache/llm-discovery/models.toml
```

**Example Output (Change Detection - Changes Found)**:

```
Changes detected!

Added models (3):
  openai/gpt-5
  google/gemini-2.0-pro
  anthropic/claude-3.5-opus

Removed models (1):
  openai/gpt-3.5-turbo-0301

Changes recorded in:
  - ~/.cache/llm-discovery/changes.json
  - ~/.cache/llm-discovery/CHANGELOG.md
```

**Example Output (Change Detection - First Run)**:

```
No previous snapshot found. Saving current state as baseline.
Next run with --detect-changes will detect changes from this baseline.

Snapshot ID: 550e8400-e29b-41d4-a716-446655440000
```

:::{warning}
Rate limits apply to API calls. For CI/CD environments, use caching strategies to minimize API calls.
Recommended: Run `update` once per hour or less frequently.
:::

**Error Handling**:

```bash
# API failure example
Error: Failed to fetch models from OpenAI API.

Provider: openai
Cause: Connection timeout (10 seconds)

Suggested actions:
  1. Check your internet connection
  2. Verify OPENAI_API_KEY is set correctly
  3. Check OpenAI status: https://status.openai.com/
  4. Retry the command later

Exit code: 1
```

```bash
# Partial failure example
Error: Partial failure during model fetch.

Successful providers:
  - openai (15 models)
  - anthropic (8 models)

Failed providers:
  - google (Connection refused)

To ensure data consistency, processing has been aborted.
Please resolve the issue with the failed provider and retry.

Exit code: 1
```

### list

Display cached models in a formatted table.

**Syntax**:

```bash
llm-discovery list
```

**Behavior**:

- Read models from local cache
- Display in formatted table using Rich library
- No API calls (offline operation)

**Example Output (Table Format)**:

```
Provider  | Model ID         | Model Name       | Source | Fetched At
----------|------------------|------------------|--------|-------------------
openai    | gpt-4-turbo      | GPT-4 Turbo     | API    | 2025-10-19 12:00
openai    | gpt-4            | GPT-4           | API    | 2025-10-19 12:00
google    | gemini-1.5-pro   | Gemini 1.5 Pro  | API    | 2025-10-19 12:00
google    | gemini-1.5-flash | Gemini 1.5 Flash| API    | 2025-10-19 12:00
anthropic | claude-3-opus    | Claude 3 Opus   | API    | 2025-10-19 12:00

Total: 35 models
Cache: ~/.cache/llm-discovery/models.toml
```

**Error Handling**:

```bash
# Cache not found
Error: Cache file not found.

Location: ~/.cache/llm-discovery/models.toml

Please run the update command first to fetch models from APIs:
  llm-discovery update

Exit code: 1
```

```bash
# Cache corrupted
Error: Cache file is corrupted.

Location: ~/.cache/llm-discovery/models.toml
Cause: TOML parse error at line 15

Please delete the cache and run update to fetch fresh data:
  rm -rf ~/.cache/llm-discovery/
  llm-discovery update

Exit code: 1
```

### export

Export models to various formats (JSON, CSV, YAML, Markdown, TOML).

**Syntax**:

```bash
llm-discovery export --format FORMAT [--output FILE]
```

**Options**:

- `--format FORMAT`: Output format (required)
  - Choices: `json`, `csv`, `yaml`, `markdown`, `toml`
- `--output FILE`: Output file path (optional)
  - Default: stdout

**Example: JSON Export**

```bash
llm-discovery export --format json --output models.json
```

**JSON Output Format**:

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
    },
    {
      "model_id": "gemini-1.5-pro",
      "model_name": "Gemini 1.5 Pro",
      "provider_name": "google",
      "source": "API",
      "fetched_at": "2025-10-19T12:00:00Z",
      "capabilities": ["chat", "vision"]
    }
  ],
  "metadata": {
    "total_count": 35,
    "fetched_at": "2025-10-19T12:00:00Z",
    "export_format": "json"
  }
}
```

**Example: CSV Export**

```bash
llm-discovery export --format csv --output models.csv
```

**CSV Output Format**:

```
provider_name,model_id,model_name,source,fetched_at,capabilities
openai,gpt-4,GPT-4,API,2025-10-19T12:00:00Z,"chat,completion"
google,gemini-1.5-pro,Gemini 1.5 Pro,API,2025-10-19T12:00:00Z,"chat,vision"
```

**Example: YAML Export**

```bash
llm-discovery export --format yaml --output models.yaml
```

**YAML Output Format**:

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
  - model_id: gemini-1.5-pro
    model_name: Gemini 1.5 Pro
    provider_name: google
    source: API
    fetched_at: '2025-10-19T12:00:00Z'
    capabilities:
      - chat
      - vision
metadata:
  total_count: 35
  fetched_at: '2025-10-19T12:00:00Z'
  export_format: yaml
```

**Example: Markdown Export**

```bash
llm-discovery export --format markdown --output models.md
```

**Markdown Output Format**:

```markdown
# LLM Models

Total: 35 models

| Provider | Model ID | Model Name | Source | Fetched At | Capabilities |
|----------|----------|------------|--------|------------|--------------|
| openai | gpt-4 | GPT-4 | API | 2025-10-19T12:00:00Z | chat, completion |
| google | gemini-1.5-pro | Gemini 1.5 Pro | API | 2025-10-19T12:00:00Z | chat, vision |
```

**Example: TOML Export**

```bash
llm-discovery export --format toml --output models.toml
```

**TOML Output Format**:

```toml
[[models]]
model_id = "gpt-4"
model_name = "GPT-4"
provider_name = "openai"
source = "API"
fetched_at = "2025-10-19T12:00:00Z"
capabilities = ["chat", "completion"]

[[models]]
model_id = "gemini-1.5-pro"
model_name = "Gemini 1.5 Pro"
provider_name = "google"
source = "API"
fetched_at = "2025-10-19T12:00:00Z"
capabilities = ["chat", "vision"]

[metadata]
total_count = 35
fetched_at = "2025-10-19T12:00:00Z"
export_format = "toml"
```

**Example: Output to stdout**

```bash
llm-discovery export --format json | jq '.models[] | select(.provider_name == "openai")'
```

**Error Handling**:

```bash
# Invalid format
Error: Invalid export format: 'xml'

Supported formats:
  - json
  - csv
  - yaml
  - markdown
  - toml

Example:
  llm-discovery export --format json --output models.json

Exit code: 1
```

## Environment Variables

:::{important}
All environment variables containing sensitive credentials must be set before running commands.
Never commit API keys to version control.
:::

### Required Environment Variables

At least one provider API key must be configured:

**OpenAI**:
```bash
export OPENAI_API_KEY="sk-..."
```

**Google AI Studio**:
```bash
export GOOGLE_API_KEY="AIza..."
```

**Google Vertex AI** (alternative to AI Studio):
```bash
export GOOGLE_GENAI_USE_VERTEXAI=true
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

### Optional Environment Variables

**Cache Directory**:
```bash
export LLM_DISCOVERY_CACHE_DIR="/custom/cache/path"
```

Default: `~/.cache/llm-discovery`

## Exit Codes

llm-discovery follows standard Unix exit code conventions:

- `0`: Success
- `1`: General error (API failure, configuration error, etc.)
- `2`: Command-line usage error (invalid arguments)

**Example Usage in Scripts**:

```bash
#!/bin/bash

# Update models and check exit code
llm-discovery update
if [ $? -eq 0 ]; then
    echo "✓ Models updated successfully"
    llm-discovery export --format json --output /var/www/models.json
else
    echo "✗ Failed to update models"
    exit 1
fi
```

## CI/CD Integration Examples

### GitHub Actions

```yaml
name: Update LLM Models

on:
  schedule:
    - cron: '0 */6 * * *'  # Every 6 hours
  workflow_dispatch:

jobs:
  update-models:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.13'

      - name: Install llm-discovery
        run: pip install llm-discovery

      - name: Update models
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
        run: |
          llm-discovery update --detect-changes
          llm-discovery export --format json --output models.json

      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: models
          path: models.json
```

### GitLab CI

```yaml
update-models:
  image: python:3.13
  script:
    - pip install llm-discovery
    - llm-discovery update --detect-changes
    - llm-discovery export --format json --output models.json
  artifacts:
    paths:
      - models.json
  schedule:
    - cron: '0 */6 * * *'
  variables:
    OPENAI_API_KEY: $OPENAI_API_KEY
    GOOGLE_API_KEY: $GOOGLE_API_KEY
```

## Complete Workflow Example

```bash
# 1. Set up environment variables
export OPENAI_API_KEY="sk-..."
export GOOGLE_API_KEY="AIza..."

# 2. Fetch and cache models
llm-discovery update

# 3. Display cached models
llm-discovery list

# 4. Export to multiple formats
llm-discovery export --format json --output models.json
llm-discovery export --format csv --output models.csv
llm-discovery export --format markdown --output models.md

# 5. Check for changes (run daily in cron)
llm-discovery update --detect-changes

# 6. View change log
cat ~/.cache/llm-discovery/CHANGELOG.md
```

## Troubleshooting

### Cache Location

View cache location:
```bash
echo $LLM_DISCOVERY_CACHE_DIR  # If set
# Or default: ~/.cache/llm-discovery
```

Clear cache:
```bash
rm -rf ~/.cache/llm-discovery/
```

### Verbose Output

For debugging, use Python's logging:
```bash
PYTHONLOGLEVEL=DEBUG llm-discovery update
```

### Common Issues

**Issue**: `OPENAI_API_KEY not set`
```bash
Error: Required environment variable not set: OPENAI_API_KEY

Please set your OpenAI API key:
  export OPENAI_API_KEY="sk-..."

To obtain an API key, visit: https://platform.openai.com/api-keys
```

**Solution**: Set the environment variable as shown.

**Issue**: `Connection timeout`
```bash
Error: Failed to fetch models from OpenAI API.
Cause: Connection timeout (10 seconds)
```

**Solution**:
1. Check internet connection
2. Check provider status page
3. Retry after a few minutes

## Next Steps

- **Python API**: See technical contract at `specs/001-llm-model-discovery/contracts/python-api.md`
- **Error Handling**: See `specs/001-llm-model-discovery/contracts/error-handling.md`
- **Contributing**: See `CONTRIBUTING.md` in the repository root
