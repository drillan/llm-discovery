# Contract: Content Guidelines

**Feature**: 002-docs | **Version**: 1.0.0 | **Date**: 2025-10-19

## Purpose

llm-discoveryプロジェクトのドキュメントコンテンツ作成ガイドラインを定義する。MyST記法、Admonitionsの使用、コードサンプルの記述方法、スタイルガイドを規定し、ドキュメントの品質と一貫性を保証する。

## MyST Markdown Syntax

### Required Extensions

以下のMyST拡張機能を使用すること:

- **Colon Fence** (`::: directive`): Admonitions、ディレクティブ
- **Deflist**: 定義リスト
- **Tasklist**: タスクリスト（チェックボックス）

### Admonitions

情報の種類に応じて、適切なAdmonitionを使用すること:

#### Note
一般的な補足情報、参考情報に使用。

```markdown
:::{note}
This is a supplementary information that readers should be aware of.
:::
```

**Usage**:
- 追加の背景情報
- 関連トピックへの参照
- 一般的な注意事項

#### Warning
重要な警告、潜在的な問題、注意が必要な事項に使用。

```markdown
:::{warning}
Never commit API keys to version control. Use environment variables instead.
:::
```

**Usage**:
- セキュリティ上の注意
- データ損失の可能性
- 互換性の問題

#### Tip
ベストプラクティス、推奨事項、効率的な使用方法に使用。

```markdown
:::{tip}
Use `uvx llm-discovery` to run the tool without installation.
:::
```

**Usage**:
- 効率的な使用方法
- パフォーマンス最適化
- 便利な機能

#### Important
必須事項、見落としてはならない情報に使用。

```markdown
:::{important}
Python 3.13 or higher is required to run llm-discovery.
:::
```

**Usage**:
- 必須要件
- 重要な前提条件
- 見落としやすい必須手順

#### Caution
慎重に扱うべき事項、推奨されない使用方法に使用。

```markdown
:::{caution}
Running `update` command in CI/CD pipelines may hit rate limits.
:::
```

**Usage**:
- 非推奨の使用方法
- パフォーマンスへの影響
- リソース制限

#### Danger
危険な操作、データ損失の可能性がある事項に使用。

```markdown
:::{danger}
This command will delete all cached data permanently.
:::
```

**Usage**:
- データ削除操作
- 破壊的変更
- 回復不能な操作

### Code Blocks

#### Syntax Highlighting

コードブロックには必ず言語指定を含めること:

```markdown
​```python
from llm_discovery import DiscoveryClient

client = DiscoveryClient()
​```
```

**Supported Languages**:
- `python`: Python code
- `bash`: Shell commands
- `yaml`: YAML configuration
- `json`: JSON data
- `toml`: TOML configuration
- `markdown`: Markdown examples

#### Executable Code

実行可能なコードサンプルは完全な形式で提供すること:

**Good**:
```markdown
​```python
import asyncio
from llm_discovery import DiscoveryClient
from llm_discovery.models.config import Config

async def main():
    config = Config.from_env()
    client = DiscoveryClient(config)
    models = await client.fetch_all_models()
    for provider in models:
        print(f"{provider.provider_name}: {len(provider.models)} models")

asyncio.run(main())
​```
```

**Bad** (incomplete):
```markdown
​```python
client = DiscoveryClient()
models = await client.fetch_all_models()
​```
```

#### Command Examples

CLIコマンド例にはプロンプト記号（`$`）を使用すること:

```markdown
​```bash
$ uvx llm-discovery update
$ uvx llm-discovery list
​```
```

出力例を含む場合:

```markdown
​```bash
$ uvx llm-discovery list
Provider       Model ID              Model Name
─────────────────────────────────────────────────
OpenAI         gpt-4                 GPT-4
OpenAI         gpt-3.5-turbo         GPT-3.5 Turbo
​```
```

### Definition Lists

用語定義には定義リストを使用すること:

```markdown
DiscoveryClient
: The main client class for fetching model data from LLM providers.

ProviderSnapshot
: A snapshot of models available from a specific provider at a point in time.
```

### Task Lists

チェックリストにはタスクリストを使用すること:

```markdown
- [x] Install llm-discovery
- [x] Set up environment variables
- [ ] Run first update command
- [ ] Explore exported data
```

## Writing Style

### Tone

