# Python API Contract

**Feature**: [spec.md](../spec.md)
**Data Model**: [data-model.md](../data-model.md)

## Purpose

このドキュメントは、`llm-discovery`のPython API契約を定義します。CLIと同等の機能をプログラムから利用可能にし、型安全性、エラーハンドリング、非同期API設計を保証します（FR-014、FR-016、FR-023）。

## Specification

### Package Version Attribute

**目的**: パッケージバージョンをPython APIとして公開します（FR-023）。

**公開属性**:
```python
llm_discovery.__version__: str
```

**実装方法**:
- importlib.metadataを使用してpyproject.tomlから動的に取得
- pyproject.tomlをSingle Source of Truthとして維持
- ハードコーディング禁止（Primary Data Non-Assumption Principle準拠）

**動作**:
```python
from llm_discovery import __version__

print(__version__)  # 例: "0.1.0"
```

**エラーハンドリング**:
- バージョン取得に失敗した場合:
  - `PackageNotFoundError`: パッケージがインストールされていない
  - `AttributeError`: メタデータにバージョン情報が存在しない

**実装例**:
```python
# src/llm_discovery/__init__.py
from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("llm-discovery")
except PackageNotFoundError as e:
    raise PackageNotFoundError(
        "Package 'llm-discovery' not found. "
        "Please ensure it is properly installed: "
        "uv pip install llm-discovery"
    ) from e
```

### DiscoveryClient Class

**目的**: プログラムからモデル取得と差分検出を実行します（FR-014、FR-016）。

**Import**:
```python
from llm_discovery import DiscoveryClient
```

#### Constructor

```python
class DiscoveryClient:
    def __init__(
        self,
        *,
        config: Config | None = None
    ):
        """
        DiscoveryClientを初期化します。

        Args:
            config: 設定オブジェクト（None の場合は環境変数から自動生成）

        Raises:
            ConfigurationError: 必須環境変数が未設定
            RuntimeError: 設定の検証失敗
        """
```

**Example**:
```python
from llm_discovery import DiscoveryClient

# 環境変数から自動設定
client = DiscoveryClient()

# カスタム設定を使用
from llm_discovery.models import Config
custom_config = Config.from_env()
client = DiscoveryClient(config=custom_config)
```

#### `async fetch_models() -> list[Model]`

**目的**: すべてのプロバイダーからモデル一覧を並行取得します（FR-001、FR-016）。

**シグネチャ**:
```python
async def fetch_models(self) -> list[Model]:
    """
    すべてのプロバイダーからモデル一覧を取得します。

    Returns:
        Modelオブジェクトのリスト

    Raises:
        ProviderFetchError: API取得失敗（フェイルファスト、FR-017）
        PartialFetchError: 部分的取得失敗（FR-018）
        AuthenticationError: 認証情報不正（FR-021）
        ConfigurationError: 環境変数未設定
    """
```

**動作**:
1. 各プロバイダーへの非同期API呼び出し（asyncio.gather使用）
2. すべてのプロバイダーが成功した場合のみ結果を返す
3. 1つでも失敗した場合は例外を発生（部分成功の継続禁止、FR-018）

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
        # 外部でリトライ管理（cron、CI/CD等）

    except PartialFetchError as e:
        print(f"Partial failure: {e}")
        print(f"Successful providers: {e.successful_providers}")
        print(f"Failed providers: {e.failed_providers}")

asyncio.run(main())
```

#### `get_cached_models() -> list[Model]`

**目的**: キャッシュからモデルデータを取得します（FR-003）。

**シグネチャ**:
```python
def get_cached_models(self) -> list[Model]:
    """
    キャッシュからモデル一覧を取得します。

    Returns:
        Modelオブジェクトのリスト

    Raises:
        CacheNotFoundError: キャッシュファイルが存在しない
        CacheCorruptedError: キャッシュファイルが破損（FR-019）
    """
```

**動作**:
1. TOMLキャッシュファイルを読み込み
2. Pydanticモデルとしてデシリアライズ
3. バリデーションエラーの場合はCacheCorruptedErrorを発生

**Example**:
```python
from llm_discovery import DiscoveryClient
from llm_discovery.exceptions import CacheNotFoundError, CacheCorruptedError

client = DiscoveryClient()

try:
    models = client.get_cached_models()
    print(f"Loaded {len(models)} models from cache")

except CacheNotFoundError:
    print("No cache found. Run 'llm-discovery list' first.")

