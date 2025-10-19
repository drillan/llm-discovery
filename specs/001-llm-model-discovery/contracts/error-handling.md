# Error Handling Contract

**Feature**: [spec.md](../spec.md)
**Data Model**: [data-model.md](../data-model.md)

## Purpose

このドキュメントは、`llm-discovery`のエラーハンドリング戦略を定義します。エラーカテゴリ、処理方針、エラーメッセージフォーマット、リカバリ戦略を規定し、Primary Data Non-Assumption Principleに準拠した厳格なエラーハンドリングを保証します（FR-017、FR-018、FR-019、FR-021、FR-022）。

## Specification

### Error Handling Principles

#### 1. Fail-Fast Principle

**原則**: エラー発生時は即座に処理を終了し、問題を隠蔽しない

**禁止事項**:
- フォールバック値の使用（"unknown"、"dev"、デフォルト値等）
- 部分成功での処理継続（FR-018）
- エラーの黙殺（サイレントエラー）

**実装**:
```python
# ❌ Bad: フォールバック値で継続
def get_version():
    try:
        return version("llm-discovery")
    except PackageNotFoundError:
        return "unknown"  # 禁止

# ✅ Good: 明示的なエラーで終了
def get_version():
    try:
        return version("llm-discovery")
    except PackageNotFoundError as e:
        raise PackageNotFoundError(
            "Package 'llm-discovery' not found. "
            "Please ensure it is properly installed."
        ) from e
```

#### 2. Clear Error Messages

**原則**: エラーメッセージは問題の原因と解決方法を明確に示す

**必須要素**:
1. **問題の説明**: 何が起こったか
2. **原因**: なぜ起こったか
3. **解決方法**: どうすればよいか（Suggested actions）

**実装例**:
```
Error: Failed to fetch models from OpenAI API.

Provider: openai
Cause: Connection timeout (10 seconds)

Suggested actions:
  1. Check your internet connection
  2. Verify OPENAI_API_KEY is set correctly
  3. Check OpenAI status: https://status.openai.com/
  4. Retry the command later
```

#### 3. Exception Chaining

**原則**: 元の例外を保持し、トレーサビリティを確保

**実装**:
```python
try:
    api_response = await fetch_from_api()
except httpx.TimeoutException as e:
    raise ProviderFetchError(
        provider_name="openai",
        cause="Connection timeout"
    ) from e  # 元の例外を保持
```

### Error Categories

#### Category 1: API Fetch Errors (FR-017)

**目的**: プロバイダーAPIからのモデル取得失敗

**エラークラス**: `ProviderFetchError`

**発生条件**:
- API接続タイムアウト
- APIレート制限
- API障害（5xx エラー）
- ネットワークエラー

**処理方針**:
- 明確なエラーメッセージを表示
- プロバイダー名、原因、対処法を含める
- ゼロ以外の終了コード（CLI: 1）
- **リトライは実装しない**（外部cron/CI/CDで管理）

**CLI出力例**:
```
Error: Failed to fetch models from OpenAI API.

Provider: openai
Cause: HTTP 503 Service Unavailable

Suggested actions:
  1. Check OpenAI status: https://status.openai.com/
  2. Wait a few minutes and retry
  3. If the issue persists, contact OpenAI support
```

**Python API例**:
```python
from llm_discovery.exceptions import ProviderFetchError

try:
    models = await client.fetch_models()
except ProviderFetchError as e:
    print(f"Provider: {e.provider_name}")
    print(f"Cause: {e.cause}")
    # 外部でリトライ管理
```

#### Category 2: Partial Fetch Errors (FR-018)

**目的**: 一部プロバイダーのみ取得失敗

**エラークラス**: `PartialFetchError`

**発生条件**:
- 複数プロバイダーのうち、1つ以上が失敗

**処理方針**:
- **部分成功での継続を禁止**
- 成功したプロバイダーと失敗したプロバイダーをリスト表示
- データ整合性を保つため、全体を失敗として扱う

