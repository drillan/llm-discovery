# Tasks: LLMモデル発見・追跡システム

**Input**: Design documents from `/specs/001-llm-model-discovery/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Article III (Test-First Imperative) により、すべてのタスクは実装前にテストを作成します。

**Organization**: タスクはUser Storyごとにグループ化され、各ストーリーを独立して実装・テスト可能にします。

## Format: `[ID] [P?] [Story] Description`
- **[P]**: 並列実行可能（異なるファイル、依存関係なし）
- **[Story]**: タスクが属するUser Story（例: US1、US2、US3、US4）
- 説明には正確なファイルパスを含む

## Path Conventions
- Single project構成（plan.md Section "Project Structure"に準拠）
- メインパッケージ: `llm_discovery/`（アンダースコア使用）
- テスト: `tests/`（unit、integration、contract）
- 設定: `pyproject.toml`（uv対応）

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: プロジェクト初期化と基本構造

- [ ] T001 Create project structure per plan.md (llm_discovery/, tests/, pyproject.toml, README.md, LICENSE, .gitignore)
- [ ] T002 Initialize Python project with uv and configure pyproject.toml (Python 3.13+, dependencies: typer, httpx, pydantic v2, toml, pyyaml, openai, google-generativeai, google-cloud-aiplatform, pytest, pytest-asyncio, pytest-cov)
- [ ] T003 [P] Configure linting and formatting tools (ruff for linting/formatting, mypy for type checking in pyproject.toml)
- [ ] T004 [P] Create .gitignore file with Python-specific exclusions and cache directories (~/.llm-discovery/)
- [ ] T005 [P] Create LICENSE file (choose license per project requirements)
- [ ] T006 [P] Create initial README.md with project overview and installation instructions

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: 全User Storyの実装前に完了必須のコアインフラストラクチャ

**⚠️ CRITICAL**: このフェーズが完了するまで、User Storyの作業は開始できません

### Tests for Foundational (Test-First)

- [ ] T007 [P] Create tests/conftest.py with pytest fixtures for test configuration
- [ ] T008 [P] Create tests/unit/test_models.py with initial test structure (empty placeholder tests for Model, Provider, Snapshot, Change, Cache)
- [ ] T009 [P] Create tests/unit/test_config.py with tests for environment variable loading (Primary Data Non-Assumption Principle validation)
- [ ] T010 [P] Create tests/unit/test_error_handler.py with tests for fail-fast error handling (FR-017, FR-018 validation)

### Foundational Implementation

- [ ] T011 [P] Create llm_discovery/__init__.py with public API exports (DiscoveryClient, Exporter, models) and __version__ attribute using importlib.metadata.version("llm-discovery")
- [ ] T012 [P] Create llm_discovery/config/constants.py with application constants (DEFAULT_CACHE_DIR, RETENTION_DAYS, CACHE_VERSION) - NOTE: Do NOT hardcode package version here, use importlib.metadata instead
- [ ] T013 Create llm_discovery/config/settings.py with Pydantic v2 Settings class for environment variable management (OPENAI_API_KEY, GOOGLE_API_KEY, GOOGLE_GENAI_USE_VERTEXAI, GOOGLE_APPLICATION_CREDENTIALS, LLM_DISCOVERY_CACHE_DIR, LLM_DISCOVERY_RETENTION_DAYS)
- [ ] T014 [P] Create llm_discovery/utils/error_handler.py with custom exceptions (LLMDiscoveryError, ProviderFetchError, AuthenticationError, ConfigurationError, FileIOError, SnapshotNotFoundError, CacheCorruptedError)
- [ ] T015 [P] Create llm_discovery/utils/file_io.py with TOML file I/O utilities (read_toml, write_toml, ensure_cache_dir)
- [ ] T016 Create llm_discovery/models/model.py with Model entity (Pydantic v2: id, name, provider, fetch_method, timestamp, metadata, @field_validator for non-empty strings and UTC timezone)
- [ ] T017 [P] Create llm_discovery/models/provider.py with Provider entity and ProviderName/FetchMethod enums (Pydantic v2: name, api_endpoint, fetch_method, backend, models_count, @field_validator for Google backend validation)
- [ ] T018 [P] Create llm_discovery/models/snapshot.py with Snapshot and SnapshotMetadata entities (Pydantic v2: id, timestamp, models, metadata, @field_validator for non-empty models and UTC timezone)
- [ ] T019 [P] Create llm_discovery/models/change.py with Change entity and ChangeType enum (Pydantic v2: change_type, model, detected_at, previous_snapshot_id, current_snapshot_id, @field_validator for UTC timezone)
- [ ] T020 Update tests/unit/test_models.py with comprehensive tests for all models (validation rules, timezone checks, enum constraints, cross-entity validation)
- [ ] T021 Update tests/unit/test_config.py with tests for Settings class (environment variable validation, Primary Data Non-Assumption Principle enforcement)
- [ ] T022 Update tests/unit/test_error_handler.py with tests for all custom exceptions (error message clarity, exception hierarchy)
- [ ] T023 Run tests and verify all foundational tests pass (pytest tests/unit/ with coverage)

**Checkpoint**: Foundation ready - User Story実装を並列で開始可能

---

## Phase 3: User Story 1 - リアルタイムモデル一覧取得 (Priority: P1) 🎯 MVP

**Goal**: 複数のLLMプロバイダーから利用可能なモデル一覧を取得し、現在のモデルラインナップを把握する

**Independent Test**: `uvx llm-discovery list` を実行して、全プロバイダーのモデル一覧が表示されることで検証可能。オフラインキャッシュの存在確認も独立してテストできる。

### Tests for User Story 1 (Test-First)

- [ ] T024 [P] [US1] Create tests/contract/test_cli_interface.py with contract tests for `list` command (exit code 0 on success, exit code 1 on API failure, exit code 2 on auth error)
- [ ] T025 [P] [US1] Create tests/integration/test_provider_apis.py with tests for OpenAI provider (real API calls, authentication validation, fetch_models returns list of Model objects)
- [ ] T026 [P] [US1] Create tests/integration/test_cache_io.py with tests for cache operations (TOML write/read, cache directory creation, offline mode)
- [ ] T027 [P] [US1] Create tests/unit/test_providers.py with tests for BaseProvider abstract class and provider implementations

### Implementation for User Story 1

- [ ] T028 [P] [US1] Create llm_discovery/providers/base.py with BaseProvider abstract class (async fetch_models method, name property, ProviderProtocol)
- [ ] T029 [P] [US1] Create llm_discovery/providers/openai.py with OpenAIProvider implementation (async fetch_models using openai SDK, error handling per FR-017)
- [ ] T030 [P] [US1] Create llm_discovery/providers/google.py with GoogleProvider implementation (backend selection via GOOGLE_GENAI_USE_VERTEXAI, google-generativeai for AI Studio, google-cloud-aiplatform for Vertex AI, FR-021 validation)
- [ ] T031 [P] [US1] Create llm_discovery/providers/anthropic.py with AnthropicProvider implementation (manual data loading from embedded JSON/TOML file)
- [ ] T032 [US1] Update tests/unit/test_providers.py with tests for all provider implementations (OpenAI, Google AI Studio, Vertex AI, Anthropic, authentication errors, API failures)
- [ ] T033 [US1] Create llm_discovery/services/cache.py with CacheService class (load_cache, save_cache, get_latest_models methods using TOML format, FR-003 compliance)
- [ ] T034 [US1] Create tests/unit/test_services.py with tests for CacheService (TOML read/write, cache corruption handling per FR-019)
- [ ] T035 [US1] Create llm_discovery/services/discovery.py with DiscoveryService class (async fetch_all_models using asyncio.gather for parallel provider fetching per FR-016, fail-fast error handling per FR-017/FR-018)
- [ ] T036 [US1] Update tests/unit/test_services.py with tests for DiscoveryService (parallel fetching, fail-fast on partial failure, SC-007 performance validation)
- [ ] T037 [US1] Create llm_discovery/cli/formatters/json.py with JSONFormatter class (export method for CI/CD-optimized JSON structure)
- [ ] T038 [US1] Create tests/unit/test_formatters.py with tests for JSONFormatter (output structure validation, datetime serialization)
- [ ] T039 [US1] Create llm_discovery/cli/app.py with typer application setup (Rich integration, error handling, --version flag using importlib.metadata.version("llm-discovery"))
- [ ] T040 [US1] Create llm_discovery/cli/commands/list.py with `list` command implementation (--format, --output, --detect-changes, --provider options, FR-013 compliance)
- [ ] T041 [US1] Create llm_discovery/__main__.py with uvx entry point (if __name__ == "__main__": call CLI app)
- [ ] T042 [US1] Update tests/contract/test_cli_interface.py with comprehensive CLI contract tests (all options including --version output format validation, error scenarios per Edge Cases, exit codes validation)
- [ ] T043 [US1] Update tests/integration/test_provider_apis.py with tests for Google Vertex AI provider (GCP credentials validation, FR-021 edge cases)
- [ ] T044 [US1] Run User Story 1 tests and verify all pass (pytest tests/ -k US1 with coverage ≥90%)
- [ ] T045 [US1] Manual integration test: Execute `uv run python -m llm_discovery list` with real API keys and verify output

**Checkpoint**: User Story 1は完全に機能し、独立してテスト可能

---

## Phase 4: User Story 2 - マルチフォーマットエクスポート (Priority: P2)

**Goal**: モデル一覧を分析用にCSV形式で、CI/CD統合用にJSON形式で、ドキュメント用にMarkdown形式で、設定ファイル用にTOML/YAML形式でエクスポートする

**Independent Test**: 各形式へのエクスポートコマンド（例: `uvx llm-discovery export --format csv`）を実行し、正しいフォーマットでファイルが生成されることで検証可能

### Tests for User Story 2 (Test-First)

- [ ] T046 [P] [US2] Create tests/contract/test_export_formats.py with contract tests for export command (all formats: json, csv, yaml, markdown, toml, file I/O validation)
- [ ] T047 [P] [US2] Update tests/unit/test_formatters.py with tests for CSV, YAML, Markdown, TOML formatters (structure validation, encoding checks)

### Implementation for User Story 2

- [ ] T048 [P] [US2] Create llm_discovery/cli/formatters/csv.py with CSVFormatter class (include_metadata option per contracts/cli-interface.md)
- [ ] T049 [P] [US2] Create llm_discovery/cli/formatters/yaml.py with YAMLFormatter class (settings file optimized structure)
- [ ] T050 [P] [US2] Create llm_discovery/cli/formatters/markdown.py with MarkdownFormatter class (human-readable documentation format with tables)
- [ ] T051 [P] [US2] Create llm_discovery/cli/formatters/toml.py with TOMLFormatter class (interoperability-focused structure per FR-005)
- [ ] T052 [US2] Update tests/unit/test_formatters.py with comprehensive formatter tests (all 5 formats, edge cases, special character handling)
- [ ] T053 [US2] Create llm_discovery/cli/formatters/__init__.py with Exporter class (export_to_json, export_to_csv, export_to_yaml, export_to_markdown, export_to_toml methods per contracts/python-api.md)
- [ ] T054 [US2] Create llm_discovery/cli/commands/export.py with `export` command implementation (--format required, --output required, --provider optional per contracts/cli-interface.md)
- [ ] T055 [US2] Update tests/contract/test_export_formats.py with comprehensive export tests (all 5 acceptance scenarios from spec.md)
- [ ] T056 [US2] Run User Story 2 tests and verify all pass (pytest tests/ -k US2 with coverage ≥90%)
- [ ] T057 [US2] Manual integration test: Execute `uv run python -m llm_discovery export --format csv --output models.csv` and verify CSV structure

**Checkpoint**: User Stories 1とUser Story 2の両方が独立して動作

---

## Phase 5: User Story 3 - 新モデル検知と差分レポート (Priority: P3)

**Goal**: 定期的にモデル一覧を取得し、前回からの変更（新規追加・削除されたモデル）を検知して、変更内容を記録・通知する

**Independent Test**: モデル一覧を2回取得し、2回目の取得時に `--detect-changes` フラグを使用して、changes.jsonとCHANGELOG.mdが生成されることで検証可能

### Tests for User Story 3 (Test-First)

- [ ] T058 [P] [US3] Create tests/integration/test_change_detection.py with tests for change detection logic (added models, removed models, baseline creation)
- [ ] T059 [P] [US3] Create tests/unit/test_snapshot.py with tests for snapshot management (save, load, retention policy per FR-008)
- [ ] T060 [P] [US3] Update tests/contract/test_cli_interface.py with tests for --detect-changes flag (changes.json structure, CHANGELOG.md generation)

### Implementation for User Story 3

- [ ] T061 [US3] Create llm_discovery/services/snapshot.py with SnapshotService class (create_snapshot, save_snapshot, load_latest_snapshot, cleanup_old_snapshots methods, 30-day retention per FR-008)
- [ ] T062 [US3] Update tests/unit/test_snapshot.py with tests for SnapshotService (snapshot persistence, UUID generation, retention cleanup)
- [ ] T063 [US3] Create llm_discovery/services/change_detection.py with ChangeDetectionService class (detect_changes method comparing snapshots, generate changes.json per FR-010, generate CHANGELOG.md per FR-009)
- [ ] T064 [US3] Update tests/integration/test_change_detection.py with comprehensive change detection tests (all 4 acceptance scenarios from spec.md)
- [ ] T065 [US3] Update llm_discovery/cli/commands/list.py to integrate --detect-changes flag (call ChangeDetectionService, output changes.json and CHANGELOG.md)
- [ ] T066 [US3] Run User Story 3 tests and verify all pass (pytest tests/ -k US3 with coverage ≥90%)
- [ ] T067 [US3] Manual integration test: Execute `uv run python -m llm_discovery list --detect-changes` twice and verify changes.json and CHANGELOG.md generation

**Checkpoint**: すべてのUser Stories（US1、US2、US3）が独立して機能

---

## Phase 6: User Story 4 - CI/CD統合とPython API利用 (Priority: P4)

**Goal**: GitHub ActionsのワークフローにLLMモデル監視を組み込み、新モデルが検出された際にSlackへ通知を送信する。データサイエンティストは、Pythonスクリプト内でモデル一覧を取得し、独自の分析パイプラインを構築する

**Independent Test**: GitHub ActionsのYAMLファイルを作成し、ワークフローが正常に実行されて通知が送信されることで検証可能。Python APIについては、スクリプト内でインポートして使用できることで検証可能

### Tests for User Story 4 (Test-First)

- [ ] T068 [P] [US4] Create tests/contract/test_python_api.py with contract tests for Python API (DiscoveryClient.fetch_models, DiscoveryClient.detect_changes, Exporter methods per contracts/python-api.md)
- [ ] T069 [P] [US4] Create tests/integration/test_ci_cd_integration.py with tests for CI/CD integration workflow (changes.json parsing, notification payload generation)

### Implementation for User Story 4

- [ ] T070 [US4] Create llm_discovery/client.py with DiscoveryClient class (async fetch_models, async detect_changes methods, optional providers/cache_dir/retention_days parameters per contracts/python-api.md)
- [ ] T071 [US4] Update llm_discovery/__init__.py to export DiscoveryClient and Exporter for public API (from llm_discovery import DiscoveryClient, Exporter)
- [ ] T072 [US4] Update tests/contract/test_python_api.py with comprehensive Python API tests (all example usage scenarios from contracts/python-api.md, type hints validation, __version__ attribute accessibility and format validation)
- [ ] T073 [P] [US4] Create docs/ci-cd-integration.md with GitHub Actions example workflow (cron schedule, Slack notification, 10-line YAML example per SC-004)
- [ ] T074 [P] [US4] Create docs/python-api-examples.md with Python API usage examples (basic model fetching, change detection, custom provider selection, CI/CD pipeline integration per contracts/python-api.md)
- [ ] T075 [US4] Update README.md with CI/CD integration and Python API usage sections (link to docs/)
- [ ] T076 [US4] Run User Story 4 tests and verify all pass (pytest tests/ -k US4 with coverage ≥90%)
- [ ] T077 [US4] Manual integration test: Create example Python script using DiscoveryClient and execute to verify API functionality

**Checkpoint**: すべてのUser Stories（US1、US2、US3、US4）が完全に機能し、独立してテスト可能

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: 複数のUser Storiesに影響を与える改善

- [ ] T078 [P] Update README.md with comprehensive documentation (installation via uvx and pip, basic usage, all commands, environment variables, quickstart examples)
- [ ] T079 [P] Create CONTRIBUTING.md with development guidelines (setting up dev environment with uv, running tests, code style with ruff/mypy, PR process)
- [ ] T080 [P] Validate quickstart.md examples by executing all commands manually (uvx llm-discovery list, export commands, --detect-changes, Python API examples)
- [ ] T081 Run full test suite and verify 90%+ coverage (pytest tests/ --cov=llm_discovery --cov-report=term-missing --cov-fail-under=90)
- [ ] T082 [P] Run mypy type checking and resolve all type errors (mypy llm_discovery/)
- [ ] T083 [P] Run ruff linting and formatting (ruff check llm_discovery/ && ruff format llm_discovery/)
- [ ] T084 Performance optimization: Validate parallel provider fetching achieves SC-007 (全体の取得時間 ≤ 最も遅いプロバイダーの応答時間)
- [ ] T085 Security hardening: Review error messages for sensitive data leakage (API keys, credentials should never appear in logs/errors)
- [ ] T086 [P] Create .github/workflows/ci.yml with GitHub Actions CI pipeline (pytest, mypy, ruff, coverage upload)
- [ ] T087 [P] Create pyproject.toml scripts for common tasks (uv run lint, uv run test, uv run format)
- [ ] T088 Final integration test: Execute all acceptance scenarios from spec.md and verify all pass

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: 依存なし - 即座に開始可能
- **Foundational (Phase 2)**: Setupフェーズ完了に依存 - すべてのUser Storiesをブロック
- **User Stories (Phase 3-6)**: すべてFoundationalフェーズ完了に依存
  - User Storiesは並列で進行可能（チームリソースがあれば）
  - または優先順位順に順次実行（P1 → P2 → P3 → P4）
- **Polish (Phase 7)**: 実装したいすべてのUser Storiesが完了していることに依存

### User Story Dependencies

- **User Story 1 (P1)**: Foundational完了後に開始可能 - 他のストーリーへの依存なし
- **User Story 2 (P2)**: Foundational完了後に開始可能 - US1と統合可能だが独立してテスト可能
- **User Story 3 (P3)**: Foundational完了後に開始可能 - US1/US2と統合するが独立してテスト可能
- **User Story 4 (P4)**: Foundational完了後に開始可能 - US1-US3の機能を使用するが独立してテスト可能

### Within Each User Story

- テスト（Test-First）は実装前に作成し、FAILすることを確認
- Models → Services → Endpoints/CLI Commands
- コア実装 → 統合
- ストーリー完了後、次の優先度へ

### Parallel Opportunities

- すべてのSetupタスク（[P]マーク）は並列実行可能
- Foundationalフェーズ内の[P]タスクは並列実行可能
- Foundationalフェーズ完了後、すべてのUser Storiesを並列で開始可能（チームキャパシティが許せば）
- User Story内のテスト（[P]マーク）は並列実行可能
- User Story内のモデル（[P]マーク）は並列実行可能
- 異なるUser Storiesは異なるチームメンバーによって並列作業可能

---

## Parallel Example: User Story 1

```bash
# User Story 1のテストをまとめて起動（Test-First）:
Task T024: "Create tests/contract/test_cli_interface.py with contract tests for list command"
Task T025: "Create tests/integration/test_provider_apis.py with tests for OpenAI provider"
Task T026: "Create tests/integration/test_cache_io.py with tests for cache operations"
Task T027: "Create tests/unit/test_providers.py with tests for BaseProvider"

