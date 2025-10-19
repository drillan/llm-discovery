# Quick Start: Documentation Implementation

**Feature**: 002-docs | **Date**: 2025-10-19 | **Phase**: 1

## Overview

このクイックスタートガイドは、llm-discoveryプロジェクトのドキュメント体系を実装するための手順を提供する。Phase 2（タスク実行）で使用される具体的な実装手順を記述する。

## Prerequisites

### Required Tools

- Python 3.13以上
- Sphinx 8.0以上
- myst-parser 4.0以上
- sphinx_rtd_theme 3.0以上

### Existing Files

以下のファイルが既に存在することを確認:

- `docs/conf.py` - Sphinx設定ファイル
- `docs/Makefile` - ビルドコマンド
- `docs/index.md` - トップページ（更新対象）

## Implementation Steps

### Step 1: Update Sphinx Configuration

`docs/conf.py`にMyST拡張機能を追加:

```python
# docs/conf.py

# 既存の設定を維持しつつ、以下を追加

# MyST拡張機能の有効化
myst_enable_extensions = [
    "colon_fence",      # ::: ディレクティブ（Admonitions）
    "deflist",          # 定義リスト
    "tasklist",         # タスクリスト
]

# Read the Docsテーマオプション
html_theme_options = {
    "navigation_depth": 3,
    "collapse_navigation": False,
}

# バージョン情報の動的取得
from importlib.metadata import version as get_version

release = get_version("llm-discovery")
version = ".".join(release.split(".")[:2])  # Major.Minor
```

### Step 2: Create Documentation Files

以下のドキュメントファイルを作成:

1. **docs/installation.md**
   - uvxによるインストール
   - pipによるインストール
   - ソースからのインストール

2. **docs/quickstart.md**
   - 環境変数の設定
   - 基本コマンド（update、list、export）
   - Python API基本使用例

3. **docs/api-reference.md**
   - DiscoveryClientクラス
   - Configクラス
   - ProviderSnapshotクラス
   - ModelInfoクラス
   - specs/001-llm-model-discovery/contracts/python-api.mdから情報を抽出

4. **docs/cli-reference.md**
   - updateコマンド
   - listコマンド
   - exportコマンド
   - specs/001-llm-model-discovery/contracts/cli-interface.mdから情報を抽出

5. **docs/advanced-usage.md**
   - GitHub Actions統合例
   - GitLab CI統合例
   - プロバイダーフィルタリング
   - カスタムエラーハンドリング

6. **docs/troubleshooting.md**
   - 認証エラー
   - ネットワークエラー
   - レート制限エラー
   - キャッシュ関連の問題
   - specs/001-llm-model-discovery/contracts/error-handling.mdから情報を抽出

7. **docs/contributing.md**
   - 開発環境のセットアップ
   - コーディング規約（ruff、mypy）
   - テスト実行方法
   - プルリクエストのプロセス
   - specs/001-llm-model-discovery/contracts/testing-requirements.mdから情報を抽出

### Step 3: Update index.md

`docs/index.md`を以下の構造で更新:

```markdown
---
title: llm-discovery Documentation
description: LLM model discovery and tracking system documentation
---

# llm-discovery Documentation

LLM model discovery and tracking system for real-time monitoring of available models across multiple providers (OpenAI, Google AI Studio/Vertex AI, Anthropic).

## Features

- Real-time model discovery from multiple LLM providers
- Multi-format export (JSON, CSV, YAML, Markdown, TOML)
- Change detection and tracking
- CI/CD integration support
- Python API and CLI interface
- Offline mode with caching

## Getting Started

```{toctree}
:caption: 'Getting Started'
:maxdepth: 2

installation
quickstart
```

## Reference

```{toctree}
:caption: 'Reference'
:maxdepth: 2

api-reference
cli-reference
```

## Guides

```{toctree}
:caption: 'Guides'
:maxdepth: 2

advanced-usage
troubleshooting
contributing
```
```

### Step 4: Create Build Tests

`tests/test_docs.py`を作成:

```python
import subprocess
import pytest
from pathlib import Path

def test_docs_build():
    """ドキュメントがエラーなくビルドできることを検証"""
    result = subprocess.run(
        ["sphinx-build", "-W", "-b", "html", "docs", "docs/_build/html"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Build failed: {result.stderr}"

def test_docs_no_warnings():
    """ドキュメントビルド時に警告が発生しないことを検証"""
    result = subprocess.run(
        ["sphinx-build", "-W", "-b", "html", "docs", "docs/_build/html"],
        capture_output=True,
        text=True
    )
    assert "warning" not in result.stderr.lower()

def test_all_required_files_exist():
    """必須ドキュメントファイルが存在することを検証"""
    required_files = [
        "docs/index.md",
        "docs/installation.md",
        "docs/quickstart.md",
        "docs/api-reference.md",
        "docs/cli-reference.md",
        "docs/advanced-usage.md",
        "docs/troubleshooting.md",
        "docs/contributing.md",
    ]
    for file_path in required_files:
        assert Path(file_path).exists(), f"{file_path} does not exist"
```

### Step 5: Update Makefile

`docs/Makefile`にlinkcheckターゲットを追加:

```makefile
linkcheck:
	sphinx-build -b linkcheck $(SOURCEDIR) $(BUILDDIR)/linkcheck
```

### Step 6: Build and Validate

ドキュメントをビルドして検証:

```bash
# ビルド
$ cd docs
$ make html

# リンクチェック
$ make linkcheck

# テスト実行
$ cd ..
$ pytest tests/test_docs.py
```

## Content Guidelines Summary

### MyST Syntax

- Admonitions: `:::{note}`, `:::{warning}`, `:::{tip}`, `:::{important}`
- Code blocks: 言語指定必須（```python、```bash等）
- Definition lists: 用語定義に使用
- Task lists: チェックリストに使用

### Writing Style

- 客観的で検証可能な表現
- 誇張表現・主観的表現の禁止
- 太字の使用最小化
- 具体的な数値・測定可能な指標

### Code Samples

- 完全で実行可能なコード
- 必要なimport文をすべて含む
- 適切なコメント・説明

## Contract Integration

既存contractsドキュメントから情報を抽出する際のマッピング:

| Contract | Target Doc | Section |
|----------|-----------|---------|
| python-api.md | api-reference.md | 全セクション |
| cli-interface.md | cli-reference.md | 全セクション |
| data-formats.md | api-reference.md | Export Formats |
| error-handling.md | troubleshooting.md | Error Types |
| testing-requirements.md | contributing.md | Testing |
| versioning.md | installation.md、api-reference.md | Version Info |

## Validation Checklist

実装完了後、以下を確認:

- [ ] `make html` がエラーなく完了
- [ ] `make linkcheck` が成功
- [ ] `pytest tests/test_docs.py` が全パス
- [ ] 全必須ドキュメントファイルが存在
- [ ] toctreeに全ページが含まれている
- [ ] contractsドキュメントとの整合性が取れている
- [ ] MyST記法に準拠している
- [ ] Admonitionsが適切に使用されている
- [ ] コードサンプルが実行可能

## Next Steps

Phase 2（/speckit.tasks）で、このクイックスタートガイドに基づいて具体的なタスクリストを生成し、実装を進める。
