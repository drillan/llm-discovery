# Data Formats Contract

**Feature**: [spec.md](../spec.md)
**Data Model**: [data-model.md](../data-model.md)

## Purpose

このドキュメントは、エクスポート形式（JSON、CSV、YAML、Markdown、TOML）の詳細仕様を定義します。各形式は用途に最適化された構造を持ち、User Story 2のAcceptance Scenariosに基づいてテストされます（FR-005、FR-006）。

## Specification

### JSON Format - CI/CD統合最適化

**目的**: CI/CDパイプラインでの自動処理に最適化された形式です。

**用途**:
- GitHub Actions/CI/CDワークフローでの変更検知
- プログラムからのデータ読み込み
- API レスポンスとしての利用

**スキーマ定義（JSONSchema）**:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["metadata", "models"],
  "properties": {
    "metadata": {
      "type": "object",
      "required": ["version", "exported_at", "total_models"],
      "properties": {
        "version": {
          "type": "string",
          "description": "エクスポート形式のバージョン"
        },
        "exported_at": {
          "type": "string",
          "format": "date-time",
          "description": "エクスポート日時（ISO 8601形式）"
        },
        "total_models": {
          "type": "integer",
          "minimum": 0,
          "description": "総モデル数"
        },
        "package_version": {
          "type": "string",
          "description": "llm-discoveryパッケージバージョン"
        }
      }
    },
    "models": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["model_id", "model_name", "provider_name", "source", "fetched_at"],
        "properties": {
          "model_id": {
            "type": "string",
            "description": "モデルの一意識別子"
          },
          "model_name": {
            "type": "string",
            "description": "モデルの表示名"
          },
          "provider_name": {
            "type": "string",
            "enum": ["openai", "google", "anthropic"],
            "description": "プロバイダー名"
          },
          "source": {
            "type": "string",
            "enum": ["api", "manual"],
            "description": "取得方法"
          },
          "fetched_at": {
            "type": "string",
            "format": "date-time",
            "description": "取得タイムスタンプ（ISO 8601形式）"
          },
          "metadata": {
            "type": "object",
            "description": "追加メタデータ"
          }
        }
      }
    }
  }
}
```

**出力例（User Story 2 Scenario 1）**:

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
        "context_window": 128000,
        "training_data_cutoff": "2023-12"
      }
    },
    {
      "model_id": "gemini-1.5-pro",
      "model_name": "Gemini 1.5 Pro",
      "provider_name": "google",
      "source": "api",
      "fetched_at": "2025-10-19T12:00:00Z",
      "metadata": {
        "context_window": 1000000
      }
    },
    {
      "model_id": "claude-3-opus",
      "model_name": "Claude 3 Opus",
      "provider_name": "anthropic",
      "source": "manual",
      "fetched_at": "2025-10-19T12:00:00Z",
      "metadata": {
        "context_window": 200000
      }
    }
  ]
}
```

**Validation Rules**:
- すべての日時はISO 8601形式（`YYYY-MM-DDTHH:MM:SSZ`）
- `provider_name`と`source`は列挙型
- `total_models`は`models`配列の長さと一致
- JSON形式は2スペースインデント

---

### CSV Format - 表計算ソフト分析用

**目的**: Excel、Google Sheetsなどの表計算ソフトで分析可能な形式です。

**用途**:
- モデル比較分析
- 統計処理
- レポート生成

**カラム定義**:

| Column Name    | Type     | Required | Description                     |
|----------------|----------|----------|---------------------------------|
| model_id       | string   | Yes      | モデルの一意識別子              |
| model_name     | string   | Yes      | モデルの表示名                  |
| provider_name  | string   | Yes      | プロバイダー名                  |
| source         | string   | Yes      | 取得方法（api/manual）          |
| fetched_at     | datetime | Yes      | 取得タイムスタンプ（ISO 8601）  |
| metadata       | json     | No       | 追加メタデータ（JSON文字列）    |

**出力例（User Story 2 Scenario 2）**:

```csv
model_id,model_name,provider_name,source,fetched_at,metadata
gpt-4-turbo,GPT-4 Turbo,openai,api,2025-10-19T12:00:00Z,"{""context_window"": 128000, ""training_data_cutoff"": ""2023-12""}"
gemini-1.5-pro,Gemini 1.5 Pro,google,api,2025-10-19T12:00:00Z,"{""context_window"": 1000000}"
claude-3-opus,Claude 3 Opus,anthropic,manual,2025-10-19T12:00:00Z,"{""context_window"": 200000}"
```