except CacheCorruptedError as e:
    print(f"Cache corrupted: {e}")
    print("Delete the cache file and retry.")
```

#### `async detect_changes(previous_snapshot_id: str) -> Change`

**目的**: 前回スナップショットとの差分を検出します（FR-007）。

**シグネチャ**:
```python
async def detect_changes(self, previous_snapshot_id: str) -> Change:
    """
    モデル変更を検出します。

    Args:
        previous_snapshot_id: 比較元スナップショットID（UUID）

    Returns:
        Change: 変更情報（追加・削除されたモデル）

    Raises:
        SnapshotNotFoundError: 指定IDのスナップショットが存在しない
        ValidationError: 不正なUUID形式
    """
```

**動作**:
1. 指定されたスナップショットIDを検証（UUID形式）
2. 現在のモデル一覧を取得
3. 前回スナップショットと比較
4. 差分を`Change`オブジェクトとして返す

**Example**:
```python
from llm_discovery import DiscoveryClient
from llm_discovery.models import ChangeType

async def monitor_changes():
    client = DiscoveryClient()

    # 前回のスナップショットIDを取得（例: データベースやファイルから）
    previous_id = "550e8400-e29b-41d4-a716-446655440000"

    change = await client.detect_changes(previous_id)

    print(f"Added models: {len([c for c in change.changes if c.change_type == ChangeType.ADDED])}")
    print(f"Removed models: {len([c for c in change.changes if c.change_type == ChangeType.REMOVED])}")

asyncio.run(monitor_changes())
```

### Export Functions

**目的**: モデルデータをマルチフォーマットでエクスポートします（FR-005、FR-006）。

#### `export_json(models: list[Model]) -> str`

**シグネチャ**:
```python
def export_json(models: list[Model], *, indent: int = 2) -> str:
    """
    JSON形式でモデル一覧をエクスポートします（CI/CD統合最適化）。

    Args:
        models: エクスポート対象のモデルリスト
        indent: インデント幅（デフォルト: 2）

    Returns:
        JSON文字列

    Raises:
        ValueError: modelsが空リスト
    """
```

**Example**:
```python
from llm_discovery import DiscoveryClient, export_json

async def export_to_json_file():
    client = DiscoveryClient()
    models = await client.fetch_models()

    json_str = export_json(models)

    with open("models.json", "w") as f:
        f.write(json_str)
```

#### `export_csv(models: list[Model]) -> str`

**シグネチャ**:
```python
def export_csv(models: list[Model]) -> str:
    """
    CSV形式でモデル一覧をエクスポートします（表計算ソフト分析用）。

    Args:
        models: エクスポート対象のモデルリスト

    Returns:
        CSV文字列

    Raises:
        ValueError: modelsが空リスト
    """
```

**CSV形式仕様**: [data-formats.md](./data-formats.md)を参照

#### `export_yaml(models: list[Model]) -> str`

**シグネチャ**:
```python
def export_yaml(models: list[Model]) -> str:
    """
    YAML形式でモデル一覧をエクスポートします（設定ファイル用）。

    Args:
        models: エクスポート対象のモデルリスト

    Returns:
        YAML文字列

    Raises:
        ValueError: modelsが空リスト
    """
```

#### `export_markdown(models: list[Model]) -> str`

**シグネチャ**:
```python
def export_markdown(models: list[Model]) -> str:
    """
    Markdown形式でモデル一覧をエクスポートします（ドキュメント用、人間可読）。

    Args:
        models: エクスポート対象のモデルリスト

    Returns:
        Markdown文字列

    Raises:
        ValueError: modelsが空リスト
    """
```

#### `export_toml(models: list[Model]) -> str`

**シグネチャ**:
```python
def export_toml(models: list[Model]) -> str:
    """
    TOML形式でモデル一覧をエクスポートします（相互運用性・設定ファイル用）。

    Args:
        models: エクスポート対象のモデルリスト

    Returns:
        TOML文字列

    Raises:
        ValueError: modelsが空リスト
    """
```

### Exception Hierarchy

**目的**: すべてのエラーを型安全に処理できるようにします。

**階層構造**:
```python
class LLMDiscoveryError(Exception):
    """Base exception for llm-discovery"""
    pass


class ProviderFetchError(LLMDiscoveryError):
    """
    API取得失敗（フェイルファスト原則、FR-017）

    Attributes:
        provider_name: 失敗したプロバイダー名
        cause: 失敗の原因
    """
    def __init__(self, provider_name: str, cause: str):
        self.provider_name = provider_name
        self.cause = cause
        super().__init__(f"Failed to fetch from {provider_name}: {cause}")


