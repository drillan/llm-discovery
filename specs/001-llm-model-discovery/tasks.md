# Implementation Tasks: `update`コマンド追加 - キャッシュ更新と責任分離

**Feature Branch**: `001-llm-model-discovery`
**Date**: 2025-10-19
**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

## Summary

既存の`list`コマンドからキャッシュ更新機能を分離し、新規`update`コマンドを追加する。責任の分離原則に基づき、`update`=Write操作、`list`=Read操作として明確に区別する。

**変更ファイル**:
- 新規: `llm_discovery/cli/commands/update.py` (1ファイル)
- 変更: `llm_discovery/cli/main.py`, `llm_discovery/cli/commands/list.py` (2ファイル)
- テスト変更: `tests/test_cli.py` (1ファイル)

## Constitution Compliance

- ✅ **Article III (Test-First - C010)**: すべての実装前にテストを作成し、Red-Green-Refactorサイクルに従う
- ✅ **Article VIII (Error Handling - C002, C006)**: ruff/mypy/pytest合格必須、エラー迂回禁止
- ✅ **Article XII (Destructive Refactoring - C013)**: 既存`list`コマンドを破壊的に変更（V2作成禁止）

## User Story Mapping

| User Story | Phase | Tasks | Priority |
|-----------|-------|-------|----------|
| **US1**: キャッシュ更新とモデル一覧表示 | Phase 3 | T010-T021 | P1 (MVP) |
| **US2**: マルチフォーマットエクスポート | - | 既存実装（変更なし） | P2 |
| **US3**: 新モデル検知と差分レポート | Phase 4 | T022-T026 | P3 |
| **US4**: CI/CD統合とPython API利用 | - | 既存実装（変更なし） | P4 |

**注記**: US2とUS4は既に実装済みのため、本タスクリストでは扱わない。US1（MVP）とUS3のみを実装する。

---

## Phase 1: Setup & Prerequisites

### Goal
プロジェクト環境の準備と既存コードの理解。

### Tasks

- [ ] T001 既存`list`コマンド実装の詳細分析（llm_discovery/cli/commands/list.py全203行を読み込み、API取得ロジック・変更検知ロジック・キャッシュ破損リカバリを特定）
- [ ] T002 既存テストケースの分析（tests/test_cli.py内のTestCLIListクラスを読み込み、移行が必要なテストケースを洗い出し）
- [ ] T003 Constitution Check実施（.specify/memory/constitution.md全15条を確認し、Article III, VIII, XII, XIIIの遵守を確保）
- [ ] T004 開発環境のセットアップ確認（ruff check .、mypy .、pytest --cov=llm_discovery --cov-fail-under=90を実行し、すべて合格することを確認）

**Completion Criteria**:
- [ ] 既存コードの構造を完全に理解
- [ ] 移行が必要なコード箇所とテストケースを特定
- [ ] 開発環境がすべての品質チェックに合格

---

## Phase 2: Foundational Tasks

### Goal
すべてのユーザーストーリーで共通して使用する基盤コードの整備。

### Tasks

なし（既存のDiscoveryService、CacheService、SnapshotService、ChangeDetectorをそのまま使用）

---

## Phase 3: User Story 1 - キャッシュ更新とモデル一覧表示 (P1 - MVP)

### Story Goal
DevOpsエンジニアが、`update`コマンドでAPIからモデルデータを取得してキャッシュし、`list`コマンドでキャッシュから表示できる。

### Independent Test Criteria
- ✅ `llm-discovery update` を実行して、プロバイダー別モデル数、総数、キャッシュパスが表示される
- ✅ `llm-discovery list` でキャッシュからモデル一覧が表形式で表示される
- ✅ キャッシュなしで `list` を実行すると明確なエラーメッセージが表示される
- ✅ API障害時・部分失敗時に明確なエラーメッセージが表示される

### Acceptance Scenarios (from spec.md)
1. 初回実行時に`update`でキャッシュ作成、サマリー表示
2. キャッシュ存在時に`update`で更新、サマリー表示
3. キャッシュ存在時に`list`で表形式表示
4. キャッシュなしで`list`を実行するとエラー（exit code 1）
5. API障害発生中に`update`を実行するとエラー（exit code 1）
6. 一部プロバイダー障害時に`update`を実行するとエラー（exit code 1）
7. Vertex AI使用時にモデル取得成功
8. Vertex AI認証情報未設定時にエラー

