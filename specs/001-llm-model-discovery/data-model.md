# Data Model: LLMモデル発見・追跡システム

**Feature**: [spec.md](./spec.md)
**Research**: [research.md](./research.md)

## Overview

このドキュメントは、LLMモデル発見・追跡システムのデータモデルを定義します。すべてのモデルはPydantic v2を使用して実装され、型安全性、厳格なバリデーション、Primary Data Non-Assumption Principleへの準拠を保証します。

主要なエンティティは以下の通りです：

- **Model**: LLMプロバイダーが提供する機械学習モデルの表現
- **Provider**: LLMサービスを提供する企業（OpenAI、Google、Anthropic）
- **Snapshot**: 特定時点でのモデル一覧の記録
- **Change**: スナップショット間のモデル差分情報
- **Cache**: オフライン動作を可能にするローカルストレージ
- **Config**: 環境変数とシステム設定の管理

## Entities

### Model（モデル）

**Purpose**: LLMプロバイダーが提供する個別の機械学習モデルを表現します。各モデルは一意のIDで識別され、取得方法（API/手動）とタイムスタンプを含むメタデータを保持します。

**Pydantic Model**:

```python
from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime
from typing import Literal, Optional
from enum import Enum


class ModelSource(str, Enum):
    """モデル情報の取得方法"""
    API = "api"
    MANUAL = "manual"


class Model(BaseModel):
    """
    LLMモデルのデータモデル

    Attributes:
        model_id: 一意識別子（プロバイダー内でユニーク）
        model_name: モデルの表示名
        provider_name: プロバイダー名（openai/google/anthropic）
        source: 取得方法（api/manual）
        fetched_at: 取得タイムスタンプ
        metadata: 追加メタデータ（機能、制限事項等）
    """
    model_config = ConfigDict(frozen=True)  # 不変性保証

    model_id: str = Field(..., description="一意識別子（例: gpt-4-turbo）")
    model_name: str = Field(..., description="表示名（例: GPT-4 Turbo）")
    provider_name: Literal["openai", "google", "anthropic"] = Field(
        ...,
        description="プロバイダー名"
    )
    source: ModelSource = Field(..., description="取得方法（api/manual）")
    fetched_at: datetime = Field(
        default_factory=datetime.now,
        description="取得タイムスタンプ"
    )
    metadata: dict[str, str | int | float | bool] = Field(
        default_factory=dict,
        description="追加メタデータ（context_window、pricing等）"
    )

    @field_validator("model_id")
    @classmethod
    def validate_model_id(cls, v: str) -> str:
        """モデルIDの検証：空文字列禁止、空白の正規化"""
        if not v or not v.strip():
            raise ValueError("model_id cannot be empty or whitespace")
        return v.strip()

    @field_validator("model_name")
    @classmethod
    def validate_model_name(cls, v: str) -> str:
        """モデル名の検証：空文字列禁止"""
        if not v or not v.strip():
            raise ValueError("model_name cannot be empty or whitespace")
        return v.strip()
```

**Relationships**:
- `Provider`に所属（多対一）
- `Snapshot`に含まれる（多対多）
- `Change`で参照される（一対多）

**Validation Rules**:
- `model_id`と`model_name`は空文字列禁止
- `provider_name`は列挙型で厳密に制限
- `fetched_at`は自動生成（デフォルトで現在時刻）
- `metadata`は辞書型で柔軟な拡張性を提供

**State Transitions**:
- 不変（`frozen=True`）- 作成後の変更不可
- 新しい情報が取得された場合は新しい`Model`インスタンスを作成

---

### Provider（プロバイダー）

**Purpose**: LLMサービスを提供する企業を表現します。プロバイダーはAPIエンドポイント、取得方式、サポートするモデルのリストを管理します。

**Pydantic Model**:

```python
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from typing import Literal, Optional
from enum import Enum


class ProviderType(str, Enum):
    """プロバイダーの種類"""
    OPENAI = "openai"
    GOOGLE = "google"
    ANTHROPIC = "anthropic"


class GoogleBackend(str, Enum):
    """Googleプロバイダーのバックエンド"""
    AI_STUDIO = "ai_studio"
    VERTEX_AI = "vertex_ai"


class Provider(BaseModel):
    """
    LLMプロバイダーのデータモデル

    Attributes:
        name: プロバイダー名
        api_endpoint: APIエンドポイントURL（該当する場合）
        fetch_method: 取得方式（api/manual）
        supported_models: サポートされるモデルのリスト
        google_backend: Googleプロバイダーのバックエンド（Google専用）
    """
    model_config = ConfigDict(frozen=True)

    name: ProviderType = Field(..., description="プロバイダー名")
    api_endpoint: Optional[str] = Field(
        None,
        description="APIエンドポイントURL（API取得の場合）"
    )
    fetch_method: ModelSource = Field(..., description="取得方式（api/manual）")
    supported_models: list[str] = Field(
        default_factory=list,
        description="サポートされるモデルIDのリスト"
    )
    google_backend: Optional[GoogleBackend] = Field(
        None,
        description="Googleプロバイダーのバックエンド（Google専用）"
    )

    @field_validator("api_endpoint")
    @classmethod
    def validate_api_endpoint(cls, v: Optional[str]) -> Optional[str]:
        """APIエンドポイントの検証：HTTPSスキーム推奨"""
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("api_endpoint cannot be empty string")
        if not v.startswith(("http://", "https://")):
            raise ValueError("api_endpoint must start with http:// or https://")
        return v

    @model_validator(mode='after')
    def validate_google_backend(self) -> 'Provider':
        """Googleプロバイダーの場合、バックエンド指定を検証"""
        if self.name == ProviderType.GOOGLE and self.google_backend is None:
            raise ValueError(
                "google_backend must be specified for Google provider "
                "(ai_studio or vertex_ai)"
            )
        if self.name != ProviderType.GOOGLE and self.google_backend is not None:
            raise ValueError(
                "google_backend should only be set for Google provider"
            )
        return self

    @model_validator(mode='after')
    def validate_api_consistency(self) -> 'Provider':
        """API取得方式の場合、エンドポイント必須"""
        if self.fetch_method == ModelSource.API and not self.api_endpoint:
            raise ValueError(
                "api_endpoint is required when fetch_method is 'api'"
            )
        return self
```

**Relationships**:
- `Model`を所有（一対多）
- `Snapshot`で使用される（多対多）

**Validation Rules**:
- Googleプロバイダーは`google_backend`が必須
- API取得方式の場合は`api_endpoint`が必須
- APIエンドポイントはHTTP/HTTPSスキーム必須

**State Transitions**: 不変（`frozen=True`）

---

### Snapshot（スナップショット）

**Purpose**: 特定時点でのモデル一覧の記録を表現します。スナップショット間の比較により、モデルの追加・削除を検出できます。

**Pydantic Model**:

```python
from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime
from typing import Optional
import uuid


class FetchStatus(str, Enum):
    """取得ステータス"""
    SUCCESS = "success"
    PARTIAL_FAILURE = "partial_failure"
    FAILURE = "failure"


class ProviderSnapshot(BaseModel):
    """
    プロバイダー別のスナップショット情報

    Attributes:
        provider_name: プロバイダー名
        models: モデルIDのリスト
        fetch_status: 取得ステータス
        error_message: エラーメッセージ（失敗時のみ）
    """
    provider_name: str = Field(..., description="プロバイダー名")
    models: list[str] = Field(
        default_factory=list,
        description="モデルIDのリスト"
    )
    fetch_status: FetchStatus = Field(..., description="取得ステータス")
    error_message: Optional[str] = Field(
        None,
        description="エラーメッセージ（失敗時のみ）"
    )


class Snapshot(BaseModel):
    """
    モデル一覧のスナップショット

    Attributes:
        snapshot_id: スナップショットの一意識別子（UUID）
        created_at: 作成日時
        providers: プロバイダー別のスナップショット情報
        overall_status: 全体の取得ステータス
    """
    model_config = ConfigDict(frozen=True)

    snapshot_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="スナップショットID（UUID）"
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="作成日時"
    )
    providers: dict[str, ProviderSnapshot] = Field(
        ...,
        description="プロバイダー別のスナップショット情報"
    )
    overall_status: FetchStatus = Field(..., description="全体の取得ステータス")

    @field_validator("snapshot_id")
    @classmethod
    def validate_snapshot_id(cls, v: str) -> str:
        """スナップショットIDの検証：UUID形式"""
        try:
            uuid.UUID(v)
        except ValueError as e:
            raise ValueError(f"snapshot_id must be valid UUID: {v}") from e
        return v

    @field_validator("providers")
    @classmethod
    def validate_providers_not_empty(cls, v: dict[str, ProviderSnapshot]) -> dict[str, ProviderSnapshot]:
        """プロバイダー情報が空でないことを検証"""
        if not v:
            raise ValueError("providers dictionary cannot be empty")
        return v
```

**Relationships**:
- `Model`を参照（多対多）
- `Change`で比較される（一対多）

**Validation Rules**:
- `snapshot_id`はUUID形式必須
- `providers`は空辞書禁止（最低1プロバイダー必要）
- `overall_status`は全プロバイダーのステータスから決定

**State Transitions**:
- 不変（`frozen=True`）
- 作成後の変更不可（履歴として保存）

---

### Change（変更）

**Purpose**: スナップショット間のモデル差分情報を表現します。新規追加または削除されたモデルを記録します。

**Pydantic Model**:

```python
from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime
from enum import Enum


class ChangeType(str, Enum):
    """変更タイプ"""
    ADDED = "added"
    REMOVED = "removed"


class Change(BaseModel):
    """
    モデル変更情報

    Attributes:
        change_id: 変更の一意識別子
        change_type: 変更タイプ（added/removed）
        model_id: 対象モデルのID
        provider_name: プロバイダー名
        detected_at: 検出日時
        previous_snapshot_id: 比較元スナップショットID
        current_snapshot_id: 比較先スナップショットID
    """
    model_config = ConfigDict(frozen=True)

    change_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="変更の一意識別子（UUID）"
    )
    change_type: ChangeType = Field(..., description="変更タイプ")
    model_id: str = Field(..., description="対象モデルID")
    provider_name: str = Field(..., description="プロバイダー名")
    detected_at: datetime = Field(
        default_factory=datetime.now,
        description="検出日時"
    )
    previous_snapshot_id: str = Field(..., description="比較元スナップショットID")
    current_snapshot_id: str = Field(..., description="比較先スナップショットID")

    @field_validator("change_id")
    @classmethod
    def validate_change_id(cls, v: str) -> str:
        """変更IDの検証：UUID形式"""
        try:
            uuid.UUID(v)
        except ValueError as e:
            raise ValueError(f"change_id must be valid UUID: {v}") from e
        return v

    @field_validator("model_id", "provider_name")
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """空文字列禁止"""
        if not v or not v.strip():
            raise ValueError("Field cannot be empty or whitespace")
        return v.strip()

    @field_validator("previous_snapshot_id", "current_snapshot_id")
    @classmethod
    def validate_snapshot_ids(cls, v: str) -> str:
        """スナップショットIDの検証：UUID形式"""
        try:
            uuid.UUID(v)
        except ValueError as e:
            raise ValueError(f"Snapshot ID must be valid UUID: {v}") from e
        return v
```

**Relationships**:
- `Snapshot`を参照（多対二）
- `Model`を参照（多対一）