class PartialFetchError(LLMDiscoveryError):
    """
    部分的取得失敗（FR-18）

    Attributes:
        successful_providers: 成功したプロバイダー名のリスト
        failed_providers: 失敗したプロバイダー名のリスト
    """
    def __init__(
        self,
        successful_providers: list[str],
        failed_providers: list[str]
    ):
        self.successful_providers = successful_providers
        self.failed_providers = failed_providers
        super().__init__(
            f"Partial failure. Successful: {successful_providers}, "
            f"Failed: {failed_providers}"
        )


class AuthenticationError(LLMDiscoveryError):
    """
    認証情報不正（APIキー、GCP認証情報等、FR-021）

    Attributes:
        provider_name: 認証失敗したプロバイダー名
        details: 詳細情報
    """
    def __init__(self, provider_name: str, details: str):
        self.provider_name = provider_name
        self.details = details
        super().__init__(
            f"Authentication failed for {provider_name}: {details}"
        )


class ConfigurationError(LLMDiscoveryError):
    """
    設定エラー（環境変数未設定等）

    Attributes:
        variable_name: 未設定または不正な環境変数名
        suggestion: 解決方法の提案
    """
    def __init__(self, variable_name: str, suggestion: str):
        self.variable_name = variable_name
        self.suggestion = suggestion
        super().__init__(
            f"Configuration error for {variable_name}. {suggestion}"
        )


class CacheNotFoundError(LLMDiscoveryError):
    """キャッシュファイルが存在しない"""
    pass


class CacheCorruptedError(LLMDiscoveryError):
    """
    キャッシュファイル破損（FR-019）

    Attributes:
        cache_path: 破損したキャッシュファイルのパス
        parse_error: パースエラーの詳細
    """
    def __init__(self, cache_path: str, parse_error: str):
        self.cache_path = cache_path
        self.parse_error = parse_error
        super().__init__(
            f"Cache file corrupted at {cache_path}: {parse_error}"
        )


class SnapshotNotFoundError(LLMDiscoveryError):
    """
    指定IDのスナップショット不存在

    Attributes:
        snapshot_id: 見つからなかったスナップショットID
    """
    def __init__(self, snapshot_id: str):
        self.snapshot_id = snapshot_id
        super().__init__(f"Snapshot not found: {snapshot_id}")
```

## Examples

### Example 1: Basic Model Fetching

```python
import asyncio
from llm_discovery import DiscoveryClient

async def main():
    client = DiscoveryClient()
    models = await client.fetch_models()

    print(f"Total models: {len(models)}")

    for model in models:
        print(f"{model.provider_name}/{model.model_id}: {model.model_name}")

asyncio.run(main())
```

### Example 2: Change Detection and Notification

```python
import asyncio
from llm_discovery import DiscoveryClient
from llm_discovery.models import ChangeType

async def monitor_and_notify():
    """新モデル検知とSlack通知（User Story 4）"""
    client = DiscoveryClient()

    # 前回のスナップショットIDを取得
    previous_id = load_previous_snapshot_id()  # ユーザー実装

    change = await client.detect_changes(previous_id)

    added_models = [
        c for c in change.changes
        if c.change_type == ChangeType.ADDED
    ]

    if added_models:
        # Slack通知（例）
        message = f"New models detected ({len(added_models)}):\\n"
        for change in added_models:
            message += f"  - {change.model_id}\\n"

        send_slack_notification(message)  # ユーザー実装

asyncio.run(monitor_and_notify())
```

### Example 3: Multi-Format Export

```python
from pathlib import Path
from llm_discovery import DiscoveryClient, export_json, export_csv, export_markdown

async def export_all_formats():
    client = DiscoveryClient()
    models = await client.fetch_models()

    # JSON形式（CI/CD統合用）
    json_str = export_json(models)
    Path("models.json").write_text(json_str)

    # CSV形式（分析用）
    csv_str = export_csv(models)
    Path("models.csv").write_text(csv_str)

    # Markdown形式（ドキュメント用）
    md_str = export_markdown(models)
    Path("models.md").write_text(md_str)

    print("Exported to all formats")