### Tests (Test-First - Article III)

#### Update Command Tests

- [ ] T010 [P] [US1] テスト作成: `update`コマンド基本動作（tests/test_cli.py内TestCLIUpdate.test_update_fetch_and_cache）- キャッシュ作成、サマリー表示、exit code 0を検証
- [ ] T011 [P] [US1] テスト作成: `update`コマンドキャッシュ更新（tests/test_cli.py内TestCLIUpdate.test_update_updates_existing_cache）- 既存キャッシュの上書き、更新後のサマリー表示を検証
- [ ] T012 [P] [US1] テスト作成: API障害時のエラーハンドリング（tests/test_cli.py内TestCLIUpdate.test_update_api_failure）- FR-017準拠、明確なエラーメッセージ、exit code 1を検証
- [ ] T013 [P] [US1] テスト作成: 部分失敗時のエラーハンドリング（tests/test_cli.py内TestCLIUpdate.test_update_partial_failure）- FR-018準拠、フェイルファスト動作、exit code 1を検証
- [ ] T014 [P] [US1] テスト作成: 認証エラー時の動作（tests/test_cli.py内TestCLIUpdate.test_update_authentication_error）- 明確なエラーメッセージ、exit code 2を検証
- [ ] T015 [P] [US1] テスト作成: キャッシュ破損時の自動リカバリ（tests/test_cli.py内TestCLIUpdate.test_update_corrupted_cache_recovery）- 警告表示、API再取得、成功を検証

#### List Command Tests (Modified)

- [ ] T016 [P] [US1] テスト作成: `list`コマンド基本動作（tests/test_cli.py内TestCLIList.test_list_from_cache）- キャッシュから読み込み、表形式表示、exit code 0を検証
- [ ] T017 [P] [US1] テスト作成: キャッシュなし時のエラー（tests/test_cli.py内TestCLIList.test_list_without_cache_shows_error）- FR-025準拠、明確なエラーメッセージ「No cached data available. Please run 'llm-discovery update' first to fetch model data.」、exit code 1を検証
- [ ] T018 [P] [US1] テスト作成: キャッシュ破損時のエラー（tests/test_cli.py内TestCLIList.test_list_corrupted_cache_error）- 明確なエラーメッセージ、exit code 1を検証

#### Test Review & Approval (Article III - TDD)

- [ ] T019 [US1] **STOP HERE**: すべてのテストケース（T010-T018）をユーザーに提示し、承認を得る。承認なしで実装を進めてはならない（Article III準拠）

### Implementation

#### Update Command Implementation

- [ ] T020 [US1] `update`コマンド実装（llm_discovery/cli/commands/update.py新規作成）- 既存`list`コマンド（行58-103）からAPI取得ロジックを移動、FR-024準拠のサマリー出力実装、Article XII準拠のコード移動
- [ ] T021 [US1] `update`コマンド登録（llm_discovery/cli/main.py変更）- `from llm_discovery.cli.commands.update import update_command`を追加、`app.command(name="update")(update_command)`を登録

#### List Command Modification (Destructive Refactoring)

- [ ] T022 [US1] `list`コマンド修正（llm_discovery/cli/commands/list.py破壊的変更）- API取得ロジック（行58-103）削除、`--detect-changes`オプション削除、キャッシュなし時のエラー処理（FR-025）実装、Article XII準拠

#### Quality Assurance

- [ ] T023 [US1] 品質チェック実行（ruff check .、mypy .、pytest実行）- Article VIII (C006-1)準拠、すべてのツールが合格必須、失敗時は実装を修正
- [ ] T024 [US1] カバレッジ確認（pytest --cov=llm_discovery --cov-fail-under=90実行）- 90%以上のカバレッジ維持、Article VIII (C006-1)準拠
- [ ] T025 [US1] 統合テスト実行（tests/test_cli.py内全テストケース実行）- すべてのテストが合格することを確認、Article III準拠のGreenフェーズ確認

### Completion Criteria
- [ ] すべてのテストが合格（T010-T018）
- [ ] `update`コマンドがFR-024に準拠してサマリーを表示
- [ ] `list`コマンドがFR-025に準拠してキャッシュなし時にエラー表示
- [ ] ruff、mypy、pytestがすべて合格
- [ ] テストカバレッジが90%以上

---

## Phase 4: User Story 3 - 新モデル検知と差分レポート (P3)

