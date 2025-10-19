# llm-discovery クイックスタートガイド

**最終更新**: 2025-10-19
**バージョン**: 0.1.0

## Introduction

`llm-discovery`は、複数のLLMプロバイダー（OpenAI、Google、Anthropic）から利用可能なモデル一覧をリアルタイムで取得し、変更を追跡するためのCLIツールおよびPython APIです。

### 主要機能

- **リアルタイムモデル一覧取得**: 複数プロバイダーから並行してモデル情報を取得
- **オフライン対応**: キャッシュによるオフライン動作サポート
- **変更検知**: 新規追加・削除されたモデルの自動検出
- **マルチフォーマットエクスポート**: JSON、CSV、YAML、Markdown、TOMLへのエクスポート
- **CI/CD統合**: GitHub Actionsやその他のCI/CDシステムへの簡単な統合
- **Python API**: プログラムからの柔軟な操作

## Prerequisites

### 必須環境

- **Python**: 3.13以上
- **uv**: パッケージマネージャー（推奨）
- **インターネット接続**: 初回取得時およびAPI取得時

### APIキー（オプショナル）

少なくとも1つのプロバイダーのAPIキーを設定することを推奨します：

- **OpenAI**: `OPENAI_API_KEY`
- **Google AI Studio**: `GOOGLE_API_KEY`
- **Google Vertex AI**: `GOOGLE_APPLICATION_CREDENTIALS`（GCPサービスアカウント認証情報）

APIキーがない場合でも、キャッシュデータやAnthropicの手動管理データを利用できます。

## Installation

### オプション1: uvxで即座実行（インストール不要、推奨）

**所要時間**: 即座（SC-001）

```bash
# 実行のみ（インストール不要）
uvx llm-discovery list
```

このコマンドは、パッケージを自動的にダウンロードして実行します。最も簡単な方法です。

### オプション2: pip/uvでインストール

**所要時間**: 5分以内（SC-002）

```bash
# uvを使用（推奨）
uv pip install llm-discovery

# または標準のpip
pip install llm-discovery
```

インストール後：

```bash
llm-discovery --version
# 出力: llm-discovery, version 0.1.0
```

## Quick Start Scenarios

### Scenario 1: リアルタイムモデル一覧取得（User Story 1）

**目的**: DevOpsエンジニアがモデル一覧を即座に取得

#### ステップ1: 環境変数を設定

```bash
# OpenAI
export OPENAI_API_KEY="sk-..."

# Google AI Studio（オプショナル）
export GOOGLE_API_KEY="AIza..."

# Google Vertex AI（オプショナル）
export GOOGLE_GENAI_USE_VERTEXAI=true
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"
```

#### ステップ2: モデル一覧を取得

```bash
# uvxで即座実行（インストール不要）
uvx llm-discovery list
```

#### 期待される出力

```
Fetching models from APIs...

Provider  | Model ID         | Model Name       | Source | Fetched At
----------|------------------|------------------|--------|-------------------
openai    | gpt-4-turbo      | GPT-4 Turbo     | api    | 2025-10-19 12:00
google    | gemini-1.5-pro   | Gemini 1.5 Pro  | api    | 2025-10-19 12:00
anthropic | claude-3-opus    | Claude 3 Opus   | manual | 2025-10-19 12:00

Cached to: ~/.cache/llm-discovery/models_cache.toml
```

#### ステップ3: オフライン実行（キャッシュから取得）

```bash
# 2回目以降の実行はキャッシュを使用
uvx llm-discovery list
```

期待される出力：

```
Loading from cache...

Provider  | Model ID         | Model Name       | Source | Fetched At
----------|------------------|------------------|--------|-------------------
openai    | gpt-4-turbo      | GPT-4 Turbo     | api    | 2025-10-19 12:00
google    | gemini-1.5-pro   | Gemini 1.5 Pro  | api    | 2025-10-19 12:00
anthropic | claude-3-opus    | Claude 3 Opus   | manual | 2025-10-19 12:00

(Loaded from cache: ~/.cache/llm-discovery/models_cache.toml)
```

---

### Scenario 2: マルチフォーマットエクスポート（User Story 2）

**目的**: データサイエンティストが分析用にエクスポート

#### JSON形式（CI/CD統合用）

```bash
uvx llm-discovery export --format json > models.json
```

**用途**: GitHub Actions、CI/CDパイプライン、プログラム処理

**出力例**:

```json
{
  "metadata": {
    "version": "1.0",
    "exported_at": "2025-10-19T12:00:00Z",
    "total_models": 3,
    "package_version": "0.1.0"
  },
  "models": [
    {
      "model_id": "gpt-4-turbo",
      "model_name": "GPT-4 Turbo",
      "provider_name": "openai",
      "source": "api",
      "fetched_at": "2025-10-19T12:00:00Z",
      "metadata": {
        "context_window": 128000
      }
    }
  ]
}
```

