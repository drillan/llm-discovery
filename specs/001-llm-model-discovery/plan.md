# Implementation Plan: `update`コマンド追加 - キャッシュ更新と責任分離

**Branch**: `001-llm-model-discovery` | **Date**: 2025-10-19 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-llm-model-discovery/spec.md`

## Summary

既存の`list`コマンドからキャッシュ更新機能を分離し、新規`update`コマンドを追加する。責任の分離原則（Single Responsibility Principle）に基づき、`update`=Write操作（キャッシュ更新）、`list`=Read操作（キャッシュ表示）として明確に区別する。これにより、業界標準（apt update、brew update等）との一貫性を保ち、コードの保守性と理解しやすさを向上させる。

**主要な変更点**:
- 新規`update`コマンド: APIからモデルデータを取得してキャッシュに保存（表示機能なし）
- `list`コマンドの変更: キャッシュからの読み込みと表示のみ（API取得機能を削除）
- `--detect-changes`オプションを`update`コマンドに移動
- 出力形式の明確化: プロバイダー別モデル数、総数、キャッシュパス

## Technical Context

**Language/Version**: Python 3.13以上
**Primary Dependencies**: typer（CLI）、rich（美しい出力）、pydantic v2（データバリデーション・型安全性）、tomli-w（TOML書き込み）、asyncio（非同期処理）、importlib.metadata（バージョン情報取得）
**Storage**: TOML形式のローカルファイルキャッシュ（`~/.cache/llm-discovery/`）、スナップショット履歴（30日間保持）
**Testing**: pytest（テストカバレッジ90%以上必須）、pytest-asyncio（非同期テスト）、pytest-cov（カバレッジ測定）
**Target Platform**: Linux/macOS/Windows（CLI）、uvx対応（インストール不要実行）
**Project Type**: Single（既存プロジェクトへの機能追加）
**Performance Goals**:
- 非同期並行取得により全プロバイダーからの取得時間が最も遅いプロバイダーの応答時間と同等
- キャッシュからの読み込みは1秒未満
**Constraints**:
- API障害時・部分失敗時は明確なエラーメッセージで終了（フォールバック禁止）
- プログレス表示なし（シンプルさ優先、数秒で完了する想定）
- Phase 1では全プロバイダー一括更新のみ（特定プロバイダー指定は将来的拡張）
**Scale/Scope**:
- 3プロバイダー（OpenAI、Google、Anthropic）
- 既存実装への機能追加（新規ファイル: 1、既存ファイル変更: 2、テスト追加: 3以上）

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Initial Check (Pre-Phase 0)

| Article | Status | Notes |
|---------|--------|-------|
| **I: Library-First** | ✅ PASS | 既存ライブラリ構造（llm_discovery）への機能追加。CLI層のみの変更でビジネスロジックは既存のDiscoveryServiceを活用 |
| **II: CLI Interface** | ✅ PASS | typerフレームワークを使用したCLI実装。stdin/stdout/stderrの標準的な使用 |
| **III: Test-First (C010)** | ⚠️ PENDING | TDD必須。実装前にテストケース作成・ユーザー承認が必要 |
| **IV: Integration-First** | ✅ PASS | 既存の統合テスト構造を活用。DiscoveryServiceの実際のインスタンスを使用 |
| **V: Simplicity** | ✅ PASS | 単一プロジェクト構造を維持。新規ファイル1つ、既存ファイル変更2つのみ |
| **VI: Anti-Abstraction** | ✅ PASS | typerフレームワークの標準パターンを使用。不必要な抽象化なし |
| **VII: Ideal Implementation (C004)** | ⚠️ PENDING | 理想実装ファースト原則適用。Phase 0でアーキテクチャを確定 |
| **VIII: Error Handling (C002, C006, C007)** | ⚠️ PENDING | FR-017/FR-018のエラーハンドリング要件を厳格に適用。ruff/mypy/pytest合格必須 |
| **IX: Documentation Integrity (C008)** | ✅ PASS | spec.mdに要件明記済み。FR-024/FR-025/FR-026に詳細定義 |
| **X: Data Accuracy (C011)** | ✅ PASS | Primary Data Non-Assumption Principle準拠。設定値ハードコード禁止 |
| **XI: DRY Principle (C012)** | ✅ PASS | 既存のDiscoveryService、CacheService、SnapshotServiceを再利用 |
| **XII: Destructive Refactoring (C013)** | ✅ PASS | 既存`list`コマンドを破壊的に変更（V2作成せず）。移行パス明確 |
| **XIII: No Compromise (C014)** | ⚠️ PENDING | 妥協実装禁止。最初から最高品質の実装のみを許可 |
| **XIV: Branch Management (C009)** | ✅ PASS | ブランチ`001-llm-model-discovery`で実装中 |
| **XV: Record Management (C005)** | ✅ PASS | spec.md、plan.md、research.md、tasks.mdで記録管理 |

**Gate Decision**: ⚠️ **CONDITIONAL PASS** - Phase 0でTDD戦略、理想実装、エラーハンドリング詳細を確定後にPASS

### Post-Phase 1 Re-check

*(Phase 1完了後に再評価)*

## Project Structure

### Documentation (this feature)

```
specs/001-llm-model-discovery/
├── spec.md              # 仕様書（既存・明確化済み）
├── plan.md              # このファイル（/speckit.plan command output）
├── research.md          # Phase 0 output（/speckit.plan command）
├── data-model.md        # Phase 1 output（/speckit.plan command）
├── quickstart.md        # Phase 1 output（/speckit.plan command）
├── contracts/           # Phase 1 output（/speckit.plan command）
└── tasks.md             # Phase 2 output（/speckit.tasks command - NOT created by /speckit.plan）
```

### Source Code (repository root)

```
llm_discovery/
├── __init__.py
├── __main__.py
├── cli/
│   ├── __init__.py
│   ├── main.py                    # [変更] updateコマンドを登録
│   ├── output.py                  # [既存] 出力ユーティリティ
│   └── commands/
│       ├── __init__.py
│       ├── update.py              # [新規] updateコマンド実装
│       ├── list.py                # [変更] キャッシュ表示のみに変更
│       └── export.py              # [既存] エクスポート機能
├── models/                        # [既存] データモデル
├── services/                      # [既存] ビジネスロジック
│   ├── cache.py                   # [既存] キャッシュサービス
│   ├── discovery.py               # [既存] モデル取得サービス
│   ├── snapshot.py                # [既存] スナップショット管理
│   └── change_detector.py         # [既存] 変更検知
├── constants.py                   # [既存] 定数定義
└── exceptions.py                  # [既存] 例外定義

