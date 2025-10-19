# Implementation Plan: LLMモデル発見・追跡システム

**Branch**: `001-llm-model-discovery` | **Date**: 2025-10-19 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-llm-model-discovery/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

LLMプロバイダー（OpenAI、Google AI Studio/Vertex AI、Anthropic）から利用可能なモデル一覧をリアルタイムで取得し、マルチフォーマットでエクスポート、変更検知、CI/CD統合を実現するPythonパッケージ。uvxによるインストール不要の即座実行、非同期API並行取得、厳格なエラーハンドリング（Primary Data Non-Assumption Principle準拠）、TDD・高カバレッジを徹底する。

## Technical Context

**Language/Version**: Python 3.13以上
**Primary Dependencies**: typer（CLI）、rich（美しい出力）、pydantic v2（データバリデーション・型安全性）、toml（キャッシュ管理）、asyncio（非同期処理）、importlib.metadata（バージョン情報取得）
**Storage**: TOML形式のローカルファイルキャッシュ（`~/.cache/llm-discovery/`）、スナップショット履歴（30日間保持）
**Testing**: pytest（カバレッジ90%以上、FR-020）、ruff（リント）、mypy（型チェック）- 憲章C006-1準拠
**Target Platform**: Linux/macOS/Windows（uvxによるクロスプラットフォーム対応）
**Project Type**: single（CLIツール + Python APIライブラリ）
**Performance Goals**: 複数プロバイダーからの並行取得（最も遅いプロバイダーの応答時間と同等、SC-007）、バージョン取得<10ms（packaging.md CHK024）
**Constraints**: インストール不要で即座実行（uvx）、5分以内のセットアップ（SC-002）、オフライン動作可能（キャッシュ利用）
**Scale/Scope**: 3プロバイダー（OpenAI、Google、Anthropic）、5エクスポート形式（JSON、CSV、YAML、Markdown、TOML）、4主要コマンド（list、export、--detect-changes、--version）

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Article I: Library-First Principle ✅ PASS
- **要件**: すべての機能はスタンドアロンライブラリとして開始
- **評価**: ✅ Python APIライブラリとして実装（FR-014）、CLIは薄いラッパー
- **明確な目的**: LLMモデル情報の発見・追跡という単一責務
- **DRY準拠**: 既存ツール（llm-registry）との補完関係を明示（Scope Boundaries）

### Article II: CLI Interface Mandate ✅ PASS
- **要件**: CLIを通じた機能公開、JSON/人間可読形式サポート
- **評価**: ✅ typerベースのCLI（FR-013）、5形式のエクスポート（JSON、CSV、YAML、Markdown、TOML）
- **テキストI/O**: stdin/stdout/stderr準拠（FR-022で--versionフラグ、エラーメッセージ明記）

### Article III: Test-First Imperative ✅ PASS
- **要件**: TDD必須（Red-Green-Refactor）
- **評価**: ✅ FR-020でカバレッジ90%以上を要求、Contract Tests明示（User Stories各4シナリオ）
- **仕様明確性**: spec.mdで受け入れ基準がGiven-When-Then形式で定義済み

### Article IV: Integration-First Testing ✅ PASS
- **要件**: 実際の環境を使用したテスト、コントラクトテスト必須
- **評価**: ✅ Phase 1でcontracts/生成予定、実際のプロバイダーAPIとの統合テスト必要（FR-001、FR-002）
- **注意点**: モックではなく実際のAPI呼び出しテスト（ただしCI/CDではモック許容）

### Article V: Simplicity ✅ PASS
- **要件**: 初期実装で最大3プロジェクトまで
- **評価**: ✅ 単一プロジェクト（src/、tests/）- Project Type: single
- **YAGNI準拠**: Web UI、モデル実行機能、性能ベンチマーク等をOut of Scopeで明示

### Article VI: Anti-Abstraction ✅ PASS
- **要件**: フレームワーク機能を直接使用、不必要なラッパー禁止
- **評価**: ✅ typer、pydantic v2、asyncio等の標準機能を直接使用
- **DRY準拠**: 既存ライブラリ（importlib.metadata、pathlib等）を優先使用

### Article VII: Ideal Implementation First (C004) ✅ PASS
- **要件**: 最初から理想実装、妥協・段階的改善禁止
- **評価**: ✅ Phase 1-3は機能追加であり、リファクタリングではない
- **Extended Thinking**: 明確化フェーズ（/speckit.clarify）で曖昧性を事前解消済み

### Article VIII: Error Handling and Quality (C002, C006, C007) ✅ PASS
- **要件**: エラー迂回禁止、ruff/mypy/pytest必須、品質妥協禁止
- **評価**:
  - ✅ FR-017、FR-018で明確なエラーハンドリング（フォールバック禁止）
  - ✅ Primary Data Non-Assumption Principle準拠（バージョン情報、API障害時）
  - ✅ ruff/mypy/pytest要件をTechnical Contextに明記
- **C006-1準拠**: pytest（カバレッジ90%）、ruff、mypy実行必須

### Article IX: Documentation Integrity (C008) ✅ PASS
- **要件**: 実装とドキュメントの完全同期、仕様曖昧性検出
- **評価**: ✅ spec.mdで全要件明確化済み、Clarificationsセクションで5つの質問回答済み
- **C008-2チェックリスト**: すべての項目（機能要件、入出力形式、エラーハンドリング、テストケース、パフォーマンス要件）が定義済み

### Article X: Data Accuracy (C011) ✅ PASS
- **要件**: 一次データ推測禁止、フォールバック禁止、設定値ハードコード禁止
- **評価**:
  - ✅ バージョン情報のimportlib.metadata動的取得（ハードコーディング禁止）
  - ✅ API障害時・バージョン取得失敗時はエラーで終了（フォールバック禁止、FR-017、FR-022）
  - ✅ 環境変数による設定管理（GOOGLE_GENAI_USE_VERTEXAI、GOOGLE_APPLICATION_CREDENTIALS）

### Article XI: DRY Principle (C012) ✅ PASS
- **要件**: コード重複禁止、事前調査必須
- **評価**: ✅ 既存ライブラリ使用優先（importlib.metadata、pathlib、asyncio等）
- **C012-1準拠**: llm-registryとの補完関係を調査・文書化済み

### Article XII: Destructive Refactoring (C013) ✅ PASS
- **要件**: V2クラス禁止、既存クラス修正優先
- **評価**: ✅ 新規プロジェクトのため適用外（破壊的変更の対象なし）

### Article XIII: No Compromise Implementation (C014) ✅ PASS
- **要件**: 妥協実装禁止、「とりあえず動く」実装禁止
- **評価**: ✅ Phase 1-3は段階的な機能追加であり、妥協実装ではない
- **C014-4準拠**: Phase 0でresearch.mdによる技術調査を実施予定

### Article XIV: Branch Management (C009) ✅ PASS
- **要件**: feature/XXX形式のブランチ作成必須
- **評価**: ✅ Branch: `001-llm-model-discovery`

### Article XV: Record Management (C005) ✅ PASS
- **要件**: すべての意思決定・設計選択を記録
- **評価**: ✅ Clarificationsセクションで明確化プロセス記録済み、Phase 0でresearch.md生成予定

### **総合評価: ✅ ALL GATES PASSED**

**違反なし**: Complexity Tracking Tableの記入不要

**Phase 0 Research承認**: すべての憲章要件を満たしているため、research.md生成に進む

## Project Structure

### Documentation (this feature)

```
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```
llm_discovery/                    # メインパッケージ（src/ layout不使用）
├── __init__.py                   # __version__公開、DiscoveryClient公開
├── models/                       # Pydanticモデル（data-model.md準拠）
│   ├── __init__.py
│   ├── provider.py               # Provider、Model、Cache、Snapshot、Change
│   └── config.py                 # 環境変数管理、設定モデル
├── services/                     # ビジネスロジック
│   ├── __init__.py
│   ├── discovery.py              # DiscoveryClient（メインAPIエントリポイント）
│   ├── fetchers/                 # プロバイダー別取得ロジック
│   │   ├── __init__.py
│   │   ├── openai.py             # OpenAIFetcher
│   │   ├── google.py             # GoogleFetcher（AI Studio/Vertex AI切り替え）
│   │   └── anthropic.py          # AnthropicFetcher（手動データ読み込み）
│   ├── cache.py                  # キャッシュ管理（TOML読み書き）
│   ├── snapshot.py               # スナップショット保存・履歴管理
│   ├── change_detector.py        # 差分検出アルゴリズム
│   └── exporters/                # エクスポートロジック
│       ├── __init__.py
│       ├── json_exporter.py
│       ├── csv_exporter.py
│       ├── yaml_exporter.py
│       ├── markdown_exporter.py
│       └── toml_exporter.py
├── cli/                          # CLIエントリポイント（typer）
│   ├── __init__.py
│   ├── main.py                   # typerアプリ定義、--versionコールバック
│   ├── commands/
│   │   ├── __init__.py
│   │   ├── list.py               # listコマンド
│   │   └── export.py             # exportコマンド
│   └── output.py                 # Rich出力ユーティリティ
├── data/                         # 静的データ
│   └── anthropic_models.toml     # Anthropic手動管理モデルリスト
└── constants.py                  # 定数定義（キャッシュパス、保持期間等）

tests/
├── contract/                     # コントラクトテスト（contracts/準拠）
│   ├── test_cli_interface.py     # CLI全コマンド・オプション検証
│   └── test_python_api.py        # Python API契約検証
├── integration/                  # 統合テスト（実際のAPI呼び出し）
│   ├── test_openai_integration.py
│   ├── test_google_integration.py
│   └── test_anthropic_integration.py
├── unit/                         # ユニットテスト
│   ├── models/
│   ├── services/
│   └── cli/
└── fixtures/                     # テストデータ、モックレスポンス

pyproject.toml                    # プロジェクト設定、依存関係、バージョン（静的）
README.md                         # 使用方法、インストール手順
CHANGELOG.md                      # 変更履歴（自動生成対象）
.gitignore                        # Python標準パターン
pytest.ini                        # pytest設定（カバレッジ90%）
ruff.toml                         # ruff設定
mypy.ini                          # mypy設定
```

**Structure Decision**:
- **Single project layout**（Article V準拠）: 単一のPythonパッケージとして実装
- **Library-First**（Article I準拠）: `llm_discovery/`がライブラリ、`cli/`が薄いラッパー
- **src/ layout不使用**: `llm_discovery/`を直接配置（uvxとの互換性、シンプルさ優先）
- **テスト分離**: contract/integration/unitの3層構造（Article IV準拠）
- **データ駆動設計**: `data/anthropic_models.toml`で手動管理データを集約
- **設定ファイル集約**: pytest.ini、ruff.toml、mypy.ini で品質ツール設定（C006-1準拠）

## Complexity Tracking

*Fill ONLY if Constitution Check has violations that must be justified*

**No violations**: All constitutional requirements met.

## Phase 1 Design Artifacts (COMPLETED)

✅ **research.md**: 技術調査完了（10項目の技術決定）
✅ **data-model.md**: 6エンティティのPydantic v2モデル定義
✅ **contracts/**: 6つの契約ファイル生成
  - cli-interface.md
  - python-api.md
  - data-formats.md
  - versioning.md
  - error-handling.md
  - testing-requirements.md
✅ **quickstart.md**: User Stories 1-4に基づく実践的シナリオ
✅ **CLAUDE.md**: エージェントコンテキスト更新

## Post-Design Constitution Re-Check

*Re-evaluation after Phase 1 design artifacts generated*

### Article I-VI: 変更なし ✅
Phase 0の評価と同一（Library-First、CLI Mandate、Test-First、Integration-First、Simplicity、Anti-Abstraction）

### Article VII: Ideal Implementation First ✅ CONFIRMED
- **評価**: Phase 1設計は理想実装を前提
- **根拠**: data-model.mdで完全なバリデーション、contracts/で厳格な契約定義
- **妥協なし**: エラーハンドリング、Primary Data Non-Assumption準拠を徹底

### Article VIII: Error Handling and Quality ✅ CONFIRMED
- **評価**: contracts/error-handling.mdで8つのエラーカテゴリを明確化
- **C006-1準拠**: pytest、ruff、mypy要件をcontractcontracts/testing-requirements.mdに明記
- **C002準拠**: Fail-Fast原則をすべての契約に適用

### Article IX: Documentation Integrity ✅ CONFIRMED
- **評価**: 実装前にすべてのドキュメント生成完了（spec.md、plan.md、research.md、data-model.md、contracts/、quickstart.md）
- **C008-2準拠**: すべてのチェックリスト項目が契約で定義済み

### Article X: Data Accuracy ✅ CONFIRMED
- **評価**: data-model.md Config.from_env()でPrimary Data Non-Assumption準拠を実装
- **C011-1〜C011-3準拠**: 環境変数検証、フォールバック禁止、ハードコード禁止をすべて実装

### Article XI-XV: 変更なし ✅
Phase 0の評価と同一（DRY、Destructive Refactoring、No Compromise、Branch Management、Record Management）

### **Phase 1 総合評価: ✅ ALL GATES PASSED（再確認）**

**設計品質**: 理想実装、契約駆動、Primary Data Non-Assumption準拠を達成
**次フェーズ承認**: `/speckit.tasks`でタスク生成に進む準備完了

