# Contract: PrebuiltDataLoader

**Module**: `llm_discovery.services.prebuilt_loader`
**Phase**: 1 - Design & Contracts
**Date**: 2025-10-19
**Status**: Complete

## Overview

PrebuiltDataLoaderは、リポジトリ内に保存された事前生成モデルデータを読み込み、Modelオブジェクトのリストとして提供するサービスクラスです。

## Class: PrebuiltDataLoader

### Responsibilities

1. 事前生成データファイルの存在確認
2. JSONファイルの読み込みとパース
3. データの検証（pydanticモデル使用）
4. Modelオブジェクトへの変換
5. メタデータ情報の提供
6. データ経過時間の計算

### Public Interface

#### Constructor

```python
def __init__(self) -> None:
    """Initialize PrebuiltDataLoader.

    No parameters required. Data path is determined automatically.
    """
```

**Behavior**:
- リモートURL定数を設定
- URL: `https://raw.githubusercontent.com/drillan/llm-discovery/main/data/prebuilt/models.json`

**Postconditions**:
- `self.remote_url` が設定される（`str`）

---

#### is_available

```python
def is_available(self) -> bool:
    """Check if prebuilt data is accessible via remote URL.

    Returns:
        True if remote URL is accessible (HTTP 200), False otherwise.
    """
```

**Behavior**:
- リモートURLにHEADリクエスト送信
- HTTP 200ステータスコード確認
- タイムアウト: 3秒

**Returns**:
- `True`: URLにアクセス可能（HTTP 200）
- `False`: アクセス不可（タイムアウト、404、ネットワークエラー等）

**Exceptions**: なし（内部でキャッチし、Falseを返す）

---

#### load_models

```python
def load_models(self) -> list[Model]:
    """Load models from prebuilt data file.

    Returns:
        List of Model objects loaded from prebuilt data.

    Raises:
        PrebuiltDataNotFoundError: If prebuilt data file does not exist.
        PrebuiltDataCorruptedError: If file is corrupted or invalid JSON.
        PrebuiltDataValidationError: If data does not match expected schema.
    """
```

**Preconditions**:
- リモートURLにアクセス可能（`is_available() == True`）

**Behavior**:
1. リモートURLからJSONをHTTP GETで取得（タイムアウト: 10秒）
2. `PrebuiltModelData`でバリデーション
3. 各`ProviderSnapshot`から`Model`を抽出
4. フラットなリストとして返す

**Returns**:
- `list[Model]`: すべてのプロバイダーのモデルを含むリスト
- 空リストは返さない（データがない場合は例外）

**Exceptions**:
- `PrebuiltDataNotFoundError`: URLにアクセスできない（HTTP 404、ネットワークエラー）
- `PrebuiltDataCorruptedError`: JSONパースエラー、HTTPタイムアウト
- `PrebuiltDataValidationError`: pydanticバリデーションエラー

**Example**:
```python
loader = PrebuiltDataLoader()
if loader.is_available():
    models = loader.load_models()  # list[Model]
```

---

#### get_metadata

```python
def get_metadata(self) -> PrebuiltDataMetadata:
    """Get metadata about prebuilt data.

    Returns:
        Metadata object containing generation info.

    Raises:
        PrebuiltDataNotFoundError: If prebuilt data file does not exist.
        PrebuiltDataCorruptedError: If file is corrupted.
    """
```

**Preconditions**:
- リモートURLにアクセス可能

**Behavior**:
1. リモートURLからJSONをHTTP GETで取得
2. `metadata`セクションをパース
3. `PrebuiltDataMetadata`オブジェクトを返す

**Returns**:
- `PrebuiltDataMetadata`: メタデータオブジェクト

**Exceptions**:
- `PrebuiltDataNotFoundError`: URLにアクセスできない
- `PrebuiltDataCorruptedError`: JSONパースエラー、HTTPエラー

---

#### get_age_hours