tests/
├── test_cli.py                    # [変更] updateコマンドのテスト追加、listコマンドのテスト更新
├── test_cache.py                  # [既存] キャッシュサービステスト
├── test_discovery.py              # [既存] ディスカバリーサービステスト
└── conftest.py                    # [既存] テストフィクスチャ
```

**Structure Decision**: 既存の単一プロジェクト構造を維持。CLI層（`llm_discovery/cli/commands/`）のみを変更し、ビジネスロジック層（`llm_discovery/services/`）は既存のまま再利用する。これにより、Article V（Simplicity）およびArticle XI（DRY Principle）に準拠。

## Complexity Tracking

*Fill ONLY if Constitution Check has violations that must be justified*

**現時点で違反なし** - すべての原則に準拠した設計

---

## Phase 0: Outline & Research

### Research Tasks

以下の未解決項目について調査が必要:

1. **既存`list`コマンドからの移行パス**
   - 既存の`list`コマンドのAPI取得ロジックを`update`コマンドにどのように移動するか
   - `--detect-changes`オプションの移行方法
   - 既存テストケースの移行戦略

2. **エラーメッセージの具体的な文言**
   - FR-025: `list`コマンドでキャッシュがない場合のエラーメッセージ
   - FR-017/FR-018: API障害時・部分失敗時のエラーメッセージ詳細
   - ユーザーガイダンスの内容（環境変数設定方法、トラブルシューティング手順）

3. **出力フォーマットの実装詳細**
   - FR-024: プロバイダー別モデル数、総数、キャッシュパスの具体的な表示形式
   - FR-026: 変更検知時の出力形式（変更タイプ別カウント + モデルID/名前のグループ化）
   - richライブラリを使用した視覚的な出力デザイン

4. **テストカバレッジ戦略**
   - 既存の90%カバレッジを維持しつつ、新規コードも同水準に保つ方法
   - `llm_discovery/cli/`がomitされている場合の統合テストでのカバレッジ確保
   - エッジケースのテストケース洗い出し

### Research Output

*(research.mdに記載予定)*

- **Decision**: 既存`list`コマンドのロジックを`update`コマンドに移動し、`list`コマンドは完全にRead専用に変更
- **Rationale**: 責任の分離原則を徹底し、業界標準との一貫性を保つ。保守性向上、テストの容易さ、ユーザーの理解しやすさを実現
- **Alternatives considered**:
  - (A) `list --refresh`オプション追加 → 却下（責任が不明瞭、オプションの増加による複雑化）
  - (B) `update`コマンド追加 + `list`コマンドは後方互換性維持（キャッシュなしで自動取得） → 却下（責任の分離が不徹底）
  - (C) `update`コマンド追加 + `list`コマンドをRead専用に変更 → **採用**（責任の分離徹底、業界標準との一貫性）

---

## Phase 1: Design & Contracts

### Data Model

*(data-model.mdに記載予定)*

**既存のデータモデルを使用** - 新規のデータモデル追加は不要

- `Model`: 既存の`llm_discovery/models/provider.py`で定義済み
- `ProviderSnapshot`: 既存の`llm_discovery/models/provider.py`で定義済み
- `Cache`: 既存の`llm_discovery/services/cache.py`で管理
- `Config`: 既存の`llm_discovery/models/config.py`で定義済み

### API Contracts

*(contracts/に記載予定)*

**CLI Contract - `update`コマンド**:

```yaml
command: llm-discovery update
options:
  --detect-changes:
    type: boolean
    default: false
    description: 変更検知機能を実行