### Story Goal
MLOpsエンジニアが、`update --detect-changes`で前回からの変更を検知し、変更内容を記録・通知できる。

### Independent Test Criteria
- ✅ `llm-discovery update --detect-changes` で変更が検出され、changes.jsonとCHANGELOG.mdに記録される
- ✅ 初回実行時にベースライン作成メッセージが表示される
- ✅ 30日以上前のスナップショットが自動削除される

### Acceptance Scenarios (from spec.md)
1. 前回スナップショット存在時に変更検知、変更タイプ別カウント+モデルID/名前表示、changes.json/CHANGELOG.md記録
2. 変更検知完了後にCHANGELOG.mdに日付付きで変更内容追記
3. 初回実行時にベースライン作成メッセージ表示、現在データ保存
4. 30日以上前のスナップショット自動削除

### Tests (Test-First - Article III)

- [ ] T026 [P] [US3] テスト作成: `--detect-changes`基本動作（tests/test_cli.py内TestCLIUpdate.test_update_detect_changes）- 変更検知、FR-026準拠の出力形式、changes.json/CHANGELOG.md生成を検証
- [ ] T027 [P] [US3] テスト作成: 初回実行時のベースライン作成（tests/test_cli.py内TestCLIUpdate.test_update_detect_changes_first_run）- ベースライン作成メッセージ、スナップショット保存を検証
- [ ] T028 [P] [US3] テスト作成: 変更なし時の動作（tests/test_cli.py内TestCLIUpdate.test_update_detect_changes_no_changes）- 「No changes detected」メッセージ表示を検証
- [ ] T029 [P] [US3] テスト作成: スナップショット自動削除（tests/test_cli.py内TestCLIUpdate.test_update_cleanup_old_snapshots）- FR-008準拠、30日以上前のスナップショット削除を検証

#### Test Review & Approval (Article III - TDD)

- [ ] T030 [US3] **STOP HERE**: すべてのテストケース（T026-T029）をユーザーに提示し、承認を得る。承認なしで実装を進めてはならない（Article III準拠）

### Implementation

- [ ] T031 [US3] `--detect-changes`オプション実装（llm_discovery/cli/commands/update.py変更）- 既存`list`コマンド（行105-186）から変更検知ロジックを移動、FR-026準拠の出力形式実装、Article XII準拠
- [ ] T032 [US3] 品質チェック実行（ruff check .、mypy .、pytest実行）- Article VIII (C006-1)準拠、すべてのツールが合格必須
- [ ] T033 [US3] カバレッジ確認（pytest --cov=llm_discovery --cov-fail-under=90実行）- 90%以上のカバレッジ維持
- [ ] T034 [US3] 統合テスト実行（tests/test_cli.py内全テストケース実行）- すべてのテストが合格することを確認

### Completion Criteria
- [ ] すべてのテストが合格（T026-T029）
- [ ] `update --detect-changes`がFR-026に準拠して変更を表示
- [ ] スナップショット自動削除がFR-008に準拠して動作
- [ ] ruff、mypy、pytestがすべて合格
- [ ] テストカバレッジが90%以上

---

## Phase 5: Polish & Cross-Cutting Concerns

### Goal
ドキュメント更新、最終品質確認、コミット準備。

### Tasks

- [ ] T035 [P] CHANGELOG.md更新（CHANGELOG.md変更）- 破壊的変更（`list`コマンドの動作変更）、新機能（`update`コマンド追加）を記載
- [ ] T036 [P] README.md更新（README.md変更）- クイックスタートガイドを新ワークフロー（`update` → `list`）に更新
- [ ] T037 最終品質チェック実行（ruff check .、mypy .、pytest --cov=llm_discovery --cov-fail-under=90を順次実行）- すべてのツールが合格必須、Article VIII (C006-2)準拠のコミット前チェック
- [ ] T038 Constitution Check最終確認（.specify/memory/constitution.md全15条を再確認）- すべての原則に準拠していることを確認
- [ ] T039 **STOP HERE**: ユーザーに最終レビューを依頼し、コミット・PR作成の承認を得る。承認なしでコミットしてはならない（Article VIII (C006-3)準拠）

### Completion Criteria
- [ ] すべてのドキュメントが更新済み
- [ ] すべての品質チェックが合格
- [ ] ユーザーの最終承認を取得

---

## Dependencies & Parallel Execution

### User Story Completion Order

