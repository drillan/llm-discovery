# Data Model: プロジェクトドキュメント体系

**Feature**: 002-docs | **Date**: 2025-10-19 | **Phase**: 1

## Overview

ドキュメントプロジェクトにおけるデータモデルは、ドキュメントの構造、コンテンツ、メタデータを表現するエンティティで構成される。このドキュメントはドキュメンテーションプロジェクト特有のデータ構造を定義する。

:::{note}
このプロジェクトは静的ドキュメント生成であり、実行時のデータモデル（クラス定義）は存在しない。ここで定義するのは、ドキュメントファイルの構造とメタデータのスキーマである。
:::

## Entities

### DocumentPage

各ドキュメントページ（.mdファイル）を表すエンティティ。

**Attributes**:
- `filename` (string, required): ファイル名（例: `index.md`、`api-reference.md`）
- `title` (string, required): ページタイトル（例: "API Reference"）
- `description` (string, optional): ページの簡潔な説明（メタデータ用）
- `priority` (integer, required): ナビゲーション順序（1が最優先）
- `parent` (string, optional): 親ページのファイル名（階層構造用）
- `toctree_entry` (boolean, required): index.mdのtoctreeに含めるかどうか

**Validation Rules**:
- `filename`は`.md`拡張子必須
- `priority`は1以上の整数
- `parent`が指定された場合、対応するファイルが存在すること

**Example**:
```yaml
filename: api-reference.md
title: API Reference
description: Python API documentation for llm-discovery
priority: 3
parent: null
toctree_entry: true
```

### CodeExample

ドキュメント内のコードサンプルを表すエンティティ。

**Attributes**:
- `language` (string, required): プログラミング言語（例: `python`、`bash`、`yaml`）
- `code` (string, required): コード本文
- `caption` (string, optional): コードブロックのキャプション
- `executable` (boolean, required): 実行可能なコードかどうか
- `filename` (string, optional): コードが記載されているファイル名
- `line_range` (string, optional): 行範囲（例: "1-10"）

**Validation Rules**:
- `language`はサポート対象言語リスト（python、bash、yaml、json、toml、markdown）に含まれること
- `executable=true`の場合、`code`は構文エラーなしで実行可能であること

**Example**:
```yaml
language: python
code: |
  from llm_discovery import DiscoveryClient
  client = DiscoveryClient()
  models = await client.fetch_all_models()
caption: "Basic usage of DiscoveryClient"
executable: true
filename: api-reference.md
line_range: null
```

### NavigationItem

ドキュメントサイトのナビゲーション項目を表すエンティティ。

**Attributes**:
- `label` (string, required): ナビゲーションに表示されるラベル（例: "Quick Start"）
- `link` (string, required): リンク先（相対パス、例: `quickstart.html`）
- `level` (integer, required): 階層レベル（0がトップレベル）
- `parent` (string, optional): 親ナビゲーション項目のラベル
- `order` (integer, required): 同一レベル内での表示順序

**Validation Rules**:
- `level`は0以上の整数
- `parent`が指定された場合、対応するNavigationItemが存在すること
- `link`は有効な相対パスまたはアンカーリンク

**Example**:
```yaml
label: Quick Start
link: quickstart.html
level: 0
parent: null
order: 2
```

### Admonition

MyST記法のAdmonition（注意書き）を表すエンティティ。

**Attributes**:
- `type` (string, required): Admonitionタイプ（note、warning、tip、important、caution、danger）
- `title` (string, optional): カスタムタイトル
- `content` (string, required): Admonitionの内容
- `location` (object, required): 出現場所
  - `filename` (string): ファイル名
  - `section` (string): セクション名

**Validation Rules**:
- `type`はサポート対象タイプ（note、warning、tip、important、caution、danger）に含まれること
- `content`は空でないこと

**Example**:
```yaml
type: warning
title: "API Key Security"
content: "Never commit API keys to version control. Use environment variables instead."
location:
  filename: quickstart.md
  section: "Environment Variables"
```

### ContractReference

既存contractsドキュメントへの参照を表すエンティティ。

**Attributes**:
- `source_contract` (string, required): 参照元contractファイル名（例: `python-api.md`）
- `target_doc` (string, required): 統合先ドキュメントファイル名（例: `api-reference.md`）
- `section` (string, required): 統合先のセクション名
- `sync_status` (string, required): 同期状態（synced、needs_update、conflicting）
- `last_checked` (string, required): 最終確認日時（ISO 8601形式）

**Validation Rules**:
- `source_contract`はspecs/001-llm-model-discovery/contracts/内の有効なファイル
- `target_doc`はdocs/内の有効なファイル
- `sync_status`は定義された値のいずれか
- `last_checked`は有効なISO 8601日時形式

**Example**:
```yaml
source_contract: python-api.md
target_doc: api-reference.md
section: "DiscoveryClient Class"
sync_status: synced
last_checked: "2025-10-19T15:30:00Z"
```

## Relationships

```
DocumentPage 1 ─── * CodeExample
  │
  └─ parent ──> DocumentPage (self-reference)

NavigationItem * ─── 1 DocumentPage
  │
  └─ parent ──> NavigationItem (self-reference)

Admonition * ─── 1 DocumentPage

ContractReference * ─── 1 DocumentPage
```

## Document Structure Schema

トップページ（index.md）のtoctree構造:

```yaml
index.md:
  toctree:
    - installation.md         # Priority 1
    - quickstart.md           # Priority 2
    - api-reference.md        # Priority 3
    - cli-reference.md        # Priority 4
    - advanced-usage.md       # Priority 5
    - troubleshooting.md      # Priority 6
    - contributing.md         # Priority 7
```

## Validation Protocol

ドキュメント品質を保証するための検証プロトコル:

### Build Validation
- Sphinxビルドがエラーなく完了すること（`sphinx-build -W`）
- 全ページがHTMLに正しく変換されること

### Link Validation
- 内部リンクがすべて有効であること（`sphinx-build -b linkcheck`）
- 外部リンクが404エラーを返さないこと

### Code Example Validation
- `executable=true`のコードサンプルが構文エラーなしで実行可能であること
- シンタックスハイライトが正しく適用されていること

### Contract Sync Validation
- 全ContractReferenceの`sync_status`が`synced`または`needs_update`であること
- `conflicting`状態のものが存在する場合、解決されること

### MyST Syntax Validation
- 全AdmonitionがMyST記法に準拠していること
- 不正なディレクティブ記法が存在しないこと

## File Metadata Template

各ドキュメントファイルのフロントマター（メタデータ）テンプレート:

```yaml
---
title: [Page Title]
description: [Brief description for SEO and navigation]
priority: [Integer for navigation order]
---
```

Example:
```yaml
---
title: API Reference
description: Python API documentation for llm-discovery client library
priority: 3
---
```