output:
  success:
    format: "プロバイダー別モデル数 / 総数 / キャッシュパス"
    example: "OpenAI: 15, Google: 20, Anthropic: 7 / Total: 42 / Cached to: ~/.cache/llm-discovery/models_cache.toml"
  success_with_changes:
    format: "変更タイプ別カウント + モデルID/名前リスト + キャッシュパス"
    example: |
      Changes detected!

      Added models (3):
        openai/gpt-4.5
        google/gemini-2.0
        anthropic/claude-3.5-opus

      Removed models (1):
        openai/gpt-3.5-turbo-0301

      Details saved to:
        - ~/.cache/llm-discovery/changes.json
        - ~/.cache/llm-discovery/CHANGELOG.md

      Total models: 44 / Cached to: ~/.cache/llm-discovery/models_cache.toml
exit_codes:
  0: 成功
  1: API障害・部分失敗・その他エラー
  2: 認証エラー
```

**CLI Contract - `list`コマンド（変更後）**:

```yaml
command: llm-discovery list
options: なし（--detect-changesオプションを削除）
output:
  success:
    format: "表形式でモデル一覧を表示 + 総数"
  error_no_cache:
    message: "No cached data available. Please run 'llm-discovery update' first to fetch model data."
    exit_code: 1
exit_codes:
  0: 成功
  1: キャッシュなし・その他エラー
```

### Quickstart

*(quickstart.mdに記載予定)*

基本的な使用フロー:

```bash
# 1. 初回または更新時: モデルデータを取得
$ llm-discovery update
OpenAI: 15, Google: 20, Anthropic: 7 / Total: 42 / Cached to: ~/.cache/llm-discovery/models_cache.toml

# 2. モデル一覧を表示
$ llm-discovery list
┌─────────────┬──────────────────────┬─────────┐
│ Provider    │ Model ID             │ Source  │
├─────────────┼──────────────────────┼─────────┤
│ openai      │ gpt-4                │ api     │
│ openai      │ gpt-3.5-turbo        │ api     │
...

Total models: 42

# 3. 変更検知付き更新
$ llm-discovery update --detect-changes
Changes detected!

Added models (3):
  openai/gpt-4.5
  google/gemini-2.0
  anthropic/claude-3.5-opus

Total models: 45 / Cached to: ~/.cache/llm-discovery/models_cache.toml
```

### Agent Context Update

*(Phase 1完了後に実行)*

`.specify/scripts/bash/update-agent-context.sh claude` を実行し、以下の技術スタックをCLAUDE.mdに追加:

- `update`コマンドの責任範囲: キャッシュ更新のみ（Write操作）
- `list`コマンドの責任範囲: キャッシュ表示のみ（Read操作）
- 責任の分離原則（Single Responsibility Principle）の適用

---

## Implementation Notes

### Key Design Decisions

1. **責任の完全分離**: `update`と`list`のコマンド責任を明確に分離し、業界標準（apt、brew、npm等）との一貫性を保つ
2. **破壊的変更の採用**: 既存`list`コマンドを破壊的に変更し、V2クラス作成を回避（Article XII: Destructive Refactoring準拠）
3. **シンプルな出力**: プログレス表示なし、完了後にサマリーのみ表示（数秒で完了する想定）
4. **将来の拡張性**: Phase 1では全プロバイダー一括更新のみ。`--provider`オプションはPhase 2以降で検討

### Risk Mitigations

1. **既存ユーザーへの影響**:
   - `list`コマンドがキャッシュなしでエラーを返すように変更される
   - 明確なエラーメッセージで`update`コマンドの実行を促す
   - ドキュメントとCHANGELOG.mdで変更を明示

2. **テストカバレッジ維持**:
   - 既存の90%カバレッジを維持
   - 新規`update`コマンドも同水準のカバレッジを確保
   - 統合テストで実際のワークフローを検証

3. **エラーハンドリングの厳格性**:
   - FR-017/FR-018に準拠し、フォールバック禁止
   - 明確なエラーメッセージと適切な終了コード
   - ログファイル優先確認原則（C002-1）の適用

### Next Steps

1. **Phase 0 完了**: research.mdの作成（上記Research Tasks完了）
2. **Phase 1 完了**: data-model.md、contracts/、quickstart.mdの作成
3. **Agent Context Update**: update-agent-context.sh実行
4. **Constitution Re-check**: Phase 1後にConstitution Checkを再実行
5. **Phase 2**: `/speckit.tasks`コマンドでtasks.mdを生成し、実装タスクを洗い出し
