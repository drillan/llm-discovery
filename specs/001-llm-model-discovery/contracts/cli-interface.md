# CLI Interface Contract

**Feature**: [spec.md](../spec.md)
**Data Model**: [data-model.md](../data-model.md)

## Purpose

このドキュメントは、`llm-discovery`コマンドラインインターフェースの契約を定義します。コマンド構造、グローバルオプション、サブコマンドの動作、エラーハンドリング、終了コードの規約を規定し、ユーザーおよびCI/CD環境での一貫した動作を保証します。

## Specification

### Global Command Structure

```bash
llm-discovery [GLOBAL_OPTIONS] [COMMAND] [COMMAND_OPTIONS]
```

### Global Options

#### `--version`

**目的**: パッケージバージョン情報を表示します（FR-022）。

**動作**:
- importlib.metadataを使用してpyproject.tomlから動的に取得
- ハードコーディング禁止（Primary Data Non-Assumption Principle準拠）

**出力形式**:
```
llm-discovery, version X.Y.Z
```

例:
```
llm-discovery, version 0.1.0
```

**エラーハンドリング**:
- バージョン取得に失敗した場合（PackageNotFoundError、AttributeError等）:
  - 明確なエラーメッセージを表示
  - 再インストール手順を含める
  - 終了コード: 1（一般エラー）
  - **フォールバック値（"unknown"、"dev"等）の使用禁止**

エラーメッセージ例:
```
Error: Could not retrieve package version.
This may indicate an improper installation.

Please try reinstalling llm-discovery:
  uv pip install --reinstall llm-discovery

If you installed in editable mode (uv pip install -e .), ensure pyproject.toml is present.
```

#### `--help`

**目的**: 全体的なヘルプメッセージを表示します。

**動作**:
- 利用可能なコマンドの一覧
- グローバルオプションの説明
- 基本的な使用例

**終了コード**: 0（成功）

### Commands

#### `list` - モデル一覧取得

**目的**: マルチプロバイダーから利用可能なモデル一覧を取得し、表示します（FR-001、FR-002、FR-003）。

**構文**:
```bash
llm-discovery list [OPTIONS]
```

**オプション**:
- `--detect-changes`: 前回からの差分を検出（FR-007、オプショナル）

**動作**:

1. **通常実行（`llm-discovery list`）**:
   - キャッシュが存在する場合: キャッシュから読み込み（FR-003）
   - キャッシュが存在しない場合: APIから取得し、キャッシュに保存
   - 出力形式: Rich Tableによる整形されたテーブル表示

2. **差分検出有効（`llm-discovery list --detect-changes`）**:
   - 前回のスナップショットと比較
   - 新規追加・削除されたモデルを検出
   - changes.jsonとCHANGELOG.mdを生成
   - 初回実行時（前回データなし）: ベースラインとして現在のデータを保存

**出力形式（通常実行）**:
```
Provider  | Model ID         | Model Name       | Source | Fetched At
----------|------------------|------------------|--------|-------------------
openai    | gpt-4-turbo      | GPT-4 Turbo     | api    | 2025-10-19 12:00
google    | gemini-1.5-pro   | Gemini 1.5 Pro  | api    | 2025-10-19 12:00
anthropic | claude-3-opus    | Claude 3 Opus   | manual | 2025-10-19 12:00
```

**出力形式（差分検出有効、変更あり）**:
```
Changes detected!

Added models (3):
  openai/gpt-5
  google/gemini-2.0-pro
  anthropic/claude-3.5-opus

Removed models (1):
  openai/gpt-3.5-turbo

Details saved to:
  - changes.json
  - CHANGELOG.md
```

**出力形式（差分検出有効、初回実行）**:
```
No previous snapshot found. Saving current state as baseline.
Next run with --detect-changes will detect changes from this baseline.

Snapshot ID: 550e8400-e29b-41d4-a716-446655440000
```

**エラーハンドリング**:

1. **API障害（FR-017）**:
   - 明確なエラーメッセージ（プロバイダー名、原因、対処法）
   - 終了コード: 1
   - 例:
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

2. **部分失敗（FR-018）**:
   - 部分成功での継続禁止
   - 明確なエラーメッセージ
   - 終了コード: 1
   - 例:
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

3. **Vertex AI認証エラー（Edge Cases）**:
   - 環境変数設定方法を含む
   - GCP認証情報取得手順へのリンク
   - 終了コード: 1
   - 例:
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

4. **キャッシュ破損（FR-019）**:
   - 警告表示
   - API再取得試行
   - 再取得不可の場合はエラーで終了
   - 例:
     ```
     Warning: Cache file is corrupted (TOML parse error).
     Attempting to fetch fresh data from APIs...

     [Success: Fresh data retrieved and cached]
     ```

   再取得不可の場合:
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

**終了コード**:
- 0: 成功
- 1: API障害、部分失敗、キャッシュ破損等

#### `export` - マルチフォーマットエクスポート

**目的**: モデル一覧を指定形式でエクスポートします（FR-005、FR-006）。

**構文**:
```bash
llm-discovery export --format FORMAT [--output PATH]
```

**必須オプション**:
- `--format`: エクスポート形式（`json`、`csv`、`yaml`、`markdown`、`toml`のいずれか）

**オプショナルオプション**:
- `--output PATH`: 出力先ファイルパス（省略時は標準出力）

**動作**:
1. キャッシュからモデルデータを読み込み
2. 指定形式に変換
3. 標準出力またはファイルに書き込み

**出力形式**: [data-formats.md](./data-formats.md)を参照

**エラーハンドリング**:

1. **形式未指定**:
   - 終了コード: 2（コマンドライン引数エラー）
   - 例:
     ```
     Error: --format is required.

     Usage: llm-discovery export --format FORMAT [--output PATH]

     Available formats: json, csv, yaml, markdown, toml
     ```

2. **サポート外形式**:
   - 終了コード: 2
   - 例:
     ```
     Error: Unsupported format 'xml'.

     Available formats: json, csv, yaml, markdown, toml
     ```

3. **ファイル書き込み失敗**:
   - 終了コード: 1
   - 例:
     ```
     Error: Failed to write to file '/readonly/path/output.json'.

     Cause: Permission denied

     Suggested actions:
       1. Check directory permissions
       2. Ensure the directory exists
       3. Try writing to a different location
     ```

4. **キャッシュデータなし**:
   - 終了コード: 1
   - 例:
     ```
     Error: No cached data available.

     Please run 'llm-discovery list' first to fetch model data.
     ```

**終了コード**:
- 0: 成功
- 1: ファイル書き込み失敗、キャッシュデータなし
- 2: コマンドライン引数エラー

### Exit Codes Summary

| Exit Code | Description                      | Examples                                      |
|-----------|----------------------------------|-----------------------------------------------|
| 0         | 成功                             | 正常な実行完了                                |
| 1         | 一般エラー                       | API障害、ファイル破損、書き込み失敗           |
| 2         | コマンドライン引数エラー         | 必須オプション未指定、サポート外形式指定      |

## Examples

### Example 1: バージョン確認

```bash
$ llm-discovery --version
llm-discovery, version 0.1.0
```

### Example 2: モデル一覧取得（初回実行）

```bash
$ llm-discovery list
Fetching models from APIs...

Provider  | Model ID         | Model Name       | Source | Fetched At
----------|------------------|------------------|--------|-------------------
openai    | gpt-4-turbo      | GPT-4 Turbo     | api    | 2025-10-19 12:00
google    | gemini-1.5-pro   | Gemini 1.5 Pro  | api    | 2025-10-19 12:00
anthropic | claude-3-opus    | Claude 3 Opus   | manual | 2025-10-19 12:00

Cached to: ~/.cache/llm-discovery/models_cache.toml
```