**Formatting Rules**:
- ヘッダー行を含む
- ダブルクォートでフィールドを囲む（カンマを含む場合は必須）
- メタデータはJSON文字列としてエスケープ
- 日時はISO 8601形式
- 改行コードはLF（`\n`）

---

### YAML Format - 設定ファイル用

**目的**: 人間が読み書きしやすく、設定ファイルとして利用可能な形式です。

**用途**:
- CI/CD設定ファイルへの埋め込み
- アプリケーション設定
- ドキュメント生成

**階層構造定義**:

```yaml
metadata:
  version: string           # エクスポート形式バージョン
  exported_at: datetime     # エクスポート日時（ISO 8601）
  total_models: integer     # 総モデル数
  package_version: string   # llm-discoveryバージョン

providers:
  <provider_name>:          # openai/google/anthropic
    - model_id: string
      model_name: string
      source: string        # api/manual
      fetched_at: datetime
      metadata: object      # 任意のメタデータ
```

**出力例（User Story 2 Scenario 3）**:

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
        training_data_cutoff: "2023-12"

  google:
    - model_id: gemini-1.5-pro
      model_name: Gemini 1.5 Pro
      source: api
      fetched_at: "2025-10-19T12:00:00Z"
      metadata:
        context_window: 1000000

  anthropic:
    - model_id: claude-3-opus
      model_name: Claude 3 Opus
      source: manual
      fetched_at: "2025-10-19T12:00:00Z"
      metadata:
        context_window: 200000
```

**Formatting Rules**:
- 2スペースインデント
- 日時は引用符で囲む
- プロバイダー別にグループ化
- YAMLバージョン1.2準拠

---

### Markdown Format - ドキュメント用、人間可読

**目的**: GitHub README、ドキュメント、レポートに直接埋め込める形式です。

**用途**:
- ドキュメント生成
- レポート作成
- 社内共有資料

**テーブルレンダリング**:

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

### Google (1 model)

| Model ID | Model Name | Source | Fetched At | Context Window |
|----------|------------|--------|------------|----------------|
| gemini-1.5-pro | Gemini 1.5 Pro | api | 2025-10-19 12:00 | 1,000,000 |

### Anthropic (1 model)

| Model ID | Model Name | Source | Fetched At | Context Window |
|----------|------------|--------|------------|----------------|
| claude-3-opus | Claude 3 Opus | manual | 2025-10-19 12:00 | 200,000 |

---
Generated by [llm-discovery](https://github.com/your-org/llm-discovery)
```

**出力例（User Story 2 Scenario 4）**:

実際の出力は上記のMarkdownテーブル形式で生成されます。

**Formatting Rules**:
- GitHub Flavored Markdown（GFM）準拠
- プロバイダー別にセクション分割
- メタデータから重要な項目を自動抽出してカラムに表示
- 日時は人間可読形式（`YYYY-MM-DD HH:MM`）
- 数値は3桁区切り（カンマ）で表示

---

### TOML Format - 相互運用性・設定ファイル用

**目的**: 他ツールとの相互運用性を重視した形式です。

**用途**:
- 設定ファイルとしての利用
- Rustベースのツールとの連携
- 静的データとしての保存

**セクション構造定義**:

```toml
[metadata]
version = "string"
exported_at = "datetime"
total_models = integer
package_version = "string"

[[models.openai]]
model_id = "string"
model_name = "string"
provider_name = "string"
source = "string"
fetched_at = "datetime"

[models.openai.metadata]
key = "value"

[[models.google]]
# ... 同様の構造

[[models.anthropic]]
# ... 同様の構造
```

**出力例（User Story 2 Scenario 5）**:

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
training_data_cutoff = "2023-12"

[[models.google]]
model_id = "gemini-1.5-pro"
model_name = "Gemini 1.5 Pro"
provider_name = "google"
source = "api"
fetched_at = "2025-10-19T12:00:00Z"

[models.google.metadata]
context_window = 1000000