- **Objective**: 客観的で検証可能な表現を使用
- **Clear**: 明確で曖昧さのない記述
- **Concise**: 簡潔で冗長でない文章

### Prohibited Expressions

以下の表現は使用禁止:

- **誇張表現**: 「革新的」「画期的」「驚くべき」「素晴らしい」
- **最上級表現**: 「最高の」「最も優れた」「最速の」
- **主観的表現**: 「簡単に」「すぐに」（具体的な数値で置き換え）

**Bad**:
```markdown
llm-discovery is the best tool for model discovery.
```

**Good**:
```markdown
llm-discovery fetches model data from OpenAI, Google, and Anthropic providers.
```

### Preferred Expressions

具体的で測定可能な表現を使用:

- 「5分以内にセットアップ完了」（「簡単にセットアップ」の代わり）
- 「3つのプロバイダーに対応」（「多くのプロバイダー」の代わり）
- 「エラー率0.1%未満」（「非常に信頼性が高い」の代わり）

### Minimal Formatting

太字（`**bold**`）の使用は最小限に抑えること:

**Allowed**:
- 定義語（初出の重要な用語）
- 重要な概念（セクション内で1-2箇所のみ）

**Not Allowed**:
- 強調のための多用
- 文全体の太字
- 見出しの代わりとしての太字

**Good**:
```markdown
The **DiscoveryClient** class is the main entry point for fetching model data.
```

**Bad**:
```markdown
This is **very important** and you **must** read this **carefully**.
```

### Headings

見出しレベルを適切に使用:

- `#`: ページタイトル（1ページに1つ）
- `##`: 主要セクション
- `###`: サブセクション
- `####`: 詳細セクション（必要な場合のみ）

## Code Sample Requirements

### Completeness

全コードサンプルは以下の要件を満たすこと:

- **Self-contained**: 単独で実行可能
- **Imports included**: 必要なimport文をすべて含む
- **Error handling**: 適切なエラーハンドリングを含む（長い例の場合）

### Accuracy

- **Tested**: 実際に実行して動作確認済み
- **Up-to-date**: 最新のAPI仕様に準拠
- **Contract-compliant**: contractsドキュメントと整合

### Annotations

複雑なコードには適切なコメントを含めること:

```python
# Fetch models from all configured providers
provider_snapshots = await client.fetch_all_models()

# Filter models by specific criteria
openai_models = [
    model for snapshot in provider_snapshots
    if snapshot.provider_name == "openai"
    for model in snapshot.models
]
```

## Contract Integration

### Reference Format

既存contractsドキュメントを参照する場合:

```markdown
For detailed API specifications, see the [Python API Contract](../../001-llm-model-discovery/contracts/python-api.md).
```

### Content Extraction

contractsから情報を抽出する際:

1. **User-friendly rephrasing**: 技術仕様をユーザー視点で言い換え
2. **Example addition**: 実用的なサンプルコードを追加
3. **Context provision**: 使用場面、目的を明確化

**Contract (technical)**:
```markdown
### DiscoveryClient.fetch_all_models()

Returns: `List[ProviderSnapshot]`
Raises: `APIError` if provider API is unavailable
```

**Docs (user-friendly)**:
```markdown
### Fetching Models from All Providers

Use the `fetch_all_models()` method to retrieve model data from all configured providers:

​```python
provider_snapshots = await client.fetch_all_models()
​```

This method returns a list of `ProviderSnapshot` objects, one for each provider. If a provider's API is unavailable, an `APIError` is raised.

:::{tip}
Handle API errors gracefully in production code to avoid service interruption.
:::
```

## Validation Checklist

提出前に以下をチェック:

- [ ] MyST記法に準拠している
- [ ] Admonitionsが適切に使用されている
- [ ] コードサンプルが完全で実行可能
- [ ] 誇張表現・主観的表現が含まれていない
- [ ] 太字の使用が最小限
- [ ] 見出しレベルが適切
- [ ] contractsドキュメントと整合している

## Review Protocol

ドキュメントレビュー時の確認事項:

1. **Technical Accuracy**: コードサンプルが正しいか
2. **MyST Compliance**: 記法が正しいか
3. **Style Compliance**: スタイルガイドに準拠しているか
4. **Contract Sync**: contractsドキュメントと矛盾がないか
5. **Build Success**: `make html` が成功するか
