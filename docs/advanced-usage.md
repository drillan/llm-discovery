---
title: Advanced Usage
description: Advanced usage patterns, CI/CD integration, and provider filtering
---

# Advanced Usage

Advanced patterns for using llm-discovery in production environments.

## CI/CD Integration

### GitHub Actions

Complete workflow for fetching and exporting models on a schedule.

```yaml
name: Update LLM Models

on:
  schedule:
    # Run every 6 hours
    - cron: '0 */6 * * *'
  workflow_dispatch:  # Allow manual triggers

jobs:
  update-models:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.13'

      - name: Install llm-discovery
        run: pip install llm-discovery

      - name: Fetch models from all providers
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
        run: |
          llm-discovery update --detect-changes

      - name: Export to multiple formats
        run: |
          mkdir -p exports
          llm-discovery export --format json --output exports/models.json
          llm-discovery export --format csv --output exports/models.csv
          llm-discovery export --format markdown --output exports/models.md

      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: llm-models
          path: exports/
          retention-days: 30

      - name: Commit changes (if any)
        run: |
          git config user.name "GitHub Actions"
          git config user.email "actions@github.com"
          git add exports/
          git diff --quiet && git diff --staged --quiet || \
            (git commit -m "chore: update LLM model data [skip ci]" && git push)
```

:::{tip}
Use GitHub Actions secrets to store API keys securely.
Never commit API keys directly to the repository.
:::

### GitLab CI

GitLab CI pipeline for model updates.

```yaml
stages:
  - fetch
  - export

variables:
  PYTHON_VERSION: "3.13"

fetch-models:
  stage: fetch
  image: python:${PYTHON_VERSION}
  script:
    - pip install llm-discovery
    - llm-discovery update --detect-changes
  artifacts:
    paths:
      - ~/.cache/llm-discovery/
    expire_in: 1 day
  only:
    - schedules
  variables:
    OPENAI_API_KEY: $OPENAI_API_KEY
    GOOGLE_API_KEY: $GOOGLE_API_KEY

export-models:
  stage: export
  image: python:${PYTHON_VERSION}
  dependencies:
    - fetch-models
  script:
    - pip install llm-discovery
    - mkdir -p exports
    - llm-discovery export --format json --output exports/models.json
    - llm-discovery export --format csv --output exports/models.csv
  artifacts:
    paths:
      - exports/
    expire_in: 30 days
  only:
    - schedules
```

**Schedule Configuration** (GitLab UI):
- Go to CI/CD → Schedules
- Add new schedule: `0 */6 * * *` (every 6 hours)
- Set variables: `OPENAI_API_KEY`, `GOOGLE_API_KEY`

## Provider Filtering

Filter models by provider using Python API.

### Filter by Single Provider

```python
import asyncio
from llm_discovery import DiscoveryClient

async def fetch_openai_only():
    client = DiscoveryClient()
    all_models = await client.fetch_models()

    # Filter OpenAI models only
    openai_models = [
        model for model in all_models
        if model.provider_name == "openai"
    ]

    print(f"OpenAI models: {len(openai_models)}")
    for model in openai_models:
        print(f"  {model.model_id}: {model.model_name}")

asyncio.run(fetch_openai_only())
```

### Filter by Multiple Providers

```python
import asyncio
from llm_discovery import DiscoveryClient

async def fetch_specific_providers():
    client = DiscoveryClient()
    all_models = await client.fetch_models()

    # Filter by provider list
    allowed_providers = {"openai", "google"}
    filtered_models = [
        model for model in all_models
        if model.provider_name in allowed_providers
    ]

    # Group by provider
    by_provider = {}
    for model in filtered_models:
        if model.provider_name not in by_provider:
            by_provider[model.provider_name] = []
        by_provider[model.provider_name].append(model)

    # Display results
    for provider, models in by_provider.items():
        print(f"\n{provider}: {len(models)} models")
        for model in models:
            print(f"  {model.model_id}")

asyncio.run(fetch_specific_providers())
```

### Filter by Capabilities