asyncio.run(export_all_formats())
```

### Example 4: Error Handling

```python
import asyncio
from llm_discovery import DiscoveryClient
from llm_discovery.exceptions import (
    ProviderFetchError,
    PartialFetchError,
    AuthenticationError,
    CacheCorruptedError
)

async def safe_fetch_with_fallback():
    client = DiscoveryClient()

    try:
        # API取得を試行
        models = await client.fetch_models()
        return models

    except ProviderFetchError as e:
        print(f"API fetch failed: {e.provider_name} - {e.cause}")

        # キャッシュからフォールバック
        try:
            models = client.get_cached_models()
            print("Loaded from cache")
            return models
        except CacheCorruptedError as cache_err:
            print(f"Cache corrupted: {cache_err}")
            raise

    except PartialFetchError as e:
        # 部分失敗は継続しない（FR-018）
        print(f"Partial failure detected")
        print(f"Successful: {e.successful_providers}")
        print(f"Failed: {e.failed_providers}")
        raise

    except AuthenticationError as e:
        print(f"Authentication failed: {e.provider_name}")
        print(f"Details: {e.details}")
        raise

asyncio.run(safe_fetch_with_fallback())
```

### Example 5: CI/CD Integration (User Story 4)

```python
import asyncio
import json
from pathlib import Path
from llm_discovery import DiscoveryClient
from llm_discovery.models import ChangeType

async def ci_cd_pipeline():
    """GitHub ActionsでのCI/CD統合例"""
    client = DiscoveryClient()

    # 前回のスナップショットIDを取得
    snapshot_file = Path(".llm-discovery-snapshot")
    if snapshot_file.exists():
        previous_id = snapshot_file.read_text().strip()

        # 変更検知
        change = await client.detect_changes(previous_id)

        # changes.jsonへ出力
        changes_data = {
            "previous_snapshot_id": change.previous_snapshot_id,
            "current_snapshot_id": change.current_snapshot_id,
            "detected_at": change.detected_at.isoformat(),
            "changes": [
                {
                    "type": c.change_type.value,
                    "model_id": c.model_id,
                    "provider_name": c.provider_name
                }
                for c in change.changes
            ]
        }

        Path("changes.json").write_text(json.dumps(changes_data, indent=2))

        # 新モデルがあればCI失敗（通知目的）
        added = [c for c in change.changes if c.change_type == ChangeType.ADDED]
        if added:
            print(f"::warning::New models detected: {len(added)}")
            # GitHub Actionsの出力に表示
    else:
        # 初回実行: ベースラインを保存
        models = await client.fetch_models()
        snapshot_id = "initial-snapshot"  # 実際はUUIDを生成
        snapshot_file.write_text(snapshot_id)

asyncio.run(ci_cd_pipeline())
```

## Test Requirements

### Unit Tests

- `tests/unit/api/test_discovery_client.py`:
  - `DiscoveryClient.__init__()`の動作
  - `fetch_models()`の正常系・異常系
  - `get_cached_models()`の動作
  - `detect_changes()`の差分検出ロジック

- `tests/unit/api/test_export_functions.py`:
  - 各エクスポート関数の出力形式検証
  - 空リストの処理
  - エッジケース（特殊文字、大量データ等）

- `tests/unit/api/test_version_attribute.py`:
  - `__version__`属性の取得成功
  - バージョン取得失敗時の例外

### Integration Tests

- `tests/integration/api/test_api_workflow.py`:
  - 取得→エクスポート→ファイル保存の一連のフロー
  - キャッシュ→差分検出のフロー

### Contract Tests

- `tests/contract/test_python_api.py`:
  - User Story 4のAcceptance Scenarios（全4シナリオ）
  - 型ヒントの正確性検証
  - 例外階層の整合性検証
  - 非同期APIの動作検証

### Error Handling Tests

- `tests/error/test_api_exceptions.py`:
  - 各例外クラスの生成と属性
  - エラーメッセージの内容
  - 例外チェーン（`raise ... from e`）

## References

- **FR-001**: マルチプロバイダー対応
- **FR-003**: TOMLキャッシュ
- **FR-005**: マルチフォーマットエクスポート
- **FR-007**: 差分検出
- **FR-014**: Python API提供
- **FR-016**: 非同期API
- **FR-017**: API障害時エラーハンドリング
- **FR-018**: 部分失敗時エラーハンドリング
- **FR-019**: キャッシュ破損リカバリ
- **FR-021**: Vertex AI認証
- **FR-023**: `__version__`属性公開
- **User Story 4**: CI/CD統合とPython API利用
