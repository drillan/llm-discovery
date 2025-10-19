# Tasks: Prebuilt Model Data Support

**Input**: Design documents from `/specs/004-prebuilt-data/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/prebuilt-data-loader.md
**Tests**: TDD approach - tests MUST be written and FAIL before implementation

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions
- Single project structure: `llm_discovery/`, `tests/` at repository root
- Paths shown below follow existing project structure from plan.md

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and repository data directory structure

- [X] T001 Create repository data directory: `data/prebuilt/` at repository root
- [X] T002 Add `.gitkeep` file to `data/prebuilt/` to ensure directory is tracked in git

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core models and exceptions that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 [P] Create PrebuiltDataMetadata pydantic model in `llm_discovery/models/prebuilt.py`
- [X] T004 [P] Create PrebuiltModelData pydantic model in `llm_discovery/models/prebuilt.py`
- [X] T005 [P] Create DataSourceType enum in `llm_discovery/models/prebuilt.py`
- [X] T006 [P] Create DataSourceInfo pydantic model in `llm_discovery/models/prebuilt.py`
- [X] T007 [P] Add PrebuiltDataNotFoundError to `llm_discovery/exceptions.py`
- [X] T008 [P] Add PrebuiltDataCorruptedError to `llm_discovery/exceptions.py`
- [X] T009 [P] Add PrebuiltDataValidationError to `llm_discovery/exceptions.py`
- [X] T010 Add has_any_api_keys() method to Config class in `llm_discovery/models/config.py`
- [X] T011 Export new models and exceptions in `llm_discovery/models/__init__.py`
- [X] T012 [P] Verify HTTP library availability (use urllib.request from stdlib, no new dependencies)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Zero-Configuration Quick Start (Priority: P1) 🎯 MVP

**Goal**: 新規ユーザーがAPIキー不要で即座にモデルリストを確認できる

**Independent Test**: APIキーを設定せずに `llm-discovery list` を実行し、事前生成データが表示されることを確認

### Tests for User Story 1 (TDD - Write FIRST, ensure FAIL)

- [X] T013 [P] [US1] Contract test: PrebuiltDataLoader.is_available() in `tests/contract/test_prebuilt_loader_contract.py`
- [X] T014 [P] [US1] Contract test: PrebuiltDataLoader.load_models() in `tests/contract/test_prebuilt_loader_contract.py`
- [X] T015 [P] [US1] Contract test: PrebuiltDataLoader.get_metadata() in `tests/contract/test_prebuilt_loader_contract.py`
- [X] T016 [P] [US1] Contract test: PrebuiltDataLoader.get_age_hours() in `tests/contract/test_prebuilt_loader_contract.py`
- [X] T017 [P] [US1] Unit test: PrebuiltDataLoader URL not accessible handling in `tests/unit/services/test_prebuilt_loader.py`
- [X] T018 [P] [US1] Unit test: PrebuiltDataLoader corrupted JSON handling in `tests/unit/services/test_prebuilt_loader.py`
- [X] T019 [P] [US1] Unit test: PrebuiltDataLoader validation error handling in `tests/unit/services/test_prebuilt_loader.py`

### Implementation for User Story 1

- [X] T020 [US1] Implement PrebuiltDataLoader.__init__() with remote URL in `llm_discovery/services/prebuilt_loader.py`
- [X] T021 [US1] Implement PrebuiltDataLoader.is_available() with HEAD request in `llm_discovery/services/prebuilt_loader.py`
- [X] T022 [US1] Implement PrebuiltDataLoader.load_models() with HTTP GET in `llm_discovery/services/prebuilt_loader.py`
- [X] T023 [US1] Implement PrebuiltDataLoader.get_metadata() with HTTP GET in `llm_discovery/services/prebuilt_loader.py`
- [X] T024 [US1] Implement PrebuiltDataLoader.get_age_hours() in `llm_discovery/services/prebuilt_loader.py`
- [X] T025 [US1] Implement PrebuiltDataLoader.get_data_source_info() in `llm_discovery/services/prebuilt_loader.py`
- [X] T026 [US1] Export PrebuiltDataLoader in `llm_discovery/services/__init__.py`
- [X] T027 [US1] Run contract and unit tests, verify they PASS
- [X] T028 [US1] Run ruff, mypy, pytest on PrebuiltDataLoader module

**Checkpoint**: PrebuiltDataLoader is fully functional and tested independently

---

## Phase 4: User Story 2 - Seamless API Key Integration (Priority: P2)

**Goal**: APIキー設定で自動的にリアルタイムデータ取得モードに切り替わる

**Independent Test**: APIキー設定/未設定で `llm-discovery list` を実行し、データソースが自動切替されることを確認

### Tests for User Story 2 (TDD - Write FIRST, ensure FAIL)

- [X] T029 [P] [US2] Integration test: No API keys → prebuilt data in `tests/integration/test_data_source_switching.py`
- [X] T030 [P] [US2] Integration test: API keys set → API data in `tests/integration/test_data_source_switching.py`
- [X] T031 [P] [US2] Integration test: Invalid API key → prebuilt data with error message in `tests/integration/test_data_source_switching.py`
- [X] T032 [P] [US2] Unit test: DiscoveryService.has_api_keys() in `tests/unit/services/test_discovery.py`
- [X] T033 [P] [US2] Unit test: DiscoveryService.fetch_or_load_models() no keys in `tests/unit/services/test_discovery.py`
- [X] T034 [P] [US2] Unit test: DiscoveryService.fetch_or_load_models() with keys in `tests/unit/services/test_discovery.py`

### Implementation for User Story 2

- [X] T035 [US2] Add has_api_keys() method to DiscoveryService in `llm_discovery/services/discovery.py`
- [X] T036 [US2] Add fetch_or_load_models() method to DiscoveryService in `llm_discovery/services/discovery.py`
- [X] T037 [US2] Initialize PrebuiltDataLoader in DiscoveryService.__init__() in `llm_discovery/services/discovery.py`
- [X] T038 [US2] Run integration and unit tests, verify they PASS
- [X] T039 [US2] Run ruff, mypy, pytest on DiscoveryService module

**Checkpoint**: API key detection and automatic data source switching works

---

## Phase 5: User Story 4 - Data Source Transparency (Priority: P2)

**Goal**: ユーザーはデータソース（API/事前生成）とタイムスタンプを明確に識別できる

**Independent Test**: `llm-discovery list` でデータソース情報が表示されることを確認

### Tests for User Story 4 (TDD - Write FIRST, ensure FAIL)

- [ ] T040 [P] [US4] Integration test: CLI displays prebuilt data source info in `tests/integration/test_cli_data_source_display.py`
- [ ] T041 [P] [US4] Integration test: CLI displays API data source info in `tests/integration/test_cli_data_source_display.py`
- [ ] T042 [P] [US4] Integration test: CLI warns about old data (>24h) in `tests/integration/test_cli_data_source_display.py`
- [ ] T043 [P] [US4] Integration test: Export includes metadata in `tests/integration/test_export_metadata.py`

### Implementation for User Story 4

- [ ] T044 [P] [US4] Extend list command to display data source info in `llm_discovery/cli/commands/list.py`
- [ ] T045 [P] [US4] Add data age warning logic to list command in `llm_discovery/cli/commands/list.py`
- [ ] T046 [P] [US4] Extend JSON exporter to include metadata in `llm_discovery/services/exporters/json_exporter.py`
- [ ] T047 [P] [US4] Extend CSV exporter to include data_source column in `llm_discovery/services/exporters/csv_exporter.py`
- [ ] T048 [P] [US4] Extend Markdown exporter to include source header in `llm_discovery/services/exporters/markdown_exporter.py`
- [ ] T049 [US4] Run integration tests, verify they PASS
- [ ] T050 [US4] Run ruff, mypy, pytest on CLI and exporter modules

**Checkpoint**: Data source transparency is fully implemented and tested

---

## Phase 6: User Story 3 - Automated Data Freshness (Priority: P3)

**Goal**: 事前生成データが1日1回自動更新される

**Independent Test**: GitHub Actions workflow が実行され、データファイルが更新されることを確認

### Tests for User Story 3 (TDD - Write FIRST, ensure FAIL)

- [X] T051 [P] [US3] Integration test: Metadata script adds correct metadata in `tests/integration/test_metadata_script.py`
- [X] T052 [P] [US3] Unit test: Metadata script validates input JSON in `tests/unit/scripts/test_add_metadata.py`
- [X] T053 [P] [US3] Unit test: Metadata script handles errors gracefully in `tests/unit/scripts/test_add_metadata.py`

### Implementation for User Story 3

- [X] T054 [P] [US3] Create metadata addition script in `scripts/add_metadata.py`
- [X] T055 [P] [US3] Implement input JSON loading in `scripts/add_metadata.py`
- [X] T056 [P] [US3] Implement metadata generation logic in `scripts/add_metadata.py`
- [X] T057 [P] [US3] Implement output JSON writing in `scripts/add_metadata.py`
- [X] T058 [P] [US3] Add error handling and validation in `scripts/add_metadata.py`
- [X] T059 [US3] Create GitHub Actions workflow in `.github/workflows/update-prebuilt-data.yml`
- [X] T060 [US3] Configure schedule trigger (cron: '0 0 * * *') in workflow
- [X] T061 [US3] Add workflow_dispatch trigger for manual execution in workflow
- [X] T062 [US3] Add steps: checkout, setup-uv, fetch models, generate JSON to `data/prebuilt/models.json` in workflow
- [X] T063 [US3] Add metadata script execution step in workflow
- [X] T064 [US3] Add git commit and push step in workflow
- [X] T065 [US3] Add failure notification (create issue) step in workflow
- [X] T066 [US3] Run metadata script tests, verify they PASS
- [X] T067 [US3] Run ruff, mypy, pytest on metadata script
- [ ] T068 [US3] Test workflow manually via workflow_dispatch

**Checkpoint**: Automated data freshness is fully implemented and operational

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Quality checks, documentation, and final integration

- [ ] T069 [P] Update README.md with prebuilt data feature documentation
- [ ] T070 [P] Update quickstart.md in project docs with usage examples
- [ ] T071 [P] Add edge case handling: URL not accessible, network timeout, very old data (>7 days)
- [ ] T072 Run full test suite: `uv run pytest --cov=llm_discovery`
- [ ] T073 Verify test coverage >90% per pyproject.toml settings
- [ ] T074 Run ruff check on entire codebase: `ruff check .`
- [ ] T075 Run mypy on entire codebase: `mypy llm_discovery/`
- [ ] T076 Manual end-to-end test: no API keys, verify prebuilt data works
- [ ] T077 Manual end-to-end test: set API keys, verify auto-switching works
- [ ] T078 Manual end-to-end test: export to JSON/CSV, verify metadata present
- [ ] T079 Update CLAUDE.md if new patterns/technologies introduced
- [ ] T080 Final code review and quality gate check

**Checkpoint**: Feature is production-ready and fully tested

---

## Dependencies & Execution Order

### Story Completion Order

```
Foundation (Phase 2)
    ↓
