# Contract: Documentation Structure

**Feature**: 002-docs | **Version**: 1.0.0 | **Date**: 2025-10-19

## Purpose

llm-discoveryプロジェクトのドキュメント構造、ファイル配置、ナビゲーション階層を定義する。このコントラクトは、ドキュメントの一貫性と保守性を保証する。

## Document Files

### Required Documents

以下のドキュメントファイルは必須であり、常に存在しなければならない:

| ファイル名 | タイトル | 目的 | Priority |
|-----------|---------|------|---------|
| `index.md` | Home | トップページ、プロジェクト概要、ナビゲーション | 0 |
| `installation.md` | Installation | インストール方法（uvx、pip、ソース） | 1 |
| `quickstart.md` | Quick Start | 環境変数設定、基本コマンド、Python API | 2 |
| `api-reference.md` | API Reference | Python API詳細リファレンス | 3 |
| `cli-reference.md` | CLI Reference | CLIコマンド詳細リファレンス | 4 |
| `advanced-usage.md` | Advanced Usage | CI/CD統合、高度な使用例 | 5 |
| `troubleshooting.md` | Troubleshooting | エラー解決、FAQ | 6 |
| `contributing.md` | Contributing | 開発環境、コーディング規約、PR手順 | 7 |

### Optional Documents

以下のドキュメントは任意であり、必要に応じて追加できる:

- `architecture.md`: プロジェクトアーキテクチャ、データフロー
- `changelog.md`: 変更履歴（root CHANGELOGへのリンクでも可）
- `license.md`: ライセンス情報（root LICENSEへのリンクでも可）

## Directory Structure

```
docs/
├── index.md                      # トップページ
├── installation.md               # インストールガイド
├── quickstart.md                 # クイックスタート
├── api-reference.md              # APIリファレンス
├── cli-reference.md              # CLIリファレンス
├── advanced-usage.md             # 高度な使用例
├── troubleshooting.md            # トラブルシューティング
├── contributing.md               # コントリビューションガイド
├── conf.py                       # Sphinx設定
├── Makefile                      # ビルドコマンド
├── _static/                      # 静的ファイル（画像、CSS）
│   └── custom.css               # カスタムスタイル（任意）
├── _templates/                   # カスタムテンプレート（任意）
└── _build/                       # ビルド出力（git ignore）
    ├── html/                    # HTML出力
    └── linkcheck/               # リンクチェック結果
```

## Navigation Hierarchy

### Toctree Configuration

`index.md`のtoctree構造:

```markdown
# llm-discovery Documentation

[Project overview and introduction]

```{toctree}
:caption: 'Getting Started'
:maxdepth: 2

installation
quickstart
```

```{toctree}
:caption: 'Reference'
:maxdepth: 2

api-reference
cli-reference
```

```{toctree}
:caption: 'Guides'
:maxdepth: 2

advanced-usage
troubleshooting
contributing
```
```

### Navigation Levels

- **Level 0**: トップレベル（index.md）
- **Level 1**: 主要カテゴリ（Getting Started、Reference、Guides）
- **Level 2**: 個別ページ（installation.md、api-reference.md等）
- **Level 3**: ページ内セクション（## 見出し）

## File Header Format

全ドキュメントファイルは以下のフォーマットでフロントマターを含めること:

```markdown
---
title: [Page Title]
description: [Brief description]
---

# [Page Title]

[Content starts here]
```

Example:
```markdown
---
title: API Reference
description: Python API documentation for llm-discovery client library
---

# API Reference

This document provides detailed API documentation for the llm-discovery Python library.
```

## Cross-References

### Internal Links

ドキュメント内部リンクはMyST記法のcross-referenceを使用:

```markdown
See the {ref}`installation guide <installation>` for setup instructions.
```

### External Links

外部リンクは標準Markdown記法を使用:

```markdown
For more information, see the [Sphinx documentation](https://www.sphinx-doc.org/).
```

### Contract Integration Links

既存contractsドキュメントへのリンクは相対パスを使用:

```markdown
For detailed API contract, see [python-api.md](../../001-llm-model-discovery/contracts/python-api.md).
```

## Build Configuration

### Sphinx conf.py

必須設定項目:

```python
project = "llm-discovery"
copyright = "2025, driller"
author = "driller"

extensions = [
    "myst_parser",
    "sphinx_rtd_theme",
]

myst_enable_extensions = [
    "colon_fence",      # ::: ディレクティブ（Admonitions）
    "deflist",          # 定義リスト
    "tasklist",         # タスクリスト
]

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

html_theme_options = {
    "navigation_depth": 3,
    "collapse_navigation": False,
}
```

### Makefile Targets

必須ビルドターゲット:

```makefile
html:
	sphinx-build -b html docs docs/_build/html

linkcheck:
	sphinx-build -b linkcheck docs docs/_build/linkcheck

clean:
	rm -rf docs/_build
```

## Validation Requirements

### Build Validation

- `make html` がエラーなく完了すること
- 警告（warnings）が0件であること（`sphinx-build -W`）

### Link Validation

- `make linkcheck` が成功すること
- 内部リンク切れが0件であること
- 外部リンクの404エラーが0件であること

### Structure Validation

- 全必須ドキュメントファイルが存在すること
- toctreeに全必須ページが含まれること
- ナビゲーション順序（priority）が正しいこと

## Versioning

ドキュメントのバージョンはプロジェクトバージョンと同期する:

- プロジェクトバージョン: `pyproject.toml`の`version`フィールド
- ドキュメントバージョン: `conf.py`の`release`変数

```python
# conf.py
from importlib.metadata import version as get_version

release = get_version("llm-discovery")
version = ".".join(release.split(".")[:2])  # Major.Minor
```

## Change Protocol

ドキュメント構造を変更する場合:

1. このコントラクトを更新
2. 変更理由を記録（Why this change?）
3. 影響を受けるファイルをリスト化
4. ユーザーに承認を得る
5. 実装後、バリデーションテストを実行