# User Story 1のプロバイダー実装をまとめて起動:
Task T028: "Create llm_discovery/providers/base.py with BaseProvider abstract class"
Task T029: "Create llm_discovery/providers/openai.py with OpenAIProvider implementation"
Task T030: "Create llm_discovery/providers/google.py with GoogleProvider implementation"
Task T031: "Create llm_discovery/providers/anthropic.py with AnthropicProvider implementation"
```

---

## Parallel Example: User Story 2

```bash
# User Story 2のフォーマッター実装をまとめて起動:
Task T048: "Create llm_discovery/cli/formatters/csv.py with CSVFormatter class"
Task T049: "Create llm_discovery/cli/formatters/yaml.py with YAMLFormatter class"
Task T050: "Create llm_discovery/cli/formatters/markdown.py with MarkdownFormatter class"
Task T051: "Create llm_discovery/cli/formatters/toml.py with TOMLFormatter class"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - すべてのストーリーをブロック)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: User Story 1を独立してテスト
5. 準備ができたらデプロイ/デモ

### Incremental Delivery

1. Setup + Foundational完了 → 基盤準備完了
2. User Story 1追加 → 独立してテスト → デプロイ/デモ（MVP！）
3. User Story 2追加 → 独立してテスト → デプロイ/デモ
4. User Story 3追加 → 独立してテスト → デプロイ/デモ
5. User Story 4追加 → 独立してテスト → デプロイ/デモ
6. 各ストーリーが前のストーリーを壊さずに価値を追加

### Parallel Team Strategy

複数の開発者がいる場合:

1. チームでSetup + Foundationalを一緒に完了
2. Foundational完了後:
   - Developer A: User Story 1
   - Developer B: User Story 2
   - Developer C: User Story 3
   - Developer D: User Story 4
3. ストーリーは独立して完了し、統合

---

## Notes

- [P]タスク = 異なるファイル、依存関係なし
- [Story]ラベルはタスクを特定のUser Storyにマッピングしてトレーサビリティを確保
- 各User Storyは独立して完了・テスト可能であるべき
- 実装前にテストがFAILすることを検証（Test-First Imperative）
- 各タスクまたは論理的なグループ後にコミット
- 任意のチェックポイントで停止し、ストーリーを独立して検証
- 避けるべき事項: 曖昧なタスク、同じファイルでの競合、独立性を壊すストーリー間の依存関係
- Article III（Test-First Imperative）遵守: すべての実装前にテスト作成
- Article IV（Integration-First Testing）遵守: 実際のAPI呼び出しによる統合テスト優先
- FR-020遵守: テストカバレッジ90%以上維持
