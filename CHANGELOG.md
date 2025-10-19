# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2025-10-19

### Added

#### Core Features
- Real-time model discovery from multiple LLM providers (OpenAI, Google AI Studio/Vertex AI, Anthropic)
- Multi-format export support (JSON, CSV, YAML, Markdown, TOML)
- Automatic change detection and tracking over time
- Snapshot-based versioning with 30-day retention policy
- TOML-based caching for offline mode support
- Python 3.13+ support with modern async/await patterns
- **Prebuilt data support** - Access model information without API keys
  - Remote prebuilt data fetching from GitHub repository
  - HTTP client with timeout strategy (HEAD: 3s, GET: 10s)
  - Comprehensive error handling (HTTPError, URLError, JSONDecodeError)
- **Data source transparency** - Track data origin and freshness
  - Data source type tracking (API/PREBUILT)
  - Data age display with visual warnings (>24h: yellow, >7d: red)
  - Source metadata in all export formats

#### CLI Commands
- `llm-discovery update` - Fetch and cache models from all providers
  - Displays summary: provider counts, total models, and cache path
  - Supports all error handling (API failures, partial failures, authentication errors)
  - Automatically recovers from corrupted cache by fetching fresh data
  - `--detect-changes` option for tracking model additions and removals over time
    - Detects added and removed models since last snapshot
    - Saves changes to `changes.json` and `CHANGELOG.md`
    - Automatically cleans up snapshots older than 30 days
    - Creates baseline snapshot on first run
- `llm-discovery list` - Display cached models (read-only)
  - `--source` option for explicit data source selection (api/prebuilt/auto)
  - Shows data source information with age warnings
  - Clear error message when cache doesn't exist
- `llm-discovery export` - Export model data in multiple formats
  - Supports both API and prebuilt data sources
  - Includes data source metadata in all formats
- Rich terminal output with beautiful tables

#### Python API
- `DiscoveryClient` - Main client for programmatic access
- Five export functions: `export_json`, `export_csv`, `export_yaml`, `export_markdown`, `export_toml`
- Comprehensive type hints and Pydantic models
- Async-first API design for concurrent provider fetching

#### Data Models
- `Model` - Core model entity with validation
- `ProviderSnapshot` - Provider-specific snapshot with fetch status
- `Snapshot` - Complete multi-provider snapshot with UUID tracking
- `Change` - Model change record for version tracking
- `Cache` - TOML-based cache structure with metadata
- `CacheMetadata` - Extended with data source tracking (v1.0.0 → v1.1.0)
  - `data_source_type` - Tracks API or PREBUILT origin
  - `data_source_timestamp` - Records when data was fetched
  - Backward compatible with optional fields
- `DataSourceInfo` - Data source information with computed age

#### Services
- `DiscoveryService` - Orchestrates parallel provider fetching with fail-fast error handling
- `CacheService` - TOML-based persistence with automatic metadata management
- `SnapshotService` - UUID-based snapshot management with retention policy
- `ChangeDetector` - Detects model additions and removals between snapshots
- `ChangelogGenerator` - Generates human-readable Markdown changelogs
- `PrebuiltDataService` - Fetches prebuilt model data from remote repository
  - HTTP client with timeout strategy
  - Automatic validation and error handling

#### Provider Support
- **OpenAI**: Full API integration with model metadata
- **Google**: Dual backend support (AI Studio and Vertex AI)
- **Anthropic**: Manual model data (Claude Sonnet 4.5, Haiku 4.5, Opus 4.1)

#### Configuration
- Environment variable-based configuration
- Support for multiple Google backends (AI Studio / Vertex AI)
- Configurable cache directory and retention policy
- Automatic cache directory creation with permission validation

#### Testing & Quality
- 90.22% test coverage (84 tests, all passing)
- Comprehensive unit, integration, and CLI tests
- Strict mypy type checking (zero errors)
- Ruff linting with project-specific rules

#### Documentation
- Comprehensive README with quickstart examples
- Example scripts in `examples/` directory
- API reference contracts
- CLI interface documentation
- **Sphinx documentation system** (docs/)
  - Installation guide, quickstart, and tutorials
  - Complete CLI and API reference
  - Advanced guides and troubleshooting
  - Architecture and design documentation
  - Built with Sphinx 8.0+, myst-parser 4.0+, sphinx_rtd_theme 3.0+

### Technical Details

#### Architecture
- Fail-fast error handling with partial failure detection
- UTC-first datetime handling (Python 3.13 `datetime.UTC`)
- Immutable Pydantic models with frozen configuration
- Primary Data Non-Assumption Principle compliance

#### Dependencies
- Python 3.13+
- Typer for CLI framework
- Rich for terminal output
- Pydantic v2 for data validation
- OpenAI, Google GenAI, and Google Cloud AI Platform SDKs
- TOML support via tomllib (built-in) and tomli-w

#### Performance
- Async parallel fetching from all providers
- Cache-first operation for offline usage
- Efficient TOML serialization

### Changed

- **BREAKING CHANGE**: `list` command is now read-only (cache display only)
  - No longer fetches from APIs automatically
  - Shows clear error message when cache doesn't exist: "No cached data available. Please run 'llm-discovery update' first to fetch model data."
  - Requires running `update` command first to populate cache
  - New `--source` option for explicit data source selection (api/prebuilt/auto)

### Migration Guide

If you were using `llm-discovery list` to fetch and display models:

```bash
# Old workflow
llm-discovery list

# New workflow
llm-discovery update  # Fetch and cache models
llm-discovery list    # Display cached models

# Or use prebuilt data (no API keys required)
llm-discovery list --source prebuilt
```

### Known Limitations

- Google Vertex AI requires GCP service account credentials
- Anthropic models use manual data (no official API yet)
- Change detection requires at least one previous snapshot
- Prebuilt data may not include the latest models (updated periodically)

[0.1.0]: https://github.com/drillan/llm-discovery/releases/tag/v0.1.0
