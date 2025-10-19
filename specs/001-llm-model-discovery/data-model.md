# Data Model: `update`コマンド実装

## Overview

`update`コマンドの実装では、**新規のデータモデル追加は不要**です。既存のデータモデル（`llm_discovery/models/provider.py`、`llm_discovery/services/cache.py`）をそのまま使用し、Article XI（DRY Principle）に準拠します。

## Existing Data Models

### 1. Model (既存)

**Location**: `llm_discovery/models/provider.py`

```python
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

class ModelSource(str, Enum):
    """Source of model information."""
    API = "api"
    MANUAL = "manual"

class Model(BaseModel):
    """Represents an LLM model."""
    model_id: str = Field(..., description="Unique identifier for the model")
    model_name: str = Field(..., description="Human-readable name")
    provider_name: str = Field(..., description="Provider name (e.g., 'openai', 'google', 'anthropic')")
    source: ModelSource = Field(..., description="Source of model data (api/manual)")
    fetched_at: datetime = Field(..., description="Timestamp when model was fetched")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional model metadata")

    model_config = ConfigDict(
        frozen=True,  # Immutable
        str_strip_whitespace=True,
    )
```

**Usage in `update` Command**:
- APIから取得したモデルデータをModelインスタンスとして管理
- `fetch_all_models()`の戻り値として使用

### 2. ProviderSnapshot (既存)

**Location**: `llm_discovery/models/provider.py`

```python
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

class FetchStatus(str, Enum):
    """Status of provider fetch operation."""
    SUCCESS = "success"
    FAILURE = "failure"

class ProviderSnapshot(BaseModel):
    """Snapshot of models from a single provider at a specific point in time."""
    provider_name: str = Field(..., description="Provider name")
    models: list[Model] = Field(default_factory=list, description="List of models from this provider")
    fetch_status: FetchStatus = Field(..., description="Success or failure status")
    fetched_at: datetime = Field(..., description="Timestamp of fetch operation")
    error_message: str | None = Field(None, description="Error message if fetch failed")

    model_config = ConfigDict(
        frozen=True,
        str_strip_whitespace=True,
    )
```

**Usage in `update` Command**:
- `fetch_all_models()`が返すプロバイダー別のスナップショット
- `--detect-changes`オプション使用時にスナップショットとして保存

### 3. Cache (既存)

**Location**: `llm_discovery/services/cache.py`

```python
from datetime import datetime
from pydantic import BaseModel, Field

class CacheMetadata(BaseModel):
    """Metadata for the cache file."""
    version: str = Field(..., description="Cache format version")
    created_at: datetime = Field(..., description="When cache was first created")
    last_updated: datetime = Field(..., description="When cache was last updated")

class Cache(BaseModel):
    """Root cache structure."""
    metadata: CacheMetadata
    providers: list[ProviderSnapshot]
```

**Usage in `update` Command**:
- `CacheService.save_cache(providers)`でTOMLファイルに保存
- キャッシュメタデータ（作成日時、最終更新日時）の管理

### 4. Snapshot (既存)

**Location**: `llm_discovery/models/provider.py`

```python
from uuid import UUID, uuid4
from datetime import datetime
from pydantic import BaseModel, Field

class Snapshot(BaseModel):
    """Complete snapshot of all providers at a specific point in time."""
    snapshot_id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    providers: list[ProviderSnapshot]

    model_config = ConfigDict(
        frozen=True,
    )
```

**Usage in `update --detect-changes`**:
- 変更検知のために前回のスナップショットと比較
- `SnapshotService.save_snapshot(providers)`で保存

### 5. Change (既存)

**Location**: `llm_discovery/models/provider.py`

```python
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

class ChangeType(str, Enum):
    """Type of change detected."""
    ADDED = "added"
    REMOVED = "removed"

class Change(BaseModel):
    """Represents a detected change in model availability."""
    change_type: ChangeType
    model_id: str
    model_name: str
    provider_name: str
    detected_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    model_config = ConfigDict(frozen=True)
```

