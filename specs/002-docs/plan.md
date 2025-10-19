# Implementation Plan: プロジェクトドキュメント体系

**Branch**: `002-docs` | **Date**: 2025-10-19 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/002-docs/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

llm-discoveryプロジェクトの包括的なドキュメント体系を構築する。Sphinx + MyST Markdownを使用し、新規ユーザー向けの基本ドキュメント（概要、インストール、クイックスタート）、開発者向けのリファレンス（API、CLI）、高度な使用例、トラブルシューティングガイド、コントリビューションガイドを整備する。既存のcontractsディレクトリ（specs/001-llm-model-discovery/contracts/）の内容と整合性を保ちながら、Read the Docsテーマで統一されたデザインのドキュメントサイトを提供する。

## Technical Context

**Language/Version**: Python 3.13以上（既存プロジェクトと同一）
**Primary Dependencies**: Sphinx 8.0以上、myst-parser 4.0以上、sphinx_rtd_theme 3.0以上
**Storage**: 静的HTMLファイル生成（docs/_build/html/）
**Testing**: ドキュメントビルドテスト（make html）、リンク切れチェック
**Target Platform**: Webブラウザ（デスクトップ、モバイル）、Read the Docs/GitHub Pagesホスティング
**Project Type**: ドキュメンテーションプロジェクト（既存のsingleプロジェクトに統合）
**Performance Goals**: ビルド時間30秒以内、ページロード3秒以内
**Constraints**: MyST記法準拠、既存contractsとの整合性100%、モバイルレスポンシブ対応
**Scale/Scope**: 10-15ページのドキュメント、100以上のコードサンプル

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Article I: Library-First Principle ✅ PASS
- **Status**: N/A（ドキュメンテーションプロジェクトのため適用外）
- **Justification**: ドキュメントは実行可能なライブラリではなく、静的コンテンツ

### Article II: CLI Interface Mandate ✅ PASS
- **Status**: N/A（ドキュメンテーションプロジェクトのため適用外）
- **Justification**: ドキュメントビルドは既存のSphinx CLIを使用（make html）

### Article III: Test-First Imperative (TDD) ✅ PASS
- **Status**: 適用（ドキュメントビルドテスト、リンク切れテスト）
- **Implementation**: Phase 1でビルドテストとバリデーションテストを定義

### Article IV: Integration-First Testing ✅ PASS
- **Status**: 適用（実際のSphinxビルド環境でテスト）
- **Implementation**: モックではなく実際のmake htmlコマンドでテスト

### Article V: Simplicity ✅ PASS
- **Status**: 単一ドキュメントプロジェクト（docs/ディレクトリ）
- **Justification**: 既存プロジェクト構造に統合、追加プロジェクト不要

### Article VI: Anti-Abstraction ✅ PASS
- **Status**: Sphinxの標準機能を直接使用
- **Implementation**: カスタムビルドシステムではなく、標準のSphinx + MyST

### Article VII: Ideal Implementation First ✅ PASS
- **Status**: 最初から完全なドキュメント構造を設計
- **Implementation**: 段階的追加ではなく、全セクションを一括計画

### Article VIII: Error Handling and Quality ✅ PASS
- **Status**: ビルドエラー検出、リンク切れ検出
- **Implementation**: 品質チェックツール（sphinx-build -W）の使用

### Article IX: Documentation Integrity ✅ PASS
- **Status**: 既存contractsドキュメントとの整合性を厳密に保証
- **Implementation**: Phase 0でcontractsとの整合性検証プロトコルを定義

### Article X: Data Accuracy ✅ PASS
- **Status**: コードサンプルは実行可能な完全形式で提供
- **Implementation**: サンプルコードの動作検証を必須化

### Article XI: DRY Principle ✅ PASS
- **Status**: 既存contractsドキュメントを参照・統合
- **Implementation**: 重複記述を避け、contractsから情報を抽出

### Article XII: Destructive Refactoring ✅ PASS
- **Status**: 既存docs/index.mdを破壊的に更新
- **Implementation**: V2ドキュメントではなく、既存ファイルを直接改善

### Article XIII: No Compromise Implementation ✅ PASS
- **Status**: 最初から完全なドキュメント体系を実装
- **Implementation**: 簡易版を作らず、理想的な構造で一括実装

### Article XIV: Branch Management ✅ PASS
- **Status**: 002-docsブランチで作業中
- **Implementation**: mainブランチでの直接作業なし

### Article XV: Record Management ✅ PASS
- **Status**: plan.md、research.mdで意思決定を記録
- **Implementation**: ドキュメント構造の選択理由を明確に記録

### Article XVI: Documentation Style (C015) ✅ PASS
- **Status**: MyST記法、Admonitions活用、客観的表現を厳格適用
- **Implementation**:
  - Phase 1でMyST記法のベストプラクティスを定義
  - Admonitions（note、warning、tip等）の使用ガイドライン策定
  - 装飾最小化プロトコル適用（太字・強調の制限）
  - 客観的・検証可能な表現のみ使用（誇張表現の完全排除）

**GATE RESULT**: ✅ PASS - All articles compliant. Proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```
specs/002-docs/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   ├── documentation-structure.md
│   └── content-guidelines.md
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Documentation Source (repository root)

```
docs/
├── index.md                      # トップページ（概要、ナビゲーション）
├── installation.md               # インストールガイド（uvx、pip、ソース）
├── quickstart.md                 # クイックスタートガイド（環境変数、基本コマンド、Python API）
├── api-reference.md              # Python APIリファレンス（DiscoveryClient、Config等）
├── cli-reference.md              # CLIリファレンス（update、list、export）
├── advanced-usage.md             # 高度な使用例（CI/CD統合、フィルタリング）
├── troubleshooting.md            # トラブルシューティングガイド（エラー解決）
├── contributing.md               # コントリビューションガイド（開発環境、規約）
├── conf.py                       # Sphinx設定ファイル（既存）
├── Makefile                      # ビルドコマンド（既存）
├── _static/                      # 静的ファイル（画像、CSS）
├── _templates/                   # カスタムテンプレート
└── _build/                       # ビルド出力（git ignore）
    └── html/                     # HTMLドキュメント
```

### Integration with Existing Contracts

```
specs/001-llm-model-discovery/contracts/
├── python-api.md                 # → docs/api-reference.md の情報源
├── cli-interface.md              # → docs/cli-reference.md の情報源
├── data-formats.md               # → docs/api-reference.md に統合
├── error-handling.md             # → docs/troubleshooting.md に統合
├── testing-requirements.md       # → docs/contributing.md に統合
└── versioning.md                 # → docs/installation.md、docs/api-reference.md に統合
```

**Structure Decision**:
- 既存のdocs/ディレクトリを拡張する形で実装（新規プロジェクト作成なし）
- Option 1（Single project）構造を採用（ドキュメントのみのため、src/tests/は不要）
- 既存のconf.py、Makefileを活用し、MyST Markdownファイルを追加
- contractsディレクトリの情報を各ドキュメントページに統合・整理

## Complexity Tracking

*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |

