# Quickstart: `update`コマンド実装

## Overview

このドキュメントでは、新規追加された`update`コマンドと変更された`list`コマンドの基本的な使用方法を説明します。

## Key Changes

### 責任の分離（Single Responsibility Principle）

- **`update`コマンド**: APIからモデルデータを取得してキャッシュに保存（Write操作）
- **`list`コマンド**: キャッシュからモデルデータを読み込んで表示（Read操作）

### Breaking Changes

⚠️ **重要**: `list`コマンドの動作が変更されました：

1. **キャッシュなしでエラーを返す**: 従来の自動API取得機能を削除
2. **`--detect-changes`オプションの削除**: `update`コマンドに移動

## Prerequisites

### Environment Variables

#### For OpenAI

```bash
export OPENAI_API_KEY="sk-..."
```

#### For Google AI Studio

```bash
export GOOGLE_API_KEY="AIza..."
```

#### For Vertex AI

```bash
export GOOGLE_GENAI_USE_VERTEXAI="true"
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

#### Optional

```bash
export LLM_DISCOVERY_CACHE_DIR="~/.cache/llm-discovery"  # Default
export LLM_DISCOVERY_RETENTION_DAYS="30"                # Default
```

## Basic Workflow

### 1. 初回実行: モデルデータを取得

```bash
$ llm-discovery update
OpenAI: 15, Google: 20, Anthropic: 7 / Total: 42 / Cached to: ~/.cache/llm-discovery/models_cache.toml
```

**動作**:
- 全プロバイダーからAPIでモデルデータを並行取得
- TOML形式でキャッシュに保存
- プロバイダー別モデル数、総数、キャッシュパスを表示

### 2. モデル一覧を表示

```bash
$ llm-discovery list
┌─────────────┬──────────────────────┬─────────┬─────────────────────┐
│ Provider    │ Model ID             │ Source  │ Fetched At          │
├─────────────┼──────────────────────┼─────────┼─────────────────────┤
│ openai      │ gpt-4                │ api     │ 2025-10-19 10:30:15 │
│ openai      │ gpt-3.5-turbo        │ api     │ 2025-10-19 10:30:15 │
│ google      │ gemini-pro           │ api     │ 2025-10-19 10:30:16 │
│ anthropic   │ claude-3-opus        │ manual  │ 2025-10-19 10:30:17 │
└─────────────┴──────────────────────┴─────────┴─────────────────────┘

Total models: 42
```

**動作**:
- キャッシュからモデルデータを読み込み
- Rich table形式で表示
- キャッシュが存在しない場合はエラー

### 3. キャッシュを更新

```bash
$ llm-discovery update
OpenAI: 16, Google: 20, Anthropic: 7 / Total: 43 / Cached to: ~/.cache/llm-discovery/models_cache.toml
```

**動作**:
- 最新のモデルデータで既存キャッシュを上書き
- 更新後のサマリーを表示

## Change Detection Workflow

### 1. 初回実行: ベースライン作成

```bash
$ llm-discovery update --detect-changes
No previous snapshot found. Saving current state as baseline.
Next run with --detect-changes will detect changes from this baseline.

Snapshot ID: 3fa85f64-5717-4562-b3fc-2c963f66afa6

Total models: 42 / Cached to: ~/.cache/llm-discovery/models_cache.toml
```

**動作**:
- 前回スナップショットが存在しないため、現在のデータをベースラインとして保存
- スナップショットIDを表示

### 2. 変更検知: 新モデル追加検出

```bash
$ llm-discovery update --detect-changes
Changes detected!

Added models (3):
  openai/gpt-4.5
  google/gemini-2.0
  anthropic/claude-3.5-opus

Removed models (1):
  openai/gpt-3.5-turbo-0301

Details saved to:
  - ~/.cache/llm-discovery/changes.json
  - ~/.cache/llm-discovery/CHANGELOG.md

Total models: 44 / Cached to: ~/.cache/llm-discovery/models_cache.toml
```

**動作**:
- 前回のスナップショットと比較
- 追加・削除されたモデルをグループ化して表示
- changes.jsonとCHANGELOG.mdに記録
- 新しいスナップショットを保存

### 3. 変更なし

```bash
$ llm-discovery update --detect-changes
No changes detected.

Total models: 44 / Cached to: ~/.cache/llm-discovery/models_cache.toml
```

**動作**:
- 変更がない場合はその旨を表示
- キャッシュは最新データで更新

## Error Handling

### Cache Not Found (list command)

```bash
$ llm-discovery list
No cached data available. Please run 'llm-discovery update' first to fetch model data.
```

**Exit Code**: 1

**Solution**: `llm-discovery update`を実行してキャッシュを作成

### API Failure (update command)

```bash
$ llm-discovery update
Failed to fetch models from openai API.

Cause: Connection timeout

Suggested actions:
  1. Check your internet connection
  2. Verify API keys are set correctly
  3. Check provider status pages
  4. Retry the command later
```

**Exit Code**: 1

**Solution**: エラーメッセージの指示に従って対処

### Partial Failure (update command)

```bash
$ llm-discovery update
Partial failure during model fetch.

Successful providers: google, anthropic
Failed providers: openai

To ensure data consistency, processing has been aborted.
Please resolve the issue with the failed provider and retry.
```

**Exit Code**: 1

**Solution**: 失敗したプロバイダーのAPIキーと接続を確認後、再実行

### Authentication Failure (update command)

```bash
$ llm-discovery update
Authentication failed for openai.

Details: Invalid API key

Please check your API keys and credentials.
```

**Exit Code**: 2

**Solution**: `OPENAI_API_KEY`環境変数を確認

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Monitor LLM Models

on:
  schedule:
    - cron: '0 0 * * *'  # Daily at midnight

jobs:
  monitor:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.13'

      - name: Install llm-discovery
        run: uvx llm-discovery@latest --version

      - name: Update and detect changes
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
        run: |
          uvx llm-discovery update --detect-changes

      - name: Upload changes.json
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: model-changes
          path: ~/.cache/llm-discovery/changes.json
```

## Migration from Old Workflow

### Old Workflow (Before update command)

```bash
# 初回実行 - listコマンドが自動的にAPIから取得
$ llm-discovery list

# 変更検知
$ llm-discovery list --detect-changes
```

### New Workflow (After update command)

```bash
# 初回実行 - updateコマンドで明示的にデータ取得
$ llm-discovery update

# モデル一覧表示
$ llm-discovery list

# 変更検知
$ llm-discovery update --detect-changes
```

## Best Practices

1. **定期的な更新**: CI/CDで`llm-discovery update --detect-changes`を定期実行
2. **エラーハンドリング**: Exit codeを確認してCI/CDパイプラインを制御
3. **キャッシュの活用**: オフライン環境では`list`コマンドのみで動作
4. **変更追跡**: CHANGELOG.mdを自動生成してドキュメント化

## Troubleshooting

### Problem: `list`コマンドで「No cached data available」エラー

**Solution**: `llm-discovery update`を先に実行してキャッシュを作成してください。

### Problem: `update`コマンドが遅い

**Check**:
- 非同期並行取得により、最も遅いプロバイダーの応答時間と同等になる設計
- ネットワーク接続状況を確認

### Problem: 特定のプロバイダーのみ更新したい

**Note**: Phase 1では全プロバイダー一括更新のみをサポート。`--provider`オプションはPhase 2以降で検討予定。

## Next Steps

- `/speckit.tasks`コマンドでtasks.mdを生成し、実装タスクを洗い出し
- TDD（Test-First）に従ってテストケースを作成
- 実装開始
