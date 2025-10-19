# Checklist: Python Packaging & Version Management

**Purpose**: Pythonパッケージング・バージョン管理の要件品質を検証する

**Created**: 2025-10-19

**Focus Areas**: バージョン情報の動的取得、Primary Data Non-Assumption Principle準拠、パッケージメタデータ管理

**Target Audience**: 実装者・コードレビュアー

---

## Requirement Completeness

- [x] CHK001 - パッケージバージョン情報の取得方法が仕様で明示的に定義されているか？ [Gap]
- [x] CHK002 - `--version`フラグの実装要件にバージョン情報の取得元（ハードコード vs 動的取得）が明記されているか？ [Gap, Spec CLI contract §Global Options]
- [x] CHK003 - パッケージメタデータ（名前、バージョン、作者、ライセンス）の管理方法がpyproject.toml要件で定義されているか？ [Gap, Task T002]
- [x] CHK004 - importlib.metadataを使用したバージョン取得の要件が技術仕様に含まれているか？ [Gap]
- [x] CHK005 - バージョン情報の一元管理（Single Source of Truth）の要件が定義されているか？ [Gap]
- [x] CHK006 - `__version__`属性の公開API要件（llm_discovery.__version__）が定義されているか？ [Gap, Spec Python API]
- [x] CHK007 - pyproject.tomlのproject.version設定要件が明記されているか？ [Gap, Task T002]
- [x] CHK008 - バージョン番号のセマンティックバージョニング形式遵守の要件が定義されているか？ [Completeness, Spec Versioning §Python API/CLI]

## Requirement Clarity

- [x] CHK009 - 「バージョン情報を表示」の実装方法（例: typer.echo(__version__)）が具体的に指定されているか？ [Ambiguity, Spec CLI contract §--version flag]
- [x] CHK010 - importlib.metadata.version("llm-discovery")の使用が明示的に推奨されているか？ [Clarity, Gap]
- [x] CHK011 - パッケージ名の統一（PyPI名: llm-discovery vs Pythonモジュール名: llm_discovery）がバージョン取得要件で明確化されているか？ [Clarity, Plan §Package naming]
- [x] CHK012 - バージョン取得失敗時のフォールバック動作（エラーまたは"unknown"表示）が定義されているか？ [Clarity, Gap]
- [x] CHK013 - 開発環境でのバージョン取得（editable install時）の動作が明記されているか？ [Edge Case, Gap]

## Requirement Consistency

- [x] CHK014 - pyproject.tomlのproject.versionとCLI --versionの出力が同一ソースから取得される要件になっているか？ [Consistency, Gap]
- [x] CHK015 - Python API（llm_discovery.__version__）とCLI（--version）のバージョン情報が一致する要件が定義されているか？ [Consistency, Gap]
- [x] CHK016 - contracts/python-api.mdとcontracts/cli-interface.mdのバージョン管理ポリシーが一致しているか？ [Consistency, Spec Versioning §Python API §CLI]
- [ ] CHK017 - data-model.mdのCache.versionフィールド（キャッシュフォーマットバージョン）とパッケージバージョンの関係が明確に区別されているか？ [Consistency, Spec data-model.md §Cache]

## Primary Data Non-Assumption Principle Compliance

- [x] CHK018 - バージョン情報のハードコーディング禁止の要件が明示的に定義されているか？ [Gap, Constitution §Primary Data Non-Assumption]
- [x] CHK019 - バージョン情報はpyproject.tomlから動的に取得する要件が明記されているか？ [Gap]
- [x] CHK020 - 複数箇所でのバージョン定義（例: __init__.py、constants.py、pyproject.toml）の重複が禁止されているか？ [Gap, Anti-pattern]
- [x] CHK021 - importlib.metadata使用の根拠（PEP 566準拠、Python 3.8+標準ライブラリ）が技術的要件に記載されているか？ [Traceability, Gap]

## Acceptance Criteria Quality

- [x] CHK022 - `uvx llm-discovery --version`の期待される出力形式（例: "llm-discovery, version 1.0.0"）が定義されているか？ [Measurability, Gap]
- [x] CHK023 - Python APIでのバージョン確認方法（例: `import llm_discovery; print(llm_discovery.__version__)`）の検証基準が定義されているか？ [Measurability, Gap]
- [ ] CHK024 - バージョン取得のパフォーマンス要件（例: <10ms）が定義されているか？ [Measurability, Gap]
- [x] CHK025 - バージョン情報の正確性検証方法（pyproject.tomlとの一致確認）がテスト要件に含まれているか？ [Measurability, Gap]

## Scenario Coverage

- [x] CHK026 - 正常系シナリオ: パッケージインストール後の`--version`実行の要件が定義されているか？ [Coverage, Primary Flow]
- [x] CHK027 - 異常系シナリオ: パッケージメタデータが存在しない場合のエラーハンドリング要件が定義されているか？ [Coverage, Exception Flow, Gap]
- [x] CHK028 - 開発環境シナリオ: editable install（`uv pip install -e .`）でのバージョン取得の要件が定義されているか？ [Coverage, Alternate Flow, Gap]
- [x] CHK029 - CI/CDシナリオ: ビルド時のバージョン番号自動検証の要件が定義されているか？ [Coverage, Non-Functional, Gap]