**Usage in `update --detect-changes`**:
- `ChangeDetector.detect_changes()`が返す変更リスト
- changes.json、CHANGELOG.mdに記録される形式

### 6. Config (既存)

**Location**: `llm_discovery/models/config.py`

```python
from pathlib import Path
from pydantic import BaseModel, Field
from platformdirs import user_cache_dir

class Config(BaseModel):
    """Application configuration."""
    openai_api_key: str | None = Field(None, description="OpenAI API key")
    google_api_key: str | None = Field(None, description="Google AI API key")
    google_genai_use_vertexai: bool = Field(False, description="Use Vertex AI for Google")
    google_application_credentials: str | None = Field(None, description="GCP service account credentials path")
    llm_discovery_cache_dir: Path = Field(
        default_factory=lambda: Path(user_cache_dir("llm-discovery")),
        description="Cache directory path"
    )
    llm_discovery_retention_days: int = Field(30, description="Snapshot retention days")

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        # Implementation uses os.getenv() with Primary Data Non-Assumption Principle
```

**Usage in `update` Command**:
- 環境変数からAPIキー、キャッシュディレクトリ、保持期間を取得
- `Config.from_env()`で初期化

## Data Flow

### `update` Command (Normal Mode)

```
1. Config.from_env()
   ↓
2. DiscoveryService(config)
   ↓
3. await service.fetch_all_models()
   ↓
4. service.save_to_cache(providers: list[ProviderSnapshot])
   ↓
5. CacheService.save_cache(providers)
   ↓
6. Write to models_cache.toml
   ↓
7. Display summary (provider counts, total, cache path)
```

### `update --detect-changes` Command

```
1-6. Same as normal mode
   ↓
7. SnapshotService.list_snapshots()
   ↓
8. If previous snapshot exists:
   - SnapshotService.load_snapshot(previous_id)
   - Snapshot(providers=current_providers)
   - ChangeDetector.detect_changes(previous, current)
   - Display changes (Added/Removed lists)
   - Save to changes.json
   - Update CHANGELOG.md
   - SnapshotService.save_snapshot(providers)
   ↓
9. If no previous snapshot:
   - Save current as baseline
   - Display "No previous snapshot" message
   ↓
10. SnapshotService.cleanup_old_snapshots()
```

### `list` Command (Modified)

```
1. Config.from_env()
   ↓
2. DiscoveryService(config)
   ↓
3. service.get_cached_models() → CacheService.load_cache()
   ↓
   If cache exists:
     4. Display models in table format
   If cache missing:
     4. Display error message (EM-001)
     5. Exit with code 1
```

## Validation Rules

すべてのデータモデルはPydantic v2を使用して以下を保証:

1. **型安全性**: 厳密な型チェック（Python 3.13 + mypy）
2. **Immutability**: `frozen=True`により不変性を保証
3. **デフォルト値**: `Field(default_factory=...)`で安全なデフォルト値
4. **バリデーション**: `@field_validator`でカスタムバリデーション（必要に応じて）
5. **Primary Data Non-Assumption**: 環境変数未設定時はエラーを発生（フォールバック禁止）

## No Schema Changes Required

既存のスキーマ（TOML、JSON、Snapshot形式）は変更不要:

- `models_cache.toml`: 既存のCacheService形式を維持
- `changes.json`: 既存のChange形式を維持
- `CHANGELOG.md`: 既存のChangelogGenerator形式を維持
- `snapshots/*.json`: 既存のSnapshot形式を維持

## Compliance

- ✅ **Article I (Library-First)**: 既存ライブラリのデータモデルを再利用
- ✅ **Article V (Simplicity)**: 新規モデル追加なし、既存構造を維持
- ✅ **Article X (Data Accuracy - C011)**: Pydantic v2の厳密なバリデーション
- ✅ **Article XI (DRY - C012)**: コードの重複なし、既存モデルを活用
- ✅ **Article XIII (No Compromise - C014)**: 理想的な型安全性を最初から確保