**Validation Rules**:
- すべてのID（change_id、snapshot_id）はUUID形式必須
- `model_id`と`provider_name`は空文字列禁止
- `change_type`は列挙型で厳密に制限

**State Transitions**:
- 不変（`frozen=True`）
- 一度記録された変更は変更不可

---

### Cache（キャッシュ）

**Purpose**: オフライン動作を可能にするローカルストレージを表現します。TOML形式で保存され、最新のモデル情報と取得メタデータを含みます。

**Pydantic Model**:

```python
from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime
from typing import Optional


class CacheMetadata(BaseModel):
    """
    キャッシュメタデータ

    Attributes:
        version: キャッシュフォーマットバージョン
        created_at: キャッシュ作成日時
        last_updated_at: 最終更新日時
        package_version: パッケージバージョン
    """
    version: str = Field(..., description="キャッシュフォーマットバージョン（例: 1.0）")
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="キャッシュ作成日時"
    )
    last_updated_at: datetime = Field(
        default_factory=datetime.now,
        description="最終更新日時"
    )
    package_version: str = Field(..., description="llm-discoveryパッケージバージョン")

    @field_validator("version")
    @classmethod
    def validate_version_format(cls, v: str) -> str:
        """バージョン形式の検証：セマンティックバージョニング"""
        import re
        if not re.match(r'^\d+\.\d+(\.\d+)?$', v):
            raise ValueError(
                f"version must follow semantic versioning (X.Y or X.Y.Z): {v}"
            )
        return v


class Cache(BaseModel):
    """
    モデル一覧キャッシュ

    Attributes:
        metadata: キャッシュメタデータ
        models: プロバイダー別モデル一覧
    """
    metadata: CacheMetadata = Field(..., description="キャッシュメタデータ")
    models: dict[str, list[Model]] = Field(
        default_factory=dict,
        description="プロバイダー別モデル一覧"
    )

    @field_validator("models")
    @classmethod
    def validate_models_structure(cls, v: dict[str, list[Model]]) -> dict[str, list[Model]]:
        """モデル一覧の構造検証：プロバイダー名の整合性確認"""
        for provider_name, model_list in v.items():
            if not provider_name or not provider_name.strip():
                raise ValueError("Provider name cannot be empty")
            for model in model_list:
                if model.provider_name != provider_name:
                    raise ValueError(
                        f"Model provider_name '{model.provider_name}' does not match "
                        f"dictionary key '{provider_name}'"
                    )
        return v
```

**Relationships**:
- `Model`を含む（一対多）
- `CacheMetadata`を所有（一対一）

**Validation Rules**:
- `version`はセマンティックバージョニング形式（X.Y or X.Y.Z）
- `models`辞書のキー（プロバイダー名）とモデルの`provider_name`の整合性チェック
- キャッシュフォーマットバージョンとパッケージバージョンは別管理

**State Transitions**:
- 可変（定期的に更新）
- `last_updated_at`は更新時に自動更新

---

### Config（設定）

**Purpose**: 環境変数とシステム設定を管理します。Primary Data Non-Assumption Principleに準拠し、環境変数未設定時は明示的にエラーを発生させます。

**Pydantic Model**:

```python
import os
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from typing import Optional
from pathlib import Path


class Config(BaseModel):
    """
    システム設定（環境変数管理）

    Attributes:
        openai_api_key: OpenAI APIキー（オプショナル）
        google_api_key: Google AI Studio APIキー（オプショナル）
        google_genai_use_vertexai: Vertex AI使用フラグ（デフォルトfalse）
        google_application_credentials: GCPサービスアカウント認証情報パス（Vertex AI用）
        cache_directory: キャッシュディレクトリパス
        snapshot_retention_days: スナップショット保持期間（デフォルト30日）
    """
    model_config = ConfigDict(frozen=True)

    openai_api_key: Optional[str] = Field(
        default=None,
        description="OpenAI APIキー（環境変数: OPENAI_API_KEY）"
    )
    google_api_key: Optional[str] = Field(
        default=None,
        description="Google AI Studio APIキー（環境変数: GOOGLE_API_KEY）"
    )
    google_genai_use_vertexai: bool = Field(
        default=False,
        description="Vertex AI使用フラグ（環境変数: GOOGLE_GENAI_USE_VERTEXAI）"
    )
    google_application_credentials: Optional[Path] = Field(
        default=None,
        description="GCP認証情報パス（環境変数: GOOGLE_APPLICATION_CREDENTIALS）"
    )
    cache_directory: Path = Field(
        ...,
        description="キャッシュディレクトリパス"
    )
    snapshot_retention_days: int = Field(
        default=30,
        ge=1,
        description="スナップショット保持期間（日数）"
    )

    @classmethod
    def from_env(cls) -> 'Config':
        """
        環境変数から設定を読み込む

        Returns:
            Config: 設定インスタンス

        Raises:
            RuntimeError: 必須の環境変数が未設定の場合
        """
        from platformdirs import user_cache_dir

        # オプショナルな環境変数（Noneを許容）
        openai_api_key = os.getenv("OPENAI_API_KEY")
        google_api_key = os.getenv("GOOGLE_API_KEY")

        # Vertex AIフラグ（boolフラグはデフォルトfalseを許容）
        google_genai_use_vertexai = os.getenv(
            "GOOGLE_GENAI_USE_VERTEXAI",
            "false"
        ).lower() == "true"

        # Google認証情報パス（Vertex AI使用時のみ検証）
        google_creds_str = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        google_application_credentials = None
        if google_creds_str:
            google_application_credentials = Path(google_creds_str)

        # キャッシュディレクトリ（platformdirs使用）
        cache_directory = Path(user_cache_dir("llm-discovery", "llm-discovery"))

        # スナップショット保持期間（デフォルト30日）
        retention_days_str = os.getenv("SNAPSHOT_RETENTION_DAYS", "30")
        try:
            snapshot_retention_days = int(retention_days_str)
        except ValueError as e:
            raise RuntimeError(
                f"SNAPSHOT_RETENTION_DAYS must be an integer: {retention_days_str}"
            ) from e

        return cls(
            openai_api_key=openai_api_key,
            google_api_key=google_api_key,
            google_genai_use_vertexai=google_genai_use_vertexai,
            google_application_credentials=google_application_credentials,
            cache_directory=cache_directory,
            snapshot_retention_days=snapshot_retention_days,
        )

    @field_validator("openai_api_key", "google_api_key")
    @classmethod
    def validate_api_key_format(cls, v: Optional[str]) -> Optional[str]:
        """APIキーの基本検証：空文字列禁止（Noneは許容）"""
        if v is not None and not v.strip():
            raise ValueError("API key cannot be empty string (use None instead)")
        return v

    @field_validator("google_application_credentials")
    @classmethod
    def validate_credentials_path(cls, v: Optional[Path]) -> Optional[Path]:
        """認証情報ファイルの検証：存在確認は行わない（実行時に検証）"""
        if v is not None and str(v).strip() == "":
            raise ValueError(
                "google_application_credentials cannot be empty string (use None instead)"
            )
        return v

    @model_validator(mode='after')
    def validate_vertex_ai_credentials(self) -> 'Config':
        """
        Vertex AI使用時の認証情報検証

        Raises:
            ValueError: GOOGLE_GENAI_USE_VERTEXAI=trueだが認証情報が未設定
        """
        if self.google_genai_use_vertexai and self.google_application_credentials is None:
            raise ValueError(
                "GOOGLE_APPLICATION_CREDENTIALS environment variable is required "
                "when GOOGLE_GENAI_USE_VERTEXAI=true. "
                "Set it to the path of your GCP service account JSON key file. "
                "See: https://cloud.google.com/docs/authentication/application-default-credentials"
            )
        return self

    @model_validator(mode='after')
    def validate_cache_directory_writable(self) -> 'Config':
        """
        キャッシュディレクトリの書き込み権限検証

        Note: ディレクトリが存在しない場合は作成を試みる
        """
        try:
            self.cache_directory.mkdir(parents=True, exist_ok=True)
        except PermissionError as e:
            raise ValueError(
                f"Cannot create cache directory at {self.cache_directory}. "
                f"Check directory permissions."
            ) from e

        # 書き込み権限チェック
        if not os.access(self.cache_directory, os.W_OK):
            raise ValueError(
                f"Cache directory is not writable: {self.cache_directory}"
            )

        return self
```