[[models.anthropic]]
model_id = "claude-3-opus"
model_name = "Claude 3 Opus"
provider_name = "anthropic"
source = "manual"
fetched_at = "2025-10-19T12:00:00Z"

[models.anthropic.metadata]
context_window = 200000
```

**Formatting Rules**:
- TOML v1.0.0準拠
- プロバイダー別に配列テーブルを使用
- 日時はRFC 3339形式（ISO 8601と互換）
- メタデータはインラインテーブルまたはサブセクションとして表現

---

## Format Selection Guidelines

各形式の選択基準:

| Format   | Best For                                  | Pros                                   | Cons                              |
|----------|-------------------------------------------|----------------------------------------|-----------------------------------|
| JSON     | CI/CD統合、プログラム処理                 | パース高速、広範なライブラリサポート   | 人間可読性が低い                  |
| CSV      | Excel分析、統計処理                       | 表計算ソフトで直接開ける               | 階層構造の表現が困難              |
| YAML     | 設定ファイル、ドキュメント                | 人間可読性が高い、コメント可能         | パースが遅い、セキュリティリスク  |
| Markdown | ドキュメント生成、レポート                | GitHub/GitLabで直接表示可能            | 構造化データとしての処理が困難    |
| TOML     | 相互運用性、Rustツール連携                | 型安全、明確な仕様                     | ネストが深いとやや複雑            |

## Test Requirements

### Schema Validation Tests

- `tests/unit/export/test_json_schema.py`:
  - JSONSchemaによる出力検証
  - 必須フィールドの存在確認
  - 型の正確性検証

### Format Compliance Tests

- `tests/unit/export/test_format_compliance.py`:
  - CSV: RFC 4180準拠
  - YAML: YAML 1.2準拠
  - TOML: TOML v1.0.0準拠
  - Markdown: GFM準拠

### Round-Trip Tests

- `tests/integration/export/test_round_trip.py`:
  - エクスポート→インポート→比較で元データと一致
  - JSON、YAML、TOMLで実施
  - メタデータの保持確認

### User Story Acceptance Tests

- `tests/contract/test_data_formats.py`:
  - User Story 2 Scenario 1: JSON形式の出力検証
  - User Story 2 Scenario 2: CSV形式の出力検証
  - User Story 2 Scenario 3: YAML形式の出力検証
  - User Story 2 Scenario 4: Markdown形式の出力検証
  - User Story 2 Scenario 5: TOML形式の出力検証

### Edge Case Tests

- `tests/unit/export/test_edge_cases.py`:
  - 空のモデルリスト
  - 特殊文字を含むモデル名（エスケープ処理）
  - 大量データ（1000モデル以上）
  - Unicode文字列（日本語、絵文字等）
  - メタデータなしのモデル

## Examples

### Example 1: CLI経由のエクスポート

```bash
# JSON形式（CI/CD用）
llm-discovery export --format json --output models.json

# CSV形式（分析用）
llm-discovery export --format csv --output models.csv

# Markdown形式（ドキュメント用）
llm-discovery export --format markdown --output models.md
```

### Example 2: Python API経由のエクスポート

```python
from llm_discovery import DiscoveryClient, export_json, export_csv

async def export_example():
    client = DiscoveryClient()
    models = await client.fetch_models()

    # JSON形式
    json_str = export_json(models)
    print(json_str)

    # CSV形式
    csv_str = export_csv(models)
    print(csv_str)
```

### Example 3: CI/CDパイプラインでの利用

```yaml
# .github/workflows/model-tracking.yml
name: LLM Model Tracking

on:
  schedule:
    - cron: '0 0 * * *'  # 毎日00:00 UTC

jobs:
  track-models:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Fetch latest models
        run: |
          uvx llm-discovery export --format json --output models.json

      - name: Check for changes
        run: |
          if ! git diff --quiet models.json; then
            echo "Models have changed!"
          fi

      - name: Commit changes
        run: |
          git add models.json
          git commit -m "Update model inventory"
          git push
```

## References

- **FR-005**: マルチフォーマットエクスポート
- **FR-006**: 形式最適化
- **User Story 2**: マルチフォーマットエクスポート（全5シナリオ）
- **RFC 4180**: CSV形式仕様
- **YAML 1.2**: YAML仕様
- **TOML v1.0.0**: TOML仕様
- **GitHub Flavored Markdown**: Markdown拡張仕様