```python
import asyncio
from llm_discovery import DiscoveryClient

async def fetch_chat_models():
    client = DiscoveryClient()
    all_models = await client.fetch_models()

    # Filter models with chat capability
    chat_models = [
        model for model in all_models
        if "chat" in model.capabilities
    ]

    print(f"Chat-capable models: {len(chat_models)}")
    for model in chat_models:
        print(f"  {model.provider_name}/{model.model_id}")
        print(f"    Capabilities: {', '.join(model.capabilities)}")

asyncio.run(fetch_chat_models())
```

## Custom Error Handling

Implement custom error handling for production use.

### Retry Logic with Exponential Backoff

```python
import asyncio
import time
from llm_discovery import DiscoveryClient
from llm_discovery.exceptions import ProviderFetchError, NetworkError

async def fetch_with_retry(max_retries=3, base_delay=1):
    client = DiscoveryClient()

    for attempt in range(max_retries):
        try:
            models = await client.fetch_models()
            print(f"✓ Successfully fetched {len(models)} models")
            return models

        except NetworkError as e:
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)  # Exponential backoff
                print(f"✗ Network error on attempt {attempt + 1}/{max_retries}")
                print(f"  Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                print(f"✗ Failed after {max_retries} attempts")
                raise

        except ProviderFetchError as e:
            print(f"✗ Provider fetch error: {e}")
            raise

asyncio.run(fetch_with_retry())
```

### Fallback to Cache on API Failure

```python
import asyncio
from llm_discovery import DiscoveryClient
from llm_discovery.exceptions import (
    ProviderFetchError,
    CacheNotFoundError
)

async def fetch_with_cache_fallback():
    client = DiscoveryClient()

    try:
        # Try fetching from APIs
        models = await client.fetch_models()
        print(f"✓ Fetched {len(models)} models from APIs")
        return models

    except ProviderFetchError as e:
        print(f"✗ API fetch failed: {e}")
        print("  Attempting to load from cache...")

        try:
            models = client.get_cached_models()
            print(f"✓ Loaded {len(models)} models from cache")
            print("  (Note: Data may be outdated)")
            return models

        except CacheNotFoundError:
            print("✗ No cache available")
            print("  Cannot proceed without data")
            raise

asyncio.run(fetch_with_cache_fallback())
```

### Partial Success Handling

```python
import asyncio
from llm_discovery import DiscoveryClient
from llm_discovery.exceptions import PartialFetchError

async def handle_partial_failure():
    client = DiscoveryClient()

    try:
        models = await client.fetch_models()
        print(f"✓ All providers successful: {len(models)} models")

    except PartialFetchError as e:
        print(f"⚠ Partial failure detected")
        print(f"  Successful: {', '.join(e.successful_providers)}")
        print(f"  Failed: {', '.join(e.failed_providers)}")

        # Decision: Accept partial data or abort?
        if len(e.successful_providers) >= 2:
            print("  Proceeding with partial data (2+ providers successful)")
            # Use e.models for partial data if needed
        else:
            print("  Aborting (less than 2 providers successful)")
            raise

asyncio.run(handle_partial_failure())
```

## Google Vertex AI Setup

Configure Google Vertex AI for production environments.

### Prerequisites

1. **Create GCP Project**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create new project or select existing project

2. **Enable Vertex AI API**:
   ```bash
   gcloud services enable aiplatform.googleapis.com
   ```

3. **Create Service Account**:
   ```bash
   gcloud iam service-accounts create llm-discovery-sa \
     --display-name="LLM Discovery Service Account"
   ```

4. **Grant Permissions**:
   ```bash
   gcloud projects add-iam-policy-binding PROJECT_ID \
     --member="serviceAccount:llm-discovery-sa@PROJECT_ID.iam.gserviceaccount.com" \
     --role="roles/aiplatform.user"
   ```

5. **Download Service Account Key**:
   ```bash
   gcloud iam service-accounts keys create ~/llm-discovery-key.json \
     --iam-account=llm-discovery-sa@PROJECT_ID.iam.gserviceaccount.com
   ```

### Environment Configuration

**Local Development**:

```bash
export GOOGLE_GENAI_USE_VERTEXAI=true
export GOOGLE_APPLICATION_CREDENTIALS="$HOME/llm-discovery-key.json"
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_CLOUD_LOCATION="us-central1"
```

**GitHub Actions**:

```yaml
- name: Setup Google Cloud credentials
  env:
    GCP_SA_KEY: ${{ secrets.GCP_SA_KEY }}
  run: |
    echo "$GCP_SA_KEY" > $HOME/gcp-key.json
    export GOOGLE_APPLICATION_CREDENTIALS="$HOME/gcp-key.json"
    export GOOGLE_GENAI_USE_VERTEXAI=true

- name: Fetch models
  run: llm-discovery update
```

**GitLab CI**:

```yaml
variables:
  GOOGLE_GENAI_USE_VERTEXAI: "true"
  GOOGLE_APPLICATION_CREDENTIALS: "/tmp/gcp-key.json"

before_script:
  - echo "$GCP_SA_KEY" > /tmp/gcp-key.json
```

:::{caution}
Service account keys are sensitive credentials.
Store them securely using CI/CD secret management.
Never commit service account keys to version control.
:::

### Verify Setup

```python
import asyncio
from llm_discovery import DiscoveryClient
from llm_discovery.models.config import Config

async def verify_vertexai():
    # Verify configuration
    config = Config.from_env()
    print(f"Vertex AI enabled: {config.google_genai_use_vertexai}")
    print(f"Credentials path: {config.google_application_credentials}")

    # Fetch models
    client = DiscoveryClient(config=config)
    try:
        models = await client.fetch_models()
        google_models = [m for m in models if m.provider_name == "google"]
        print(f"✓ Successfully fetched {len(google_models)} Google models")
    except Exception as e:
        print(f"✗ Vertex AI setup error: {e}")
        raise

asyncio.run(verify_vertexai())
```

## Production Deployment Checklist

- [ ] API keys stored in secure secret management (not in code)
- [ ] Rate limiting configured (max 1 request per minute per provider)
- [ ] Caching strategy implemented (update every 6-24 hours)
- [ ] Error monitoring and alerting configured
- [ ] Retry logic with exponential backoff implemented
- [ ] Fallback to cache on API failure tested
- [ ] CI/CD pipeline tested in staging environment
- [ ] Log aggregation configured for debugging
- [ ] Backup strategy for cache data defined
- [ ] Documentation for runbook procedures created

## Performance Optimization

### Minimize API Calls

```python
import asyncio
from llm_discovery import DiscoveryClient

async def optimize_api_calls():
    client = DiscoveryClient()

    # Fetch once, use multiple times
    models = await client.fetch_models()

    # Filter without additional API calls
    openai_models = [m for m in models if m.provider_name == "openai"]
    google_models = [m for m in models if m.provider_name == "google"]
    chat_models = [m for m in models if "chat" in m.capabilities]

    # Export to multiple formats from same data
    from llm_discovery.services.exporters import (
        JSONExporter, CSVExporter, MarkdownExporter
    )

    json_exporter = JSONExporter()
    csv_exporter = CSVExporter()
    md_exporter = MarkdownExporter()

    json_data = json_exporter.export(models)
    csv_data = csv_exporter.export(models)
    md_data = md_exporter.export(models)

    # Save all formats
    with open("models.json", "w") as f:
        f.write(json_data)
    with open("models.csv", "w") as f:
        f.write(csv_data)
    with open("models.md", "w") as f:
        f.write(md_data)

    print("✓ Exported to 3 formats from single API call")

asyncio.run(optimize_api_calls())
```

### Cache Management

```python
from pathlib import Path
import shutil

def manage_cache():
    cache_dir = Path.home() / ".cache" / "llm-discovery"

    # Check cache size
    if cache_dir.exists():
        cache_size = sum(f.stat().st_size for f in cache_dir.rglob('*') if f.is_file())
        print(f"Cache size: {cache_size / 1024:.2f} KB")

    # Clear old snapshots (keep last 30 days)
    snapshots_dir = cache_dir / "snapshots"
    if snapshots_dir.exists():
        from datetime import datetime, timedelta, UTC
        cutoff = datetime.now(UTC) - timedelta(days=30)

        for snapshot in snapshots_dir.glob("*.toml"):
            if snapshot.stat().st_mtime < cutoff.timestamp():
                snapshot.unlink()
                print(f"Deleted old snapshot: {snapshot.name}")

manage_cache()
```

## Next Steps

- **Troubleshooting**: See [Troubleshooting Guide](troubleshooting.md)
- **API Reference**: See [Python API Reference](api-reference.md)
- **CLI Reference**: See [CLI Reference](cli-reference.md)