**Relationships**:
- システム全体で共有される単一の設定インスタンス
- `Cache`のディレクトリパスを提供

**Validation Rules**:
- `GOOGLE_GENAI_USE_VERTEXAI=true`の場合、`GOOGLE_APPLICATION_CREDENTIALS`が必須
- APIキーと認証情報パスは空文字列禁止（`None`は許容）
- `cache_directory`は書き込み権限必須
- `snapshot_retention_days`は1以上の整数

**State Transitions**:
- 不変（`frozen=True`）
- プログラム起動時に一度だけ環境変数から読み込み

---

## Data Flow

以下は、主要なデータフローを示します：

### 1. モデル取得フロー

```
Environment Variables (Config.from_env)
    ↓
Provider Configuration (Provider)
    ↓
API Fetch / Manual Load (Model)
    ↓
Cache Update (Cache)
    ↓
Snapshot Creation (Snapshot)
```

### 2. 変更検知フロー

```
Current Snapshot (Snapshot)
    ↓
Previous Snapshot (Snapshot)
    ↓
Diff Calculation
    ↓
Change Detection (Change)
    ↓
CHANGELOG.md Generation
    ↓
changes.json Export
```

### 3. エクスポートフロー

```
Cache (Cache)
    ↓
Model List Aggregation
    ↓
Format Conversion (JSON/CSV/YAML/Markdown/TOML)
    ↓
File Output
```

## Serialization Format

### TOML（キャッシュ、スナップショット、Anthropicモデル）

```toml
# キャッシュ例（~/.cache/llm-discovery/models_cache.toml）
[metadata]
version = "1.0"
created_at = 2025-10-19T12:00:00Z
last_updated_at = 2025-10-19T12:00:00Z
package_version = "0.1.0"

[[models.openai]]
model_id = "gpt-4-turbo"
model_name = "GPT-4 Turbo"
provider_name = "openai"
source = "api"
fetched_at = 2025-10-19T12:00:00Z

[models.openai.metadata]
context_window = 128000
pricing_input = 10.0
pricing_output = 30.0
```

### JSON（changes.json、エクスポート）

```json
{
  "changes": [
    {
      "change_id": "550e8400-e29b-41d4-a716-446655440000",
      "change_type": "added",
      "model_id": "gpt-5",
      "provider_name": "openai",
      "detected_at": "2025-10-19T12:00:00Z",
      "previous_snapshot_id": "440e8400-e29b-41d4-a716-446655440000",
      "current_snapshot_id": "660e8400-e29b-41d4-a716-446655440000"
    }
  ]
}
```

## Error Handling Strategy

すべてのデータモデルは、Primary Data Non-Assumption Principleに準拠したエラーハンドリングを実装します：

### 原則

1. **推測禁止**: デフォルト値で問題を隠蔽しない
2. **明示的エラー**: 失敗時は明確な`ValueError`または`RuntimeError`
3. **トレーサビリティ**: 例外チェーン（`raise ... from e`）
4. **ユーザーガイダンス**: エラーメッセージに解決方法を含める

### 実装例