## Edge Case Coverage

- [ ] CHK030 - importlib.metadataのインポート失敗時（Python <3.8環境）のフォールバック要件が定義されているか？ [Edge Case, Gap]
- [ ] CHK031 - パッケージ名の大文字小文字違い（llm-discovery vs LLM-Discovery）でのメタデータ取得の堅牢性要件が定義されているか？ [Edge Case, Gap]
- [ ] CHK032 - バージョン情報に特殊文字（例: 1.0.0-alpha+build.123）が含まれる場合の処理要件が定義されているか？ [Edge Case, Gap]
- [ ] CHK033 - 複数バージョンのパッケージが同時にインストールされている場合の動作が定義されているか？ [Edge Case, Gap]

## Implementation Guidance Quality

- [x] CHK034 - llm_discovery/__init__.pyでのimportlib.metadata使用例が実装ガイドに含まれているか？ [Gap]
- [x] CHK035 - typerアプリケーションでの`--version`オプション実装パターン（例: `version_callback`使用）が明記されているか？ [Gap, Task T039]
- [ ] CHK036 - pyproject.tomlのdynamic version設定（例: setuptools-scm使用）の要否が明確化されているか？ [Gap]
- [ ] CHK037 - バージョン取得コードのテスト方法（例: monkeypatchでimportlib.metadataをモック）が定義されているか？ [Gap, Test Strategy]

## Dependencies & Assumptions

- [x] CHK038 - Python 3.8+の前提（importlib.metadata標準ライブラリ化）が明記されているか？ [Assumption, Plan §Language/Version: Python 3.13+]
- [ ] CHK039 - importlib.metadata互換性（Python 3.8-3.9ではimportlib_metadata backportが必要）の要件が定義されているか？ [Dependency, Gap]
- [ ] CHK040 - pyproject.tomlのproject.versionフィールドが必須であることが依存関係として明記されているか？ [Dependency, Gap]
- [ ] CHK041 - uvxによる実行時のメタデータアクセス可能性が検証されているか？ [Assumption, Gap]

## Traceability & Documentation

- [x] CHK042 - バージョン管理方針がREADME.mdまたはCONTRIBUTING.mdで文書化される要件が定義されているか？ [Gap, Task T078-T079]
- [x] CHK043 - セマンティックバージョニングポリシー（contracts/で定義済み）とpyproject.toml管理の関係がトレース可能か？ [Traceability, Spec Versioning]
- [ ] CHK044 - バージョン番号の更新プロセス（手動 vs 自動タグベース）が要件として定義されているか？ [Gap]
- [ ] CHK045 - リリースノート生成時のバージョン情報取得元が明記されているか？ [Gap]

## Test Coverage Requirements

- [x] CHK046 - `--version`フラグの契約テスト（tests/contract/test_cli_interface.py）にバージョン形式検証が含まれているか？ [Coverage, Task T042]
- [x] CHK047 - Python APIのバージョン属性テスト（tests/contract/test_python_api.py）が定義されているか？ [Coverage, Task T072, Gap]
- [x] CHK048 - importlib.metadata.version()呼び出しのユニットテスト要件が定義されているか？ [Coverage, Gap]
- [x] CHK049 - バージョン取得失敗時のエラーハンドリングテスト要件が定義されているか？ [Coverage, Exception Flow, Gap]
- [x] CHK050 - FR-020（テストカバレッジ90%以上）がバージョン管理コードにも適用されることが明記されているか？ [Coverage, Spec FR-020]

## Anti-Patterns & Risks

- [x] CHK051 - __version__ = "1.0.0"のようなハードコーディングが明示的に禁止されているか？ [Anti-pattern, Gap]
- [x] CHK052 - constants.py内でのVERSION定数定義が禁止されているか（Primary Data Non-Assumption違反）？ [Anti-pattern, Gap, Task T012]
- [x] CHK053 - 複数ファイルでのバージョン情報重複管理のリスクが文書化されているか？ [Risk, Gap]
- [x] CHK054 - バージョン情報の不一致（pyproject.toml vs 実行時出力）のリスク軽減策が定義されているか？ [Risk, Gap]

---

## Summary

**Total Items**: 54

**Key Findings**:
- ✅ Versioningポリシーはcontracts/で定義済み（セマンティックバージョニング、後方互換性）
- ✅ `--version`フラグの要件は存在（contracts/cli-interface.md §Global Options）
- ⚠️ **Critical Gap**: バージョン情報の取得方法（importlib.metadata使用）が明示的に仕様化されていない
- ⚠️ **Critical Gap**: ハードコーディング禁止の要件が欠如（Primary Data Non-Assumption Principleに反する可能性）
- ⚠️ **Critical Gap**: `__version__`属性の公開API要件が未定義
- ⚠️ Task T012でCACHE_VERSIONを定数定義する計画があるが、パッケージバージョンとの関係が不明確

**Recommendations**:
1. spec.mdまたはplan.mdにバージョン管理の技術的要件セクションを追加
2. importlib.metadata使用の明示的な要件を定義
3. Task T012のconstants.pyでパッケージバージョンのハードコーディングを禁止
4. llm_discovery/__init__.pyでの__version__公開要件を追加
5. contracts/にバージョン取得の実装ガイドを追加