```python
def get_age_hours(self) -> float:
    """Get age of prebuilt data in hours.

    Returns:
        Age in hours since data generation.

    Raises:
        PrebuiltDataNotFoundError: If prebuilt data file does not exist.
    """
```

**Behavior**:
1. メタデータを取得
2. `generated_at`と現在時刻（UTC）の差分を計算
3. 時間単位で返す

**Returns**:
- `float`: データ経過時間（時間単位、小数点以下1桁）

**Exceptions**:
- `PrebuiltDataNotFoundError`: URLにアクセスできない
- `PrebuiltDataCorruptedError`: HTTPエラー、JSONパースエラー

---

#### get_data_source_info

```python
def get_data_source_info(self, provider_name: str) -> DataSourceInfo:
    """Get data source information for a provider.

    Args:
        provider_name: Provider name (e.g., "openai", "google", "anthropic")

    Returns:
        DataSourceInfo object for the provider.

    Raises:
        PrebuiltDataNotFoundError: If prebuilt data file does not exist.
        ValueError: If provider not found in prebuilt data.
    """
```

**Preconditions**:
- リモートURLにアクセス可能
- プロバイダー名が有効

**Behavior**:
1. リモートURLからJSONをHTTP GETで取得
2. 指定プロバイダーのスナップショットを検索
3. `DataSourceInfo`オブジェクトを生成

**Returns**:
- `DataSourceInfo`: データソース情報オブジェクト

**Exceptions**:
- `PrebuiltDataNotFoundError`: URLにアクセスできない
- `PrebuiltDataCorruptedError`: HTTPエラー、JSONパースエラー
- `ValueError`: プロバイダーが見つからない

---

### Custom Exceptions

#### PrebuiltDataNotFoundError

```python
class PrebuiltDataNotFoundError(Exception):
    """Raised when prebuilt data file does not exist."""

    def __init__(self, message: str = "Prebuilt data file not found"):
        self.message = message
        super().__init__(self.message)
```

**When Raised**:
- `load_models()` 実行時にURLにアクセスできない（HTTP 404、ネットワークエラー）
- `get_metadata()` 実行時にURLにアクセスできない
- `get_age_hours()` 実行時にURLにアクセスできない

**User Guidance**:
```
Prebuilt data not accessible from remote URL.

Please either:
1. Set API keys to fetch real-time data:
   export OPENAI_API_KEY="sk-..."
   export GOOGLE_API_KEY="AIza..."

2. Check your network connection

3. Verify GitHub repository status (https://github.com/drillan/llm-discovery)

4. Report this issue if the problem persists
```

---

#### PrebuiltDataCorruptedError

```python
class PrebuiltDataCorruptedError(Exception):
    """Raised when prebuilt data file is corrupted."""

    def __init__(self, message: str, original_error: Exception | None = None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)
```

**When Raised**:
- JSONパースエラー（`json.JSONDecodeError`）
- HTTPタイムアウト
- HTTP 5xxエラー（サーバーエラー）

**User Guidance**:
```
Prebuilt data retrieval failed: {original_error}

Possible causes:
- Network timeout or connection issues
- GitHub server temporary unavailable
- Invalid JSON format in remote data

Please:
1. Retry after a few moments
2. Check your network connection
3. Report persistent issues: https://github.com/drillan/llm-discovery/issues
```

---

#### PrebuiltDataValidationError

```python
class PrebuiltDataValidationError(Exception):
    """Raised when prebuilt data does not match expected schema."""

    def __init__(self, message: str, validation_errors: list[str]):
        self.message = message
        self.validation_errors = validation_errors
        super().__init__(self.message)
```

**When Raised**:
- pydanticバリデーションエラー
- 予期しないデータ構造

**User Guidance**:
```
Prebuilt data validation failed:
- {validation_error_1}
- {validation_error_2}

This may indicate a version mismatch. Please update llm-discovery:
pip install --upgrade llm-discovery
```

---

## Integration Points

### DiscoveryService Extension