**CLI出力例**:
```
Error: Partial failure during model fetch.

Successful providers:
  - openai (15 models)
  - anthropic (8 models)

Failed providers:
  - google (Connection refused)

To ensure data consistency, processing has been aborted.
Please resolve the issue with the failed provider and retry.
```

**Python API例**:
```python
from llm_discovery.exceptions import PartialFetchError

try:
    models = await client.fetch_models()
except PartialFetchError as e:
    print(f"Successful: {e.successful_providers}")
    print(f"Failed: {e.failed_providers}")
    # 全体を失敗として扱う
```

#### Category 3: Authentication Errors (FR-021)

**目的**: 認証情報の不正・欠如

**エラークラス**: `AuthenticationError`

**発生条件**:
- APIキー未設定
- APIキー無効
- GCP認証情報（GOOGLE_APPLICATION_CREDENTIALS）未設定
- GCP認証情報ファイルが存在しない、または不正

**処理方針**:
- 環境変数の設定方法を明示
- 認証情報の取得手順へのリンクを提供
- ゼロ以外の終了コード（CLI: 1）

**CLI出力例（Vertex AI）**:
```
Error: Vertex AI authentication failed.

GOOGLE_GENAI_USE_VERTEXAI is set to 'true', but GOOGLE_APPLICATION_CREDENTIALS is not set.

To use Vertex AI, you need to set up GCP authentication:

  1. Create a service account in GCP Console
  2. Download the JSON key file
  3. Set the environment variable:
     export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"

For detailed instructions, see:
https://cloud.google.com/docs/authentication/application-default-credentials
```

**Python API例**:
```python
from llm_discovery.exceptions import AuthenticationError

try:
    models = await client.fetch_models()
except AuthenticationError as e:
    print(f"Provider: {e.provider_name}")
    print(f"Details: {e.details}")
```

#### Category 4: Cache Corruption Errors (FR-019)

**目的**: キャッシュファイルの破損

**エラークラス**: `CacheCorruptedError`

**発生条件**:
- TOMLパース失敗
- Pydanticバリデーションエラー
- 不正なデータ構造

**処理方針**:
1. 警告を表示
2. API再取得を試行
3. 再取得成功: 新しいキャッシュを保存
4. 再取得失敗: エラーで終了

**CLI出力例（リカバリ成功）**:
```
Warning: Cache file is corrupted (TOML parse error).
Attempting to fetch fresh data from APIs...

[Success: Fresh data retrieved and cached]
```

**CLI出力例（リカバリ失敗）**:
```
Error: Cache file is corrupted and API fetch failed.

Cache file: ~/.cache/llm-discovery/models_cache.toml
Parse error: Expected '=' after key at line 15

Suggested actions:
  1. Delete the corrupted cache file:
     rm ~/.cache/llm-discovery/models_cache.toml
  2. Ensure internet connection is available
  3. Retry the command
```

**Python API例**:
```python
from llm_discovery.exceptions import CacheCorruptedError

try:
    models = client.get_cached_models()
except CacheCorruptedError as e:
    print(f"Cache path: {e.cache_path}")
    print(f"Parse error: {e.parse_error}")
    # API再取得を試行
```

#### Category 5: Version Retrieval Errors (FR-022)

**目的**: バージョン情報取得失敗

**エラークラス**: `PackageNotFoundError`, `AttributeError`

**発生条件**:
- パッケージが正しくインストールされていない
- editable installの設定ミス
- pyproject.tomlが見つからない

**処理方針**:
- 再インストール手順を提示
- editable installの確認方法を提示
- **フォールバック値（"unknown"、"dev"）の使用禁止**

**CLI出力例**:
```
Error: Could not retrieve package version.
This may indicate an improper installation.

Please try reinstalling llm-discovery:
  uv pip install --reinstall llm-discovery

If you installed in editable mode (uv pip install -e .), ensure pyproject.toml is present.
```

**Python API例**:
```python
from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("llm-discovery")
except PackageNotFoundError as e:
    raise PackageNotFoundError(
        "Package 'llm-discovery' not found. "
        "Please ensure it is properly installed."
    ) from e
```