#### CSV形式（表計算ソフト用）

```bash
uvx llm-discovery export --format csv > models.csv
```

**用途**: Excel、Google Sheetsでの分析、統計処理

**出力例**:

```csv
model_id,model_name,provider_name,source,fetched_at,metadata
gpt-4-turbo,GPT-4 Turbo,openai,api,2025-10-19T12:00:00Z,"{""context_window"": 128000}"
gemini-1.5-pro,Gemini 1.5 Pro,google,api,2025-10-19T12:00:00Z,"{""context_window"": 1000000}"
```

#### YAML形式（設定ファイル用）

```bash
uvx llm-discovery export --format yaml > models.yaml
```

**用途**: CI/CD設定ファイル、アプリケーション設定

**出力例**:

```yaml
metadata:
  version: "1.0"
  exported_at: "2025-10-19T12:00:00Z"
  total_models: 3
  package_version: "0.1.0"

providers:
  openai:
    - model_id: gpt-4-turbo
      model_name: GPT-4 Turbo
      source: api
      fetched_at: "2025-10-19T12:00:00Z"
      metadata:
        context_window: 128000
```

#### Markdown形式（ドキュメント用）

```bash
uvx llm-discovery export --format markdown > MODELS.md
```

**用途**: GitHub README、社内ドキュメント、レポート

**出力例**:

```markdown
# LLM Model Inventory

**Exported**: 2025-10-19 12:00:00 UTC
**Total Models**: 3
**Package Version**: llm-discovery 0.1.0

## Models by Provider

### OpenAI (1 model)

| Model ID | Model Name | Source | Fetched At | Context Window |
|----------|------------|--------|------------|----------------|
| gpt-4-turbo | GPT-4 Turbo | api | 2025-10-19 12:00 | 128,000 |
```

#### TOML形式（相互運用性）

```bash
uvx llm-discovery export --format toml > models.toml
```

**用途**: Rustツールとの連携、静的データ保存

**出力例**:

```toml
[metadata]
version = "1.0"
exported_at = "2025-10-19T12:00:00Z"
total_models = 3
package_version = "0.1.0"

[[models.openai]]
model_id = "gpt-4-turbo"
model_name = "GPT-4 Turbo"
provider_name = "openai"
source = "api"
fetched_at = "2025-10-19T12:00:00Z"

[models.openai.metadata]
context_window = 128000
```

---

### Scenario 3: 新モデル検知と差分レポート（User Story 3）

**目的**: MLOpsエンジニアが変更を追跡

#### ステップ1: 初回実行（ベースライン作成）

```bash
uvx llm-discovery list --detect-changes
```

**出力**:

```
No previous snapshot found. Saving current state as baseline.
Next run with --detect-changes will detect changes from this baseline.

Snapshot ID: 550e8400-e29b-41d4-a716-446655440000
```

#### ステップ2: 2回目以降の実行（差分検出）

```bash
# 翌日または数時間後に実行
uvx llm-discovery list --detect-changes
```

**出力（変更がある場合）**:

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

#### 生成されるファイル

**changes.json**（CI/CD統合用）:

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

**CHANGELOG.md**（人間可読な変更履歴）:

```markdown
# LLM Model Changes

## 2025-10-19

### Added Models (3)
- openai/gpt-5
- google/gemini-2.0-pro
- anthropic/claude-3.5-opus

### Removed Models (1)
- openai/gpt-3.5-turbo
```

---

### Scenario 4: CI/CD統合とPython API利用（User Story 4）

#### 4-1: GitHub Actions統合

**所要時間**: 10行以内のYAML設定（SC-004）

**ファイル**: `.github/workflows/llm-model-monitor.yml`

```yaml
name: LLM Model Monitor
on:
  schedule:
    - cron: '0 0 * * *'  # 毎日午前0時実行
jobs:
  monitor:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.13'
      - name: Install uv
        run: pip install uv
      - name: Check for new models
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
        run: |
          uvx llm-discovery list --detect-changes
          if [ -f changes.json ]; then
            echo "::warning::New LLM models detected!"
            cat changes.json
          fi
```

**Slack通知の追加**:

```yaml
      - name: Notify Slack
        if: hashFiles('changes.json') != ''
        run: |
          curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"New LLM models detected! Check changes.json for details.\"}" \
            ${{ secrets.SLACK_WEBHOOK_URL }}
```

#### 4-2: Python API利用

**基本的なモデル取得**:

```python
from llm_discovery import DiscoveryClient
import asyncio

async def main():
    client = DiscoveryClient()
    models = await client.fetch_models()

    print(f"Total models: {len(models)}")
    for model in models:
        print(f"{model.provider_name}: {model.model_name}")

asyncio.run(main())
```