`DiscoveryService`に新規メソッド追加:

```python
class DiscoveryService:
    def __init__(self, config: Config):
        self.config = config
        self.prebuilt_loader = PrebuiltDataLoader()  # 追加
        # ... 既存の初期化 ...

    def has_api_keys(self) -> bool:
        """Check if any API keys are configured."""
        return self.config.has_any_api_keys()

    async def fetch_or_load_models(self) -> list[Model]:
        """Fetch from API if keys available, otherwise load prebuilt."""
        if self.has_api_keys():
            # Try API fetch
            try:
                snapshots = await self.fetch_all_models()
                return [model for snapshot in snapshots for model in snapshot.models]
            except Exception as e:
                # If API fails and prebuilt available, use prebuilt
                if self.prebuilt_loader.is_available():
                    console.print(
                        f"[yellow]⚠ API fetch failed: {e}[/yellow]\n"
                        "[yellow]→ Using prebuilt data[/yellow]"
                    )
                    return self.prebuilt_loader.load_models()
                raise
        else:
            # No API keys, use prebuilt
            if self.prebuilt_loader.is_available():
                return self.prebuilt_loader.load_models()
            raise PrebuiltDataNotFoundError(
                "No API keys configured and no prebuilt data available"
            )
```

---

## Test Contract

### Unit Tests

```python
# tests/unit/services/test_prebuilt_loader.py

def test_is_available_returns_true_when_file_exists():
    """Given prebuilt data file exists, is_available returns True."""

def test_is_available_returns_false_when_file_missing():
    """Given prebuilt data file does not exist, is_available returns False."""

def test_load_models_returns_model_list():
    """Given valid prebuilt data, load_models returns list of Model objects."""

def test_load_models_raises_not_found_when_file_missing():
    """Given file does not exist, load_models raises PrebuiltDataNotFoundError."""

def test_load_models_raises_corrupted_on_invalid_json():
    """Given invalid JSON, load_models raises PrebuiltDataCorruptedError."""

def test_load_models_raises_validation_error_on_schema_mismatch():
    """Given data with invalid schema, load_models raises PrebuiltDataValidationError."""

def test_get_metadata_returns_metadata_object():
    """Given valid data, get_metadata returns PrebuiltDataMetadata."""

def test_get_age_hours_calculates_correctly():
    """Given data with known timestamp, get_age_hours returns correct value."""

def test_get_data_source_info_returns_info_for_provider():
    """Given provider name, get_data_source_info returns DataSourceInfo."""
```

### Integration Tests

```python
# tests/integration/test_prebuilt_data_integration.py

def test_load_real_prebuilt_data_file():
    """Given real prebuilt data file, all models load successfully."""

def test_discovery_service_uses_prebuilt_when_no_api_keys():
    """Given no API keys, DiscoveryService uses prebuilt data."""

def test_discovery_service_prefers_api_when_keys_available():
    """Given API keys, DiscoveryService fetches from API."""

def test_cli_displays_prebuilt_data_source():
    """Given prebuilt data usage, CLI displays source information."""
```

---

## Performance Requirements

- `load_models()`: < 3秒（HTTPリクエスト + 500KB JSONパース）
- `is_available()`: < 3秒（HEAD リクエスト）
- `get_metadata()`: < 3秒（HTTPリクエスト + メタデータパース）
- `get_age_hours()`: < 3秒（HTTPリクエスト + 計算）

---

## Security Considerations

- リモートURLは定数として定義（ユーザー入力を受け付けない）
- HTTPS通信のみ（中間者攻撃対策）
- JSONパースはPythonの標準`json`モジュールを使用（信頼できる）
- タイムアウト設定によりDoS攻撃の影響を軽減

---

## Summary

PrebuiltDataLoaderの完全なコントラクトを定義しました。5つの公開メソッドと3つのカスタム例外、DiscoveryServiceとの統合ポイント、テスト要件を含みます。

次のステップ: quickstart.mdの作成
