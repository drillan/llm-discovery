---
description: "Task list for Documentation System implementation"
---

# Tasks: プロジェクトドキュメント体系

**Input**: Design documents from `/specs/002-docs/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: ドキュメントビルドテスト、リンク切れテストを含む

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions
- Documentation source: `docs/` at repository root
- Tests: `tests/` at repository root
- Contracts reference: `specs/001-llm-model-discovery/contracts/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Sphinx設定の更新とビルド環境の準備

- [x] T001 Update docs/conf.py with MyST extensions (colon_fence, deflist, tasklist)
- [x] T002 Update docs/conf.py with Read the Docs theme options (navigation_depth, collapse_navigation)
- [x] T003 Update docs/conf.py with dynamic version retrieval from importlib.metadata
- [x] T004 Update docs/Makefile to add linkcheck target for link validation

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: ドキュメントビルドテストの構築（全ユーザーストーリーの品質保証基盤）

**⚠️ CRITICAL**: No user story documentation work can begin until build tests are in place

- [x] T005 Create tests/test_docs.py with test_docs_build function (sphinx-build -W validation)
- [x] T006 [P] Create test_docs_no_warnings function in tests/test_docs.py (warning detection)
- [x] T007 [P] Create test_all_required_files_exist function in tests/test_docs.py (file existence validation)
- [ ] T008 Run pytest tests/test_docs.py to verify test infrastructure works

**Checkpoint**: Build test infrastructure ready - documentation writing can now begin in parallel

---

## Phase 3: User Story 1 - 基本的なドキュメント構造の整備 (Priority: P1) 🎯 MVP

**Goal**: 新規ユーザーがllm-discoveryの概要、インストール方法、基本的な使い方を理解できるドキュメントを提供

**Independent Test**: `make html` でビルド成功し、index.md、installation.md、quickstart.mdが正しく表示される

### Implementation for User Story 1

- [x] T009 [P] [US1] Update docs/index.md with project overview, features list, and toctree structure (Getting Started section)
- [x] T010 [P] [US1] Create docs/installation.md with uvx installation instructions
- [x] T011 [US1] Add pip installation instructions to docs/installation.md
- [x] T012 [US1] Add source installation instructions to docs/installation.md
- [x] T013 [US1] Integrate versioning information from specs/001-llm-model-discovery/contracts/versioning.md into docs/installation.md
- [x] T014 [P] [US1] Create docs/quickstart.md with environment variables setup section
- [x] T015 [US1] Add basic command examples (update, list, export) to docs/quickstart.md
- [x] T016 [US1] Add Python API basic usage example to docs/quickstart.md with complete executable code
- [x] T017 [US1] Add Admonitions to docs/quickstart.md (warning for API keys, tip for uvx usage)
- [x] T018 [US1] Run make html and verify all US1 pages build without errors
- [x] T019 [US1] Run make linkcheck and fix any broken links in US1 pages
- [x] T020 [US1] Manually verify docs/_build/html/index.html displays correctly in browser

**Checkpoint**: At this point, User Story 1 should be fully functional - users can understand project basics, install, and run first commands

---

## Phase 4: User Story 2 - APIリファレンスとCLIリファレンスの提供 (Priority: P2)

**Goal**: 開発者がPython APIとCLIコマンドの詳細仕様を確認できるリファレンスドキュメントを提供

**Independent Test**: docs/api-reference.md と docs/cli-reference.md が存在し、全クラス・コマンドの説明とサンプルコードが含まれる

### Implementation for User Story 2

- [ ] T021 [P] [US2] Create docs/api-reference.md with DiscoveryClient class documentation from specs/001-llm-model-discovery/contracts/python-api.md
- [ ] T022 [US2] Add Config class documentation to docs/api-reference.md
- [ ] T023 [US2] Add ProviderSnapshot class documentation to docs/api-reference.md
- [ ] T024 [US2] Add ModelInfo class documentation to docs/api-reference.md
- [ ] T025 [US2] Add async/await usage examples to docs/api-reference.md (multiple use cases)
- [ ] T026 [US2] Integrate data formats (JSON, CSV, YAML, Markdown, TOML) from specs/001-llm-model-discovery/contracts/data-formats.md into docs/api-reference.md
- [ ] T027 [US2] Add Admonitions to docs/api-reference.md (note for Pydantic v2, tip for async best practices)
- [ ] T028 [P] [US2] Create docs/cli-reference.md with update command documentation from specs/001-llm-model-discovery/contracts/cli-interface.md
- [ ] T029 [US2] Add list command documentation to docs/cli-reference.md
- [ ] T030 [US2] Add export command documentation to docs/cli-reference.md with all format examples
- [ ] T031 [US2] Add command output examples to docs/cli-reference.md (table format, JSON format)
- [ ] T032 [US2] Add Admonitions to docs/cli-reference.md (important for required env vars, warning for rate limits)
- [ ] T033 [US2] Update docs/index.md toctree to include Reference section (api-reference, cli-reference)
- [ ] T034 [US2] Run make html and verify all US2 pages build without errors
- [ ] T035 [US2] Run make linkcheck and fix any broken links in US2 pages
- [ ] T036 [US2] Verify contracts integrity: compare docs/api-reference.md with specs/001-llm-model-discovery/contracts/python-api.md for consistency
- [ ] T037 [US2] Verify contracts integrity: compare docs/cli-reference.md with specs/001-llm-model-discovery/contracts/cli-interface.md for consistency

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - developers can reference detailed API/CLI documentation