#### Category 6: Configuration Errors

**目的**: 環境変数・設定の不正

**エラークラス**: `ConfigurationError`

**発生条件**:
- 必須環境変数が未設定（オプショナルな環境変数は除く）
- 環境変数の値が不正（例: SNAPSHOT_RETENTION_DAYSが整数でない）
- キャッシュディレクトリに書き込み権限がない

**処理方針**:
- 不正な環境変数名を明示
- 正しい設定方法を提示

**CLI出力例**:
```
Error: Configuration error for SNAPSHOT_RETENTION_DAYS.

Value: "invalid"
Expected: Integer (number of days)

Please set a valid value:
  export SNAPSHOT_RETENTION_DAYS=30
```

**Python API例**:
```python
from llm_discovery.exceptions import ConfigurationError

try:
    config = Config.from_env()
except ConfigurationError as e:
    print(f"Variable: {e.variable_name}")
    print(f"Suggestion: {e.suggestion}")
```

#### Category 7: File I/O Errors

**目的**: ファイル読み書き失敗

**エラークラス**: `FileIOError`

**発生条件**:
- 出力ファイルへの書き込み権限がない
- ディレクトリが存在しない
- ディスク容量不足

**処理方針**:
- ファイルパスと原因を明示
- 解決方法を提示

**CLI出力例**:
```
Error: Failed to write to file '/readonly/path/output.json'.

Cause: Permission denied

Suggested actions:
  1. Check directory permissions
  2. Ensure the directory exists
  3. Try writing to a different location
```

#### Category 8: Snapshot Not Found Errors

**目的**: 指定されたスナップショットIDが存在しない

**エラークラス**: `SnapshotNotFoundError`

**発生条件**:
- `detect_changes()`に不正なスナップショットIDを指定
- スナップショットが削除済み（保持期間超過）

**処理方針**:
- スナップショットIDを明示
- 有効なIDの取得方法を提示

**CLI出力例**:
```
Error: Snapshot not found: 550e8400-e29b-41d4-a716-446655440000

Suggested actions:
  1. Check the snapshot ID
  2. List available snapshots: llm-discovery snapshots list
  3. Use the most recent snapshot for comparison
```

**Python API例**:
```python
from llm_discovery.exceptions import SnapshotNotFoundError

try:
    change = await client.detect_changes("invalid-id")
except SnapshotNotFoundError as e:
    print(f"Snapshot ID: {e.snapshot_id}")
```

### Error Message Format

**標準フォーマット**:

```
Error: <問題の概要>

<詳細情報（キー: 値形式）>

Suggested actions:
  1. <解決方法1>
  2. <解決方法2>
  3. <参考リンク>
```

**例**:
```
Error: Failed to fetch models from Google API.

Provider: google
Cause: API key invalid or expired

Suggested actions:
  1. Verify GOOGLE_API_KEY is set correctly:
     echo $GOOGLE_API_KEY
  2. Regenerate API key: https://console.cloud.google.com/apis/credentials
  3. Check API quota: https://console.cloud.google.com/apis/dashboard
```

### Exit Codes (CLI)

| Exit Code | Category                      | Example                                |
|-----------|-------------------------------|----------------------------------------|
| 0         | Success                       | 正常終了                               |
| 1         | General Error                 | API障害、キャッシュ破損、ファイルI/O   |
| 2         | Command-Line Argument Error   | 必須オプション未指定、不正な形式指定   |

### Recovery Strategies

#### Strategy 1: No Automatic Retry

**適用**: API Fetch Errors（FR-017）

**理由**: リトライは外部（cron、CI/CD）で管理すべき

**実装**:
```python
# ❌ Bad: 自動リトライ
async def fetch_with_retry():
    for attempt in range(3):
        try:
            return await fetch_models()
        except ProviderFetchError:
            await asyncio.sleep(2 ** attempt)
    raise

# ✅ Good: 即座に失敗
async def fetch_models():
    try:
        return await api.fetch()
    except httpx.TimeoutException as e:
        raise ProviderFetchError(...) from e
```