```
Phase 1 (Setup)
    ↓
Phase 2 (Foundational) - なし
    ↓
Phase 3 (US1 - MVP) ← これを最初に完了させる
    ↓
Phase 4 (US3) ← US1完了後に実装可能（US1に依存）
    ↓
Phase 5 (Polish)
```

### Parallel Execution Opportunities

#### Phase 1: Setup
すべてのタスク（T001-T004）は並列実行可能。

#### Phase 3: US1 - Tests
すべてのテスト作成タスク（T010-T018）は**並列実行可能**（[P]マーク付き）。異なるファイルに書き込むため、競合なし。

#### Phase 3: US1 - Implementation
- T020 (update.py作成) と T021 (main.py変更) は並列実行可能
- T022 (list.py変更) は T020完了後に実行（移動元のコード箇所を確認する必要があるため）
- T023-T025 (品質チェック) は実装完了後に順次実行

#### Phase 4: US3 - Tests
すべてのテスト作成タスク（T026-T029）は**並列実行可能**（[P]マーク付き）。

#### Phase 4: US3 - Implementation
- T031 (update.py変更) 単独実行
- T032-T034 (品質チェック) は実装完了後に順次実行

#### Phase 5: Polish
T035-T036 (ドキュメント更新) は**並列実行可能**（[P]マーク付き）。

---

## Implementation Strategy

### MVP First (User Story 1 Only)

**推奨**: まずUser Story 1（Phase 3）のみを完成させ、動作確認後にUser Story 3（Phase 4）に進む。

**MVP Scope**:
- Phase 1: Setup (T001-T004)
- Phase 3: US1 (T010-T025)
- Phase 5: Polish (T035-T039)

**MVP完了後の確認事項**:
1. `llm-discovery update` が正常動作
2. `llm-discovery list` が正常動作
3. キャッシュなし時のエラー処理が正常動作
4. すべての品質チェックが合格

### Incremental Delivery

MVP完了後、User Story 3を追加:
- Phase 4: US3 (T026-T034)
- Phase 5: Polish (再度T037-T039を実行)

---

## Task Count Summary

| Phase | Task Count | Parallel Tasks | User Story |
|-------|------------|----------------|------------|
| Phase 1: Setup | 4 | 4 | - |
| Phase 2: Foundational | 0 | 0 | - |
| Phase 3: US1 | 16 | 12 | US1 (MVP) |
| Phase 4: US3 | 9 | 6 | US3 |
| Phase 5: Polish | 5 | 2 | - |
| **Total** | **34** | **24** | **2 user stories** |

**Parallel Opportunities**: 24/34タスク（71%）が並列実行可能

**MVP Task Count**: 25タスク（Phase 1 + Phase 3 + Phase 5）

---

## Quality Gates (Article VIII - C006)

すべてのフェーズで以下の品質ゲートを通過必須:

1. **ruff check .** - コードスタイル・リント検査（エラーゼロ必須）
2. **mypy .** - 静的型チェック（エラーゼロ必須）
3. **pytest** - テスト実行（全テスト合格必須）
4. **pytest --cov=llm_discovery --cov-fail-under=90** - カバレッジ90%以上必須

**いずれかのツールが失敗した場合、コミット・PR作成を禁止**（Article VIII (C006-2, C006-3)準拠）

---

## TDD Workflow (Article III - C010)

**すべての実装タスクは以下のRed-Green-Refactorサイクルに従う**:

1. **Red**: テスト作成（T010-T018、T026-T029）→ テスト実行（失敗することを確認）
2. **Stop**: ユーザーにテストを提示し、承認を得る（T019、T030）
3. **Green**: 実装（T020-T022、T031）→ テスト実行（合格することを確認）
4. **Refactor**: コード改善（必要に応じて）→ テスト実行（合格を維持）

**承認なしで実装を進めてはならない**（Article III準拠）

---

## Next Steps

1. **Phase 1実行**: T001-T004を実行し、既存コード理解と環境準備
2. **Phase 3開始**: T010-T018でテストを作成（並列実行可能）
3. **Test Review**: T019でユーザー承認を取得
4. **Implementation**: T020-T025で実装と品質確認
5. **MVP確認**: User Story 1が完全に動作することを確認
6. **Phase 4移行**: User Story 3の実装（T026-T034）
7. **Final Polish**: Phase 5で最終確認とドキュメント更新

**最初のタスク**: T001（既存`list`コマンド実装の詳細分析）から開始してください。