US1 (Phase 3) ← MVP - Can ship after this
    ↓
US2 (Phase 4) + US4 (Phase 5) ← Can implement in parallel
    ↓
US3 (Phase 6)
    ↓
Polish (Phase 7)
```

### Parallel Opportunities by Phase

**Phase 2 (Foundation)**: T003-T011 can run in parallel (marked [P]), T012 is independent

**Phase 3 (US1 Tests)**: T013-T019 can run in parallel (marked [P])

**Phase 4 (US2 Tests)**: T029-T034 can run in parallel (marked [P])

**Phase 5 (US4 Tests)**: T040-T043 can run in parallel (marked [P])
**Phase 5 (US4 Impl)**: T044-T048 can run in parallel (marked [P])

**Phase 6 (US3 Tests)**: T051-T053 can run in parallel (marked [P])
**Phase 6 (US3 Impl)**: T054-T058 can run in parallel (marked [P])

**Phase 7 (Polish)**: T069-T071 can run in parallel (marked [P])

---

## Implementation Strategy

### MVP Scope (Minimum Viable Product)

**Ship after Phase 3 (US1) complete**:
- Users can list models without API keys
- Prebuilt data loaded from remote URL (GitHub)
- HTTP request handling with timeout and error handling

**Benefit**: Immediate value delivery, early user feedback

### Incremental Delivery

1. **MVP**: Phase 1-3 (US1) - 28 tasks
2. **Enhancement 1**: Phase 4-5 (US2, US4) - 22 tasks
3. **Enhancement 2**: Phase 6 (US3) - 18 tasks
4. **Polish**: Phase 7 - 12 tasks

**Total Tasks**: 80 tasks (including tests, quality checks, documentation)

### Independent Testing Criteria

**US1**: PrebuiltDataLoader単体で、リモートデータ取得・バリデーション・モデル取得が動作
**US2**: DiscoveryService単体で、APIキー有無による自動切替が動作
**US4**: CLI単体で、データソース表示・警告メッセージが動作
**US3**: GitHub Actions単体で、データ自動更新が動作

各ストーリーは他のストーリーに依存せず、独立してテスト・デプロイ可能。

---

## Task Execution Checklist

Before marking a task as complete:
- [ ] Code written and follows project style (ruff clean)
- [ ] Type hints added and mypy passes
- [ ] Tests written (if TDD task) and PASS
- [ ] Documentation updated (docstrings, comments)
- [ ] Committed to git with meaningful message

---

## Notes

- **TDD Mandatory**: Article III of constitution - tests MUST be written before implementation
- **Quality Gates**: ruff, mypy, pytest MUST pass before marking task complete
- **Parallel Execution**: Tasks marked [P] can be executed concurrently
- **Independent Stories**: Each user story phase can be deployed as an MVP increment
- **File Paths**: All paths are relative to repository root
