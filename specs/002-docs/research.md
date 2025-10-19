# Research: プロジェクトドキュメント体系

**Feature**: 002-docs | **Date**: 2025-10-19 | **Phase**: 0

## Research Objectives

以下の技術的不明点を調査し、Phase 1の設計に必要な意思決定を行う：

1. MyST Markdown記法のベストプラクティス
2. Sphinx + Read the Docsテーマの設定方法
3. 既存contractsドキュメントとの整合性保証方法
4. ドキュメントビルドテストの実装方法
5. リンク切れ検出ツールの選定

## Research Findings

### 1. MyST Markdown記法のベストプラクティス

**Decision**: MyST Parserの標準機能を最大限活用し、Admonitions、Cross-references、Code blocksを積極的に使用する

**Rationale**:
- MyST Parser公式ドキュメント（https://myst-parser.readthedocs.io/）に従うことで、標準的で保守しやすいドキュメントを作成できる
- Admonitions（`:::{note}`、`:::{warning}`等）により、情報の種類を視覚的に区別し、読者の理解を助ける
- Cross-references（`` {ref}`label` ``）により、ドキュメント内のリンクを型安全に管理できる
- Code blocksのシンタックスハイライト（```python、```bash等）により、コードの可読性が向上する

**Alternatives Considered**:
- 標準Markdownのみ使用: MyST拡張機能の恩恵を受けられない
- reStructuredText使用: Markdown経験者にとって学習コストが高い

**Implementation Guidelines**:
- 全ドキュメントファイルは`.md`拡張子を使用
- Admonitions使用基準:
  - `:::{note}`: 補足情報、一般的な注意事項
  - `:::{warning}`: 重要な警告、潜在的な問題
  - `:::{tip}`: ベストプラクティス、推奨事項
  - `:::{important}`: 必須事項、見落としてはならない情報
- 装飾最小化: `**太字**`は定義語、重要な概念のみに使用
- 客観的表現: 「革新的」「画期的」などの誇張表現を禁止

### 2. Sphinx + Read the Docsテーマの設定方法

**Decision**: 既存のconf.pyを拡張し、myst-parserとsphinx_rtd_themeを有効化する

**Rationale**:
- 既存のconf.pyが既にmyst-parserとsphinx_rtd_themeを含んでいる（docs/conf.py:16-19、28）
- 追加設定として、MyST拡張機能（colon_fence、deflist、tasklist）を有効化することで、Admonitionsや定義リスト、タスクリストが使用可能になる
- toctree（Table of Contents）を適切に設定することで、ナビゲーション構造を明確にできる

**Alternatives Considered**:
- Sphinx Book Theme使用: より機能豊富だが、Read the Docsテーマの方がシンプルで業界標準
- カスタムテーマ作成: 保守コストが高く、YAGNI原則に反する

**Implementation Guidelines**:
```python
# conf.pyに追加する設定
myst_enable_extensions = [
    "colon_fence",      # ::: ディレクティブ（Admonitions）
    "deflist",          # 定義リスト
    "tasklist",         # タスクリスト
]

# toctree設定（index.mdで使用）
html_theme_options = {
    "navigation_depth": 3,
    "collapse_navigation": False,
}
```

### 3. 既存contractsドキュメントとの整合性保証方法

**Decision**: contracts/からの情報抽出スクリプトではなく、手動で整合性を確認するプロトコルを確立する

**Rationale**:
- contractsドキュメントは技術仕様であり、ユーザー向けドキュメントは異なる視点で記述される
- 完全な自動同期は困難であり、むしろ定期的な手動レビューの方が品質が高い
- DRY原則に従い、contractsの情報を参照・引用する形で記述することで重複を最小化

**Alternatives Considered**:
- 自動抽出スクリプト: contractsとdocsの形式が異なるため、実装コストが高い
- contractsをそのままコピー: ユーザー視点の説明が欠如する

**Implementation Guidelines**:

**整合性チェックリスト（Phase 1で実施）**:
- [ ] python-api.md と docs/api-reference.md の整合性
  - DiscoveryClient、Config、ProviderSnapshot、ModelInfoのメソッド・引数・戻り値が一致
- [ ] cli-interface.md と docs/cli-reference.md の整合性
  - update、list、exportコマンドのオプション・引数が一致
- [ ] data-formats.md の内容が docs/api-reference.md に反映
  - JSON、CSV、YAML、Markdown、TOMLのフォーマット説明が一致
- [ ] error-handling.md の内容が docs/troubleshooting.md に反映
  - 認証エラー、ネットワークエラー、レート制限エラーの対処法が一致
- [ ] testing-requirements.md の内容が docs/contributing.md に反映
  - テスト要件、実行方法が一致
- [ ] versioning.md の内容が docs/installation.md、docs/api-reference.md に反映
  - バージョン情報の取得方法、互換性情報が一致

**参照方法**:
- contractsの情報を引用する際は、出典を明記（例：「詳細は [python-api.md](../001-llm-model-discovery/contracts/python-api.md) を参照」）
- ユーザー向けに分かりやすく言い換え、サンプルコードを追加

### 4. ドキュメントビルドテストの実装方法

**Decision**: pytest + sphinxビルドコマンドを組み合わせたテストを作成する

**Rationale**:
- Sphinxの`sphinx-build -W`オプションにより、警告をエラーとして扱い、ビルドの成功を厳格に検証できる
- pytestのテストフレームワークにより、ビルドテストをCI/CDパイプラインに統合できる
- 実際のビルド環境でテストすることで、Integration-First Testing原則に準拠

**Alternatives Considered**:
- sphinx-autobuild使用: 開発時のライブリロードには有用だが、テストには不要
- カスタムビルドスクリプト: Sphinxの標準機能で十分

**Implementation Guidelines**:
```python
# tests/test_docs.py
import subprocess
import pytest

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
```

### 5. リンク切れ検出ツールの選定

**Decision**: Sphinxの`linkcheck`ビルダーを使用する

**Rationale**:
- Sphinx標準機能であり、追加の依存関係が不要
- `sphinx-build -b linkcheck docs docs/_build/linkcheck`コマンドで全リンクを検証
- 外部リンク、内部リンク、アンカーリンクを包括的にチェック

**Alternatives Considered**:
- markdown-link-check: 外部ツールであり、Sphinx環境との統合が手間
- 手動チェック: 人的ミスが発生しやすく、スケールしない

**Implementation Guidelines**:
```bash
# Makefileに追加
linkcheck:
	sphinx-build -b linkcheck docs docs/_build/linkcheck

# CI/CDパイプラインに統合
# .github/workflows/docs.yml
- name: Check links
  run: make linkcheck
```

## Summary of Decisions

| 項目 | 決定事項 | Phase 1での実装 |
|------|---------|----------------|
| MyST記法 | Admonitions、Cross-references、Code blocksを積極活用 | content-guidelines.mdでガイドライン策定 |
| Sphinx設定 | conf.pyにMyST拡張機能を追加 | conf.py更新、toctree設定 |
| contracts整合性 | 手動レビュープロトコル確立 | 整合性チェックリスト作成 |
| ビルドテスト | pytest + sphinx-build -W | tests/test_docs.py作成 |
| リンク切れ検出 | sphinx-build -b linkcheck | Makefileにlinkcheckターゲット追加 |

## Open Questions

なし（全ての技術的不明点が解決された）