### Example 3: オフライン実行（キャッシュから読み込み）

```bash
$ llm-discovery list
Loading from cache...

Provider  | Model ID         | Model Name       | Source | Fetched At
----------|------------------|------------------|--------|-------------------
openai    | gpt-4-turbo      | GPT-4 Turbo     | api    | 2025-10-19 12:00
google    | gemini-1.5-pro   | Gemini 1.5 Pro  | api    | 2025-10-19 12:00
anthropic | claude-3-opus    | Claude 3 Opus   | manual | 2025-10-19 12:00

(Loaded from cache: ~/.cache/llm-discovery/models_cache.toml)
```

### Example 4: 差分検出

```bash
$ llm-discovery list --detect-changes
Changes detected!

Added models (2):
  openai/gpt-5
  google/gemini-2.0-pro

Removed models (1):
  openai/gpt-3.5-turbo

Details saved to:
  - changes.json
  - CHANGELOG.md
```

### Example 5: JSON形式でエクスポート

```bash
$ llm-discovery export --format json --output models.json
Exported 25 models to models.json (JSON format)
```

### Example 6: 標準出力へのエクスポート（パイプライン統合）

```bash
$ llm-discovery export --format csv | grep "openai"
openai,gpt-4-turbo,GPT-4 Turbo,api,2025-10-19T12:00:00Z,"{""context_window"": 128000}"
```

### Example 7: エラーケース（API障害）

```bash
$ llm-discovery list
Error: Failed to fetch models from OpenAI API.

Provider: openai
Cause: Connection timeout (10 seconds)

Suggested actions:
  1. Check your internet connection
  2. Verify OPENAI_API_KEY is set correctly
  3. Check OpenAI status: https://status.openai.com/
  4. Retry the command later

$ echo $?
1
```

## Test Requirements

### Unit Tests

- `tests/unit/cli/test_version.py`:
  - `--version`フラグの出力形式検証
  - バージョン取得成功時の動作
  - バージョン取得失敗時のエラーメッセージ検証

- `tests/unit/cli/test_list_command.py`:
  - `list`コマンドの正常実行
  - `--detect-changes`フラグの動作
  - キャッシュからの読み込み
  - Rich Tableの出力形式検証

- `tests/unit/cli/test_export_command.py`:
  - 各形式へのエクスポート動作
  - `--output`オプションの動作
  - 標準出力への出力

### Integration Tests

- `tests/integration/cli/test_cli_workflow.py`:
  - 初回実行→キャッシュ→差分検出の一連のフロー
  - エクスポート→ファイル生成→内容検証

### Contract Tests

- `tests/contract/test_cli_interface.py`:
  - User Story 1のAcceptance Scenarios（全6シナリオ）
  - User Story 2のAcceptance Scenarios（全5シナリオ）
  - User Story 3のAcceptance Scenarios（全4シナリオ）
  - 終了コードの正確性検証
  - エラーメッセージの内容検証

### Error Handling Tests

- `tests/error/test_cli_errors.py`:
  - API障害時のエラーメッセージ
  - 部分失敗時のエラーメッセージ
  - Vertex AI認証エラー
  - キャッシュ破損エラー
  - バージョン取得失敗エラー

## References

- **FR-001**: マルチプロバイダー対応
- **FR-002**: ハイブリッド取得方式
- **FR-003**: TOMLキャッシュ
- **FR-005**: マルチフォーマットエクスポート
- **FR-006**: 形式最適化
- **FR-007**: 差分検出
- **FR-017**: API障害時エラーハンドリング
- **FR-018**: 部分失敗時エラーハンドリング
- **FR-019**: キャッシュ破損リカバリ
- **FR-022**: バージョン表示
- **User Story 1**: リアルタイムモデル一覧取得
- **User Story 2**: マルチフォーマットエクスポート
- **User Story 3**: 新モデル検知と差分レポート