---

## Phase 5: User Story 3 - 高度な使用例とトラブルシューティングガイド (Priority: P3)

**Goal**: 上級ユーザーがCI/CD統合、エラー解決方法を確認できるガイドを提供

**Independent Test**: docs/advanced-usage.md と docs/troubleshooting.md が存在し、実行可能なコード例とエラー解決手順が含まれる

### Implementation for User Story 3

- [ ] T038 [P] [US3] Create docs/advanced-usage.md with GitHub Actions integration example (complete workflow file)
- [ ] T039 [US3] Add GitLab CI integration example to docs/advanced-usage.md
- [ ] T040 [US3] Add provider filtering implementation example to docs/advanced-usage.md (Python API with filter logic)
- [ ] T041 [US3] Add custom error handling implementation example to docs/advanced-usage.md
- [ ] T042 [US3] Add Vertex AI setup guide to docs/advanced-usage.md (GCP credentials, env vars)
- [ ] T043 [US3] Add Admonitions to docs/advanced-usage.md (tip for CI/CD best practices, caution for rate limits)
- [ ] T044 [P] [US3] Create docs/troubleshooting.md with authentication errors section from specs/001-llm-model-discovery/contracts/error-handling.md
- [ ] T045 [US3] Add network errors section to docs/troubleshooting.md (causes and solutions)
- [ ] T046 [US3] Add rate limit errors section to docs/troubleshooting.md (detection and mitigation)
- [ ] T047 [US3] Add cache-related issues section to docs/troubleshooting.md (cache location, clearing cache)
- [ ] T048 [US3] Add FAQ section to docs/troubleshooting.md (common questions and answers)
- [ ] T049 [US3] Add Admonitions to docs/troubleshooting.md (warning for API key security, important for error logs)
- [ ] T050 [US3] Update docs/index.md toctree to include Guides section (advanced-usage, troubleshooting)
- [ ] T051 [US3] Run make html and verify all US3 pages build without errors
- [ ] T052 [US3] Run make linkcheck and fix any broken links in US3 pages
- [ ] T053 [US3] Verify contracts integrity: compare docs/troubleshooting.md with specs/001-llm-model-discovery/contracts/error-handling.md for consistency

**Checkpoint**: All basic, reference, and advanced user stories should now be independently functional

---

## Phase 6: User Story 4 - コントリビューションガイドと開発者向けドキュメント (Priority: P4)

**Goal**: コントリビューターが開発環境をセットアップし、プロジェクトに貢献できるガイドを提供

**Independent Test**: docs/contributing.md が存在し、開発環境セットアップ手順が実行可能である

### Implementation for User Story 4

- [ ] T054 [US4] Create docs/contributing.md with development environment setup section (uv sync, dependencies)
- [ ] T055 [US4] Add coding standards section to docs/contributing.md (ruff, mypy configuration)
- [ ] T056 [US4] Add commit message conventions to docs/contributing.md
- [ ] T057 [US4] Add testing requirements to docs/contributing.md from specs/001-llm-model-discovery/contracts/testing-requirements.md
- [ ] T058 [US4] Add test execution instructions to docs/contributing.md (pytest, coverage)
- [ ] T059 [US4] Add pull request process to docs/contributing.md (branch naming, PR description template)
- [ ] T060 [US4] Add project architecture section to docs/contributing.md (directory structure, key components)
- [ ] T061 [US4] Add Admonitions to docs/contributing.md (important for test requirements, tip for pre-commit hooks)
- [ ] T062 [US4] Update docs/index.md toctree to include contributing in Guides section
- [ ] T063 [US4] Run make html and verify docs/contributing.md builds without errors
- [ ] T064 [US4] Run make linkcheck and fix any broken links in docs/contributing.md
- [ ] T065 [US4] Verify contracts integrity: compare docs/contributing.md testing section with specs/001-llm-model-discovery/contracts/testing-requirements.md for consistency

**Checkpoint**: All user stories (US1-US4) should now be independently functional and complete

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: ドキュメント全体の品質向上と最終検証

- [ ] T066 [P] Review all docs/ files for MyST syntax compliance (Admonitions format, code block syntax)
- [ ] T067 [P] Review all docs/ files for writing style compliance (objective language, no exaggerations, minimal bold)
- [ ] T068 [P] Verify all code samples are executable (copy-paste test for Python examples)
- [ ] T069 Run full build test: make clean && make html with zero warnings
- [ ] T070 Run full link check: make linkcheck with zero broken links
- [ ] T071 Run pytest tests/test_docs.py and verify all tests pass
- [ ] T072 Manual browser test: verify all pages display correctly in Chrome, Firefox, Safari
- [ ] T073 Manual mobile test: verify responsive design on mobile devices (iOS, Android)
- [ ] T074 Final contracts integrity check: verify all docs/ content matches specs/001-llm-model-discovery/contracts/ for 100% consistency
- [ ] T075 Update CHANGELOG.md with documentation improvements
- [ ] T076 Run quickstart.md validation: follow all steps in specs/002-docs/quickstart.md to ensure implementation matches design

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3 → P4)
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Independent of US1 (different doc files)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Independent of US1/US2 (different doc files)
- **User Story 4 (P4)**: Can start after Foundational (Phase 2) - Independent of US1/US2/US3 (different doc files)