```python
# 良い例（Primary Data Non-Assumption準拠）
@classmethod
def from_env(cls) -> 'Config':
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key is None:
        raise RuntimeError(
            "OPENAI_API_KEY environment variable is not set. "
            "Please set it to your OpenAI API key: "
            "export OPENAI_API_KEY='your-key-here'"
        )
    return cls(openai_api_key=api_key)

# 悪い例（違反）
@classmethod
def from_env(cls) -> 'Config':
    api_key = os.getenv("OPENAI_API_KEY", "default-key")  # デフォルト値禁止
    return cls(openai_api_key=api_key)
```

## Testing Strategy

各エンティティは、以下のテスト戦略でカバーされます：

### Unit Tests

- Pydanticバリデーションのテスト（正常系・異常系）
- フィールドバリデータのテスト
- モデルバリデータのテスト
- 境界値テスト

### Integration Tests

- TOML読み書きテスト
- JSON読み書きテスト
- 環境変数からの設定読み込みテスト
- ファイルシステム操作テスト

### Contract Tests

- OpenAI API応答形式との互換性テスト
- Google API応答形式との互換性テスト
- Anthropic TOMLスキーマとの互換性テスト

### 目標カバレッジ

- `models/`: 95-100%（コアデータモデル）
- バリデーションロジック: 100%（すべてのエッジケース）

---

## Entity Relationships (ER Diagram)

```
┌─────────────┐
│   Config    │
│─────────────│
│ openai_api_key              │
│ google_api_key              │
│ google_genai_use_vertexai   │
│ google_application_credentials│
│ cache_directory             │
│ snapshot_retention_days     │
└──────┬──────┘
       │ provides
       ▼
┌─────────────┐
│  Provider   │
│─────────────│
│ name        │◄─────┐
│ api_endpoint│      │
│ fetch_method│      │
│ google_backend│    │ 1
└─────────────┘      │
                     │
                     │ N
                ┌────┴──────┐
                │   Model   │
                │───────────│
                │ model_id  │
                │ model_name│◄─────────┐
                │ provider_name│       │
                │ source    │          │
                │ fetched_at│          │
                │ metadata  │          │
                └───────────┘          │
                     ▲                 │
                     │ N               │
                     │                 │ 1
                ┌────┴────────┐        │
                │  Snapshot   │        │
                │─────────────│        │
                │ snapshot_id │        │
                │ created_at  │        │
                │ providers   │        │
                │ overall_status│      │
                └─────────────┘        │
                     ▲                 │
                     │ 1               │
                     │                 │
                ┌────┴────────┐        │
                │   Change    │        │
                │─────────────│        │
                │ change_id   │        │
                │ change_type │        │
                │ model_id    │────────┘
                │ provider_name│
                │ detected_at │
                │ prev_snap_id│
                │ curr_snap_id│
                └─────────────┘

┌─────────────┐
│   Cache     │
│─────────────│
│ metadata    │───► CacheMetadata
│ models      │───► Dict[ProviderName, List[Model]]
└─────────────┘
```

## Appendix: Type Hierarchy

```
BaseModel (Pydantic v2)
├── Model（不変、frozen=True）
├── Provider（不変、frozen=True）
├── Snapshot（不変、frozen=True）
│   └── ProviderSnapshot（可変）
├── Change（不変、frozen=True）
├── Cache（可変）
│   └── CacheMetadata（可変）
└── Config（不変、frozen=True）

Enum
├── ModelSource（api/manual）
├── ProviderType（openai/google/anthropic）
├── GoogleBackend（ai_studio/vertex_ai）
├── FetchStatus（success/partial_failure/failure）
└── ChangeType（added/removed）
```

---

## References

- **Pydantic v2 Documentation**: https://docs.pydantic.dev/latest/
- **PEP 680 (tomllib)**: https://peps.python.org/pep-0680/
- **XDG Base Directory Specification**: https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html
- **Semantic Versioning**: https://semver.org/
- **platformdirs Documentation**: https://platformdirs.readthedocs.io/