#### Strategy 2: Cache Fallback (Only for Cache Corruption)

**適用**: Cache Corruption Errors（FR-019）

**実装**:
```python
def get_models():
    try:
        return get_cached_models()
    except CacheCorruptedError:
        # 警告を表示
        print("Warning: Cache corrupted. Fetching fresh data...")
        try:
            models = await fetch_models()
            save_cache(models)
            return models
        except ProviderFetchError:
            # 再取得失敗: エラーで終了
            raise
```

#### Strategy 3: No Fallback for Other Errors

**適用**: すべてのエラー（Cache Corruption以外）

**理由**: Primary Data Non-Assumption Principle準拠

## Examples

### Example 1: API Fetch Error with Detailed Message

```python
import httpx
from llm_discovery.exceptions import ProviderFetchError

async def fetch_openai_models():
    try:
        response = await httpx.get(
            "https://api.openai.com/v1/models",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=10.0
        )
        response.raise_for_status()
        return response.json()
    except httpx.TimeoutException as e:
        raise ProviderFetchError(
            provider_name="openai",
            cause="Connection timeout (10 seconds)"
        ) from e
    except httpx.HTTPStatusError as e:
        raise ProviderFetchError(
            provider_name="openai",
            cause=f"HTTP {e.response.status_code} {e.response.reason_phrase}"
        ) from e
```

### Example 2: Vertex AI Authentication Error

```python
from llm_discovery.models import Config
from llm_discovery.exceptions import AuthenticationError

def validate_vertex_ai_credentials(config: Config):
    if config.google_genai_use_vertexai and config.google_application_credentials is None:
        raise AuthenticationError(
            provider_name="google",
            details=(
                "GOOGLE_APPLICATION_CREDENTIALS environment variable is required "
                "when GOOGLE_GENAI_USE_VERTEXAI=true. "
                "Set it to the path of your GCP service account JSON key file. "
                "See: https://cloud.google.com/docs/authentication/application-default-credentials"
            )
        )
```

### Example 3: Cache Corruption with Recovery

```python
from llm_discovery.exceptions import CacheCorruptedError

def load_models_with_recovery():
    try:
        return load_cache()
    except CacheCorruptedError as e:
        print(f"Warning: Cache corrupted at {e.cache_path}")
        print(f"Parse error: {e.parse_error}")
        print("Attempting to fetch fresh data...")

        try:
            models = await fetch_models()
            save_cache(models)
            print("Success: Fresh data retrieved and cached")
            return models
        except ProviderFetchError as fetch_err:
            print(f"Error: Failed to fetch fresh data: {fetch_err}")
            print("Suggested actions:")
            print("  1. Delete the corrupted cache file:")
            print(f"     rm {e.cache_path}")
            print("  2. Ensure internet connection is available")
            print("  3. Retry the command")
            raise
```

## Test Requirements

### Error Message Tests

- `tests/unit/errors/test_error_messages.py`:
  - すべてのエラークラスのメッセージ形式検証
  - "Suggested actions"の存在確認
  - 参考リンクの有効性確認

### Exception Chaining Tests

- `tests/unit/errors/test_exception_chaining.py`:
  - `raise ... from e`が正しく使用されている
  - 元の例外が保持されている
  - トレースバックが正確

### Recovery Strategy Tests

- `tests/integration/errors/test_recovery.py`:
  - キャッシュ破損からのリカバリ
  - リカバリ失敗時のエラー伝播

### Exit Code Tests

- `tests/contract/test_exit_codes.py`:
  - 各エラーカテゴリの終了コード検証
  - CLI実行時の終了コード確認

## References

- **FR-017**: API障害時エラーハンドリング
- **FR-018**: 部分失敗時エラーハンドリング
- **FR-019**: キャッシュ破損リカバリ
- **FR-021**: Vertex AI認証
- **FR-022**: バージョン取得失敗
- **Primary Data Non-Assumption Principle**: CLAUDE.md（グローバル）
- **Edge Cases**: spec.md（API障害、部分失敗、認証エラー等）
