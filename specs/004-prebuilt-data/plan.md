# Implementation Plan: Prebuilt Model Data Support

**Branch**: `004-prebuilt-data` | **Date**: 2025-10-19 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/004-prebuilt-data/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

事前生成されたモデルデータをリポジトリに保存し、APIキー未設定のユーザーでも即座にツールを試用できる機能を追加します。GitHub Actionsで1日1回最新データを自動更新し、ユーザーにはデータソースとタイムスタンプを明示します。APIキー設定により自動的にリアルタイムモードに切り替わります。

## Technical Context

**Language/Version**: Python 3.13（既存プロジェクトと同一）
**Primary Dependencies**:
- 既存: typer（CLI）、rich（出力）、pydantic v2（バリデーション）、tomli-w（TOML書き込み）
- 新規: なし（既存の依存関係で実装可能）

**Storage**: リモートJSON（GitHub: `https://raw.githubusercontent.com/drillan/llm-discovery/main/data/prebuilt/models.json`）
**Testing**: pytest + pytest-asyncio（既存）
**Target Platform**: Linux/macOS/Windows（Python 3.13実行可能環境）
**Project Type**: Single project（CLIツール）
**Performance Goals**:
- 事前生成データ読み込み: 3秒以内（HTTPリクエスト含む）
- リトライ含むタイムアウト: 10秒
- データファイルサイズ: 500KB以内
- モデルリスト表示: 5秒以内（初回、ネットワーク経由）

**Constraints**:
- リポジトリサイズへの影響最小化（データファイル500KB以内）
- 既存のAPI取得機能との互換性維持
- GitHubリポジトリへのコミット権限必要（GitHub Actions用）

**Scale/Scope**:
- 対象プロバイダー: OpenAI、Google、Anthropic
- 想定モデル数: 50-100モデル
- 更新頻度: 1日1回
- データ保持期間: 無期限（最新版のみ保持）

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Article I: Library-First Principle ✅ PASS
- PrebuiltDataLoaderを独立したモジュールとして実装
- 既存のservicesディレクトリ内に配置
- 単体テスト可能な設計

### Article II: CLI Interface Mandate ✅ PASS
- 既存CLIコマンド（list、export）を拡張
- stdout経由でデータソース情報を表示
- エラーはstderrに出力

### Article III: Test-First Imperative ✅ PASS
- Phase 1でコントラクトテスト定義
- 実装前にテストケース作成
- TDDサイクル遵守

### Article IV: Integration-First Testing ✅ PASS
- 実際のJSONファイルを使用した統合テスト
- 既存のfetchersとの統合テスト
- モックは最小限

### Article V: Simplicity ✅ PASS
- 既存プロジェクト構造を維持（追加プロジェクトなし）
- 新規モジュール: PrebuiltDataLoader のみ
- 既存機能の拡張として実装

### Article VI: Anti-Abstraction ✅ PASS
- 標準ライブラリのjsonモジュール使用
- 既存のpydanticモデルを再利用
- 不要な抽象化レイヤーなし

### Article VII: Ideal Implementation First ✅ PASS
- 段階的実装ではなく、完全な機能を一括実装
- メタデータ管理を最初から含める
- リファクタリング前提の設計を排除

### Article VIII: Error Handling and Quality ✅ PASS
- ruff、mypy、pytestによる品質チェック必須
- エラー時の明示的な処理（ファイル不在、破損データ）
- ログファイル優先確認

### Article IX: Documentation Integrity ✅ PASS
- spec.mdとの完全同期
- 実装前にコントラクト定義
- ドキュメント更新をPhase 1に含む

### Article X: Data Accuracy ✅ PASS
- 事前生成データの明示的なタイムスタンプ管理
- データ取得失敗時の明示的エラー
- デフォルト値の推測禁止

### Article XI: DRY Principle ✅ PASS
- 既存のModel、ProviderSnapshotクラスを再利用
- 既存のexporter機能を活用
- コード重複なし

### Article XII: Destructive Refactoring ✅ PASS
- 既存のDiscoveryServiceを直接拡張
- V2クラス作成なし
- 既存インターフェース維持

### Article XIII: No Compromise Implementation ✅ PASS
- 暫定版・簡易版なし
- 最初から完全な機能実装
- 技術的負債の排除

### Article XIV: Branch Management ✅ PASS
- feature/004-prebuilt-dataブランチで作業
- mainブランチへの直接コミットなし

### Article XV: Record Management ✅ PASS
- research.mdで設計判断を記録
- plan.mdで実装計画を文書化

### Article XVI: Documentation Style ✅ PASS
- MyST記法でドキュメント作成
- Admonitions活用
- 客観的表現遵守

**全ゲート合格 - Phase 0研究に進行可能**

## Project Structure

### Documentation (this feature)

```
specs/004-prebuilt-data/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── prebuilt-data-loader.md
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```
llm_discovery/
├── models/
│   ├── __init__.py
│   ├── provider.py           # 既存: Model, ProviderSnapshot
│   └── config.py             # 既存: Config
├── services/
│   ├── __init__.py
│   ├── prebuilt_loader.py    # 新規: PrebuiltDataLoader
│   ├── discovery.py          # 拡張: fetch_or_load_models()追加
│   ├── cache.py              # 既存: CacheService
│   └── exporters/            # 既存: JSON等のエクスポーター
├── cli/
│   └── commands/
│       ├── list.py           # 拡張: データソース表示追加
│       ├── update.py         # 既存: API更新コマンド
│       └── export.py         # 拡張: メタデータ追加
└── exceptions.py             # 既存: カスタム例外

tests/
├── contract/
│   └── test_prebuilt_loader_contract.py   # 新規
├── integration/
│   ├── test_prebuilt_data_integration.py  # 新規
│   └── test_data_source_switching.py      # 新規
└── unit/
    └── services/
        └── test_prebuilt_loader.py        # 新規

data/
└── prebuilt/
    └── models.json                        # 事前生成データ（GitHub Actions生成、リモート参照用）

.github/
└── workflows/
    └── update-prebuilt-data.yml           # 新規: 自動更新ワークフロー

scripts/
└── add-metadata.py                        # 新規: メタデータ追加スクリプト
```

**Structure Decision**: 既存のSingle project構造を維持し、新規モジュール（PrebuiltDataLoader）とGitHub Actionsワークフローを追加します。事前生成データはリポジトリルートの`data/prebuilt/`ディレクトリに保存し、実行時にGitHub上のURLから直接HTTPで取得します。

## Complexity Tracking

*憲法チェック違反なし - 複雑さトラッキング不要*