**変更検知とSlack通知**:

```python
import asyncio
import httpx
from llm_discovery import DiscoveryClient
from llm_discovery.models import ChangeType

async def monitor_and_notify():
    client = DiscoveryClient()

    # 前回のスナップショットIDを取得（ファイルやDBから）
    previous_id = load_previous_snapshot_id()  # ユーザー実装

    change = await client.detect_changes(previous_id)

    added_models = [
        c for c in change.changes
        if c.change_type == ChangeType.ADDED
    ]

    if added_models:
        message = f"New LLM models detected ({len(added_models)}):\n"
        for c in added_models:
            message += f"  - {c.model_id}\n"

        # Slack通知
        async with httpx.AsyncClient() as http_client:
            await http_client.post(
                "YOUR_SLACK_WEBHOOK_URL",
                json={"text": message}
            )

asyncio.run(monitor_and_notify())
```

## Common Use Cases

### Use Case 1: 定期監視（cron）

**目的**: 毎日午前0時に新モデルを自動チェック

```bash
# crontabに追加
0 0 * * * cd /path/to/project && uvx llm-discovery list --detect-changes >> /var/log/llm-discovery.log 2>&1
```

### Use Case 2: CI/CDでのモデル一覧更新

**目的**: リポジトリに最新のモデル一覧を自動コミット

```yaml
# .github/workflows/update-models.yml
name: Update Model Inventory
on:
  schedule:
    - cron: '0 0 * * 0'  # 毎週日曜日
jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Update models
        run: uvx llm-discovery export --format markdown > docs/MODELS.md
      - name: Commit changes
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add docs/MODELS.md
          git diff --quiet && git diff --staged --quiet || \
            (git commit -m "Update LLM model inventory" && git push)
```

### Use Case 3: Discord/Email通知

**Discord Webhook通知**:

```bash
# changes.jsonが生成された場合に通知
if [ -f changes.json ]; then
  curl -X POST -H 'Content-Type: application/json' \
    -d '{"content":"New LLM models detected! Check the repository for details."}' \
    "YOUR_DISCORD_WEBHOOK_URL"
fi
```

**Email通知（sendmailを使用）**:

```bash
# 新モデル検出時にメール送信
uvx llm-discovery list --detect-changes
if [ -f changes.json ]; then
  echo "New LLM models detected. See attached changes.json" | \
    mail -s "LLM Model Alert" -a changes.json your-email@example.com
fi
```

## Environment Variables

### OpenAI

```bash
export OPENAI_API_KEY="sk-..."
```

**取得方法**: [OpenAI API Keys](https://platform.openai.com/api-keys)

### Google AI Studio

```bash
export GOOGLE_API_KEY="AIza..."
```

**取得方法**: [Google AI Studio](https://makersuite.google.com/app/apikey)

### Google Vertex AI

```bash
export GOOGLE_GENAI_USE_VERTEXAI=true
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"
```

**取得方法**:
1. [GCP Console](https://console.cloud.google.com/)でサービスアカウントを作成
2. JSONキーファイルをダウンロード
3. 環境変数にパスを設定

詳細: [Google Cloud認証ドキュメント](https://cloud.google.com/docs/authentication/application-default-credentials)

### キャッシュディレクトリ（オプショナル）

```bash
# デフォルト: ~/.cache/llm-discovery/ (platformdirs使用)
export LLM_DISCOVERY_CACHE_DIR="/custom/path"
```

### スナップショット保持期間（オプショナル）

```bash
# デフォルト: 30日
export SNAPSHOT_RETENTION_DAYS=60
```

## Troubleshooting

### 1. API Fetch Error

**症状**:

```
Error: Failed to fetch models from OpenAI API.

Provider: openai
Cause: Connection timeout (10 seconds)
```

**対処法**:
1. インターネット接続を確認
2. `OPENAI_API_KEY`が正しく設定されているか確認:
   ```bash
   echo $OPENAI_API_KEY
   ```
3. プロバイダーのステータスページを確認:
   - [OpenAI Status](https://status.openai.com/)
   - [Google Cloud Status](https://status.cloud.google.com/)
4. 数分待ってから再実行

---

### 2. Partial Fetch Error

**症状**:

```
Error: Partial failure during model fetch.

Successful providers:
  - openai (15 models)
  - anthropic (8 models)

Failed providers:
  - google (Connection refused)
```

**対処法**:
1. 失敗したプロバイダーのAPIキーを確認:
   ```bash
   echo $GOOGLE_API_KEY
   ```
2. APIキーを再生成または更新
3. すべてのプロバイダーが正常に動作するまで再実行

**注意**: `llm-discovery`は部分成功での継続を行いません。データ整合性を保つため、すべてのプロバイダーが成功する必要があります。

---

### 3. Vertex AI Authentication Error

**症状**:

```
Error: Vertex AI authentication failed.

GOOGLE_GENAI_USE_VERTEXAI is set to 'true', but GOOGLE_APPLICATION_CREDENTIALS is not set.
```

**対処法**:

1. **サービスアカウントを作成**:
   - [GCP Console](https://console.cloud.google.com/iam-admin/serviceaccounts)でサービスアカウントを作成
   - 適切な権限を付与（Vertex AI User）

2. **JSONキーファイルをダウンロード**:
   - サービスアカウントの詳細ページで「キー」タブを開く
   - 「鍵を追加」→「新しい鍵を作成」→「JSON」を選択

3. **環境変数を設定**:
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
   ```

4. **確認**:
   ```bash
   echo $GOOGLE_APPLICATION_CREDENTIALS
   cat $GOOGLE_APPLICATION_CREDENTIALS | jq
   ```

**詳細ドキュメント**: [Google Cloud認証ガイド](https://cloud.google.com/docs/authentication/application-default-credentials)

---

### 4. Cache Corruption Error

**症状**:

```
Error: Cache file is corrupted and API fetch failed.

Cache file: ~/.cache/llm-discovery/models_cache.toml
Parse error: Expected '=' after key at line 15
```

**対処法**:

1. **キャッシュファイルを削除**:
   ```bash
   rm ~/.cache/llm-discovery/models_cache.toml
   ```

2. **インターネット接続を確認**

3. **コマンドを再実行**:
   ```bash
   uvx llm-discovery list
   ```

**リカバリ成功例**:

```
Warning: Cache file is corrupted (TOML parse error).
Attempting to fetch fresh data from APIs...

[Success: Fresh data retrieved and cached]
```

---

### 5. Version Retrieval Error

**症状**:

```
Error: Could not retrieve package version.
This may indicate an improper installation.
```

**対処法**:

1. **パッケージを再インストール**:
   ```bash
   uv pip install --reinstall llm-discovery
   ```

2. **editable installの場合**:
   ```bash
   # pyproject.tomlが存在することを確認
   ls pyproject.toml

   # editable installを再実行
   uv pip install -e .
   ```

3. **確認**:
   ```bash
   llm-discovery --version
   ```

---

### 6. Permission Denied (ファイル書き込みエラー)

**症状**:

```
Error: Failed to write to file '/readonly/path/output.json'.

Cause: Permission denied
```

**対処法**:

1. **ディレクトリの権限を確認**:
   ```bash
   ls -ld /path/to/directory
   ```

2. **書き込み可能なディレクトリを使用**:
   ```bash
   uvx llm-discovery export --format json --output ~/models.json
   ```

3. **キャッシュディレクトリの権限を確認**:
   ```bash
   ls -ld ~/.cache/llm-discovery/
   chmod 755 ~/.cache/llm-discovery/
   ```

## Next Steps

### 詳細ドキュメント

- **CLI Interface**: [contracts/cli-interface.md](./contracts/cli-interface.md)
  - コマンド構造、オプション、エラーハンドリング、終了コード

- **Python API**: [contracts/python-api.md](./contracts/python-api.md)
  - `DiscoveryClient`クラス、エクスポート関数、例外階層

- **Data Formats**: [contracts/data-formats.md](./contracts/data-formats.md)
  - JSON、CSV、YAML、Markdown、TOMLの詳細仕様

- **Error Handling**: [contracts/error-handling.md](./contracts/error-handling.md)
  - エラーカテゴリ、リカバリ戦略、メッセージフォーマット

- **Data Model**: [data-model.md](./data-model.md)
  - Pydanticモデル、バリデーションルール、エンティティ関係

- **Testing Requirements**: [contracts/testing-requirements.md](./contracts/testing-requirements.md)
  - テスト戦略、カバレッジ要件、テストケース

- **Versioning**: [contracts/versioning.md](./contracts/versioning.md)
  - セマンティックバージョニング、リリースプロセス

### コミュニティ・サポート

- **GitHub Issues**: バグレポート、機能リクエスト
- **GitHub Discussions**: 質問、アイデア共有
- **Contributing Guide**: 貢献ガイドライン（CONTRIBUTING.md）

### 関連ツール

- **llm-registry** (yamanahlawat/llm-registry): 静的なモデルカタログ
  - `llm-discovery`: "何が存在するか"をリアルタイムで発見
  - `llm-registry`: "モデルが何をできるか"の詳細情報

- **LiteLLM**: LLMモデルの実行・推論ツール
  - `llm-discovery`で取得したモデルIDをLiteLLMで使用可能

---

**Happy discovering!** フィードバックや質問がある場合は、GitHubリポジトリでお知らせください。
