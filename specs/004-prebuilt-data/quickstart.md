# Quick Start: Prebuilt Model Data

**Audience**: End users
**Phase**: 1 - Design & Contracts
**Date**: 2025-10-19
**Status**: Complete

## Overview

llm-discoveryは、APIキーなしで即座に試用できる事前生成データ機能を提供します。このガイドでは、基本的な使い方と、APIキーを設定してリアルタイムデータを取得する方法を説明します。

## Installation

::::{tab-set}

:::{tab-item} uvx (推奨)

APIキーなしで即座に使用できます。

```bash
uvx llm-discovery list
```

:::

:::{tab-item} pip

```bash
pip install llm-discovery
llm-discovery list
```

:::

::::

## Usage Modes

llm-discoveryは2つのモードで動作します：

| Mode | API Keys | Data Source | Data Freshness |
|------|----------|-------------|----------------|
| **Prebuilt Mode** | 不要 | 事前生成データ | 最大24時間遅れ |
| **Real-time Mode** | 必要 | Live APIs | リアルタイム |

:::{tip}
初めて使う場合は、Prebuilt Modeで試してから、必要に応じてAPIキーを設定することをお勧めします。
:::

## Prebuilt Mode (No API Keys Required)

### Basic Commands

モデルリストを表示:

```bash
uvx llm-discovery list
```

出力例:

```
ℹ Using prebuilt data (updated: 2025-10-19 00:00 UTC, age: 12.3h)

Provider       Model ID              Model Name
─────────────────────────────────────────────────
OpenAI         gpt-4                 GPT-4
OpenAI         gpt-3.5-turbo         GPT-3.5 Turbo
Google         gemini-pro            Gemini Pro
Anthropic      claude-3-opus         Claude 3 Opus
```

JSONにエクスポート:

```bash
uvx llm-discovery export --format json --output models.json
```

出力ファイルには、データソース情報が含まれます:

```json
{
  "_metadata": {
    "data_source": "prebuilt",
    "generated_at": "2025-10-19T00:00:00Z",
    "age_hours": 12.3
  },
  "providers": [...]
}
```

### Data Freshness Indicators

データの経過時間に応じて、異なるメッセージが表示されます:

- **< 24時間**: `ℹ Using prebuilt data (age: 12.3h)` （黄色）
- **24-168時間（7日）**: `⚠ Prebuilt data is outdated (age: 48.5h)` （黄色）
- **> 168時間**: `⚠ Prebuilt data is very old (age: 200.1h). Please set API keys.` （赤色）

:::{warning}
データが7日以上古い場合は、APIキーを設定してリアルタイムデータを取得することを強く推奨します。
:::

## Real-time Mode (API Keys Required)

### Setting Up API Keys

環境変数でAPIキーを設定:

::::{tab-set}

:::{tab-item} OpenAI

```bash
export OPENAI_API_KEY="sk-..."
```

APIキーの取得: [OpenAI Platform](https://platform.openai.com/)

:::

:::{tab-item} Google AI Studio

```bash
export GOOGLE_API_KEY="AIza..."
```

APIキーの取得: [Google AI Studio](https://makersuite.google.com/app/apikey)

:::

:::{tab-item} Google Vertex AI

```bash
export GOOGLE_GENAI_USE_VERTEXAI=true
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"
```

認証情報の取得: [Google Cloud Console](https://console.cloud.google.com/)

:::

::::

:::{important}
APIキーは環境変数で管理してください。ファイルにハードコードしたり、バージョン管理システムにコミットしないでください。
:::

### Switching to Real-time Mode

APIキーを設定した後、次回実行時に自動的にリアルタイムモードに切り替わります:

```bash
export OPENAI_API_KEY="sk-..."
uvx llm-discovery list
```

出力例:

```
✓ Fetching latest data from OpenAI API...
✓ Fetching latest data from Google API...
✓ Using prebuilt data for Anthropic (no API key)

Provider       Model ID              Model Name
─────────────────────────────────────────────────
OpenAI         gpt-4                 GPT-4      (API)
OpenAI         gpt-3.5-turbo         GPT-3.5    (API)
Google         gemini-pro            Gemini Pro (API)
Anthropic      claude-3-opus         Claude 3   (Prebuilt)
```

:::{note}
一部のプロバイダーのみAPIキーを設定した場合、そのプロバイダーはリアルタイムデータを取得し、他は事前生成データを使用します。
:::

### Updating Local Cache

最新データを取得してローカルキャッシュに保存:

```bash
uvx llm-discovery update
```

出力例:

```
✓ Fetched 15 models from OpenAI
✓ Fetched 20 models from Google
✓ Using 7 models from Anthropic (prebuilt)

Total: 42 models
Cached to: ~/.cache/llm-discovery/models_cache.toml
```

## Common Workflows

### Workflow 1: Quick Trial (No Setup)

```bash
# No API keys required
uvx llm-discovery list
```

### Workflow 2: Periodic Updates

```bash
# Set API keys once
export OPENAI_API_KEY="sk-..."
export GOOGLE_API_KEY="AIza..."

# Update daily
uvx llm-discovery update

# List models
uvx llm-discovery list
```

### Workflow 3: CI/CD Integration

```yaml
# .github/workflows/check-models.yml
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - name: Check models
        run: |
          # Uses prebuilt data (no API keys needed)
          uvx llm-discovery list --format json > models.json
```

## Troubleshooting

### Error: Prebuilt data not accessible

**Cause**: リモートURLにアクセスできない（ネットワークエラー、GitHub障害）

**Solution**:
1. ネットワーク接続を確認
2. GitHubのステータスを確認: [GitHub Status](https://www.githubstatus.com/)
3. APIキーを設定してリアルタイムモードを使用
4. 少し待ってから再試行

### Error: Network timeout

**Cause**: HTTP リクエストがタイムアウト

**Solution**:
1. ネットワーク速度を確認
2. プロキシ設定を確認（企業ネットワークの場合）
3. APIキーを設定してリアルタイムモードを使用

### Warning: Data is very old

**Cause**: 事前生成データが7日以上更新されていない

**Solution**:
1. APIキーを設定してリアルタイムデータを取得
2. または、GitHubリポジトリの状態を確認（自動更新の失敗可能性）

## Best Practices

:::{tip}
### For Casual Users
- Prebuilt Modeで十分な場合が多い
- APIキー不要で即座に使用可能
:::

:::{tip}
### For Production Use
- APIキーを設定してリアルタイムモードを推奨
- 定期的に `update` コマンドを実行（cron等）
- キャッシュを活用してAPI呼び出しを最小化
:::

:::{tip}
### For CI/CD
- Prebuilt Modeを使用（API rate limit回避）
- 必要に応じてAPI keys をsecrets管理
:::

## Next Steps

- **詳細なドキュメント**: [API Reference](../contracts/prebuilt-data-loader.md)
- **データモデル**: [Data Model](../data-model.md)
- **実装計画**: [Implementation Plan](../plan.md)
- **貢献ガイド**: [CONTRIBUTING.md](../../../CONTRIBUTING.md)

## Feedback

質問やフィードバックは、[GitHub Issues](https://github.com/drillan/llm-discovery/issues) でお待ちしています。