### Within Each User Story

- Doc files within a story marked [P] can be created in parallel (different files)
- toctree updates must come after doc file creation
- Build validation must come after all doc files in that story are created
- Contracts integrity check must come after content is written

### Parallel Opportunities

- All Setup tasks (T001-T004) can run sequentially (same files)
- All Foundational test creation tasks (T005-T007) marked [P] can run in parallel (different test functions)
- Once Foundational phase completes, all user stories can start in parallel:
  - **US1** (T009-T020): Developer A
  - **US2** (T021-T037): Developer B
  - **US3** (T038-T053): Developer C
  - **US4** (T054-T065): Developer D
- Within each story:
  - US1: T009, T010, T014 can run in parallel (different files)
  - US2: T021, T028 can run in parallel (different files)
  - US3: T038, T044 can run in parallel (different files)
- Polish tasks (T066-T068) can run in parallel (independent reviews)

---

## Parallel Example: After Foundational Phase

```bash
# All user stories can start in parallel (different doc files):
Task: "Update docs/index.md with project overview (US1)"
Task: "Create docs/api-reference.md with DiscoveryClient class (US2)"
Task: "Create docs/advanced-usage.md with GitHub Actions example (US3)"
Task: "Create docs/contributing.md with dev environment setup (US4)"

# Within User Story 1, these can run in parallel:
Task: "Update docs/index.md with project overview (US1)"
Task: "Create docs/installation.md with uvx instructions (US1)"
Task: "Create docs/quickstart.md with env vars setup (US1)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T004)
2. Complete Phase 2: Foundational (T005-T008) - CRITICAL test infrastructure
3. Complete Phase 3: User Story 1 (T009-T020)
4. **STOP and VALIDATE**: Run `make html`, verify index.md, installation.md, quickstart.md display correctly
5. Deploy to Read the Docs or GitHub Pages for initial user testing

### Incremental Delivery

1. Complete Setup + Foundational → Build tests ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP - basic docs!)
3. Add User Story 2 → Test independently → Deploy/Demo (+ API/CLI reference)
4. Add User Story 3 → Test independently → Deploy/Demo (+ advanced guides)
5. Add User Story 4 → Test independently → Deploy/Demo (+ contributor docs)
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (T001-T008)
2. Once Foundational is done:
   - Developer A: User Story 1 (T009-T020) - Basic docs
   - Developer B: User Story 2 (T021-T037) - API/CLI reference
   - Developer C: User Story 3 (T038-T053) - Advanced guides
   - Developer D: User Story 4 (T054-T065) - Contributing guide
3. Stories complete and integrate independently (different doc files)
4. Final polish phase together (T066-T076)

---

## Notes

- [P] tasks = different files, no dependencies - can run in parallel
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Build tests (Phase 2) are CRITICAL - they validate all subsequent work
- Commit after each task or logical group of tasks
- Stop at any checkpoint to validate story independently
- All code samples must be executable (copy-paste ready)
- All Admonitions must follow MyST syntax (`:::` fenced directives)
- All docs must be objective, avoid exaggerations, minimize bold formatting
- Contracts integrity is mandatory - 100% consistency with specs/001-llm-model-discovery/contracts/

## Task Count Summary

- **Total tasks**: 76
- **Setup (Phase 1)**: 4 tasks
- **Foundational (Phase 2)**: 4 tasks
- **User Story 1 (Phase 3)**: 12 tasks
- **User Story 2 (Phase 4)**: 17 tasks
- **User Story 3 (Phase 5)**: 16 tasks
- **User Story 4 (Phase 6)**: 12 tasks
- **Polish (Phase 7)**: 11 tasks

## Parallel Opportunities Identified

- Setup: 0 parallel sets (sequential tasks on same files)
- Foundational: 2 parallel tasks (T006, T007)
- User Story 1: 2 parallel tasks (T009, T010, T014)
- User Story 2: 2 parallel tasks (T021, T028)
- User Story 3: 2 parallel tasks (T038, T044)
- Polish: 3 parallel tasks (T066, T067, T068)
- **Cross-story parallelism**: All 4 user stories can run in parallel after Foundational phase

## Suggested MVP Scope

**MVP = Phase 1 + Phase 2 + Phase 3 (User Story 1 only)**

This delivers:
- Sphinx configuration with MyST extensions
- Build test infrastructure
- Basic documentation: index.md, installation.md, quickstart.md
- Users can understand project, install, and run first commands
- **Total MVP tasks**: 20 tasks (T001-T020)
