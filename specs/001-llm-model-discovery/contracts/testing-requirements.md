# Testing Requirements Contract

**Feature**: [spec.md](../spec.md)
**Data Model**: [data-model.md](../data-model.md)

## Purpose

このドキュメントは、`llm-discovery`のテスト要件とカバレッジ基準を定義します。契約テスト、統合テスト、ユニットテスト、カバレッジ目標を規定し、すべての機能要件とUser Storiesが検証可能であることを保証します（FR-020）。

## Specification

### Coverage Requirements

**必須カバレッジ**: 90%以上（FR-020）

**測定対象**:
- ライン カバレッジ（Line Coverage）
- ブランチカバレッジ（Branch Coverage）

**ツール**:
- pytest-cov
- coverage.py

**実行コマンド**:
```bash
pytest --cov=llm_discovery --cov-report=html --cov-report=term
```

**カバレッジ目標（モジュール別）**:

| Module                        | Target Coverage | Priority |
|-------------------------------|-----------------|----------|
| `llm_discovery/models/`       | 95-100%         | P0       |
| `llm_discovery/cli/`          | 90-95%          | P1       |
| `llm_discovery/api/`          | 90-95%          | P1       |
| `llm_discovery/providers/`    | 90-95%          | P1       |
| `llm_discovery/export/`       | 90-95%          | P2       |
| `llm_discovery/cache/`        | 90-95%          | P1       |
| `llm_discovery/exceptions.py` | 100%            | P0       |

### Test Categories

#### Category 1: Contract Tests

**目的**: CLI契約、Python API契約、データフォーマット契約を検証

**配置**: `tests/contract/`

**テスト対象**:

1. **CLI Interface Contract**:
   - コマンド構造の正確性
   - オプションの動作
   - 終了コードの一貫性
   - エラーメッセージの内容

2. **Python API Contract**:
   - クラス・メソッドシグネチャの正確性
   - 型ヒントの整合性
   - 例外階層の整合性
   - 非同期APIの動作

3. **Data Format Contract**:
   - JSONスキーマ準拠
   - CSV、YAML、TOML、Markdown形式の正確性
   - エクスポート形式の一貫性

**テストファイル**:

- `tests/contract/test_cli_interface.py`:
  - User Story 1のAcceptance Scenarios（全6シナリオ）
  - User Story 2のAcceptance Scenarios（全5シナリオ）
  - User Story 3のAcceptance Scenarios（全4シナリオ）

  ```python
  def test_user_story_1_scenario_1_initial_fetch():
      """
      Given 初回実行時
      When `uvx llm-discovery list` を実行
      Then OpenAI、Google、AnthropicのモデルがAPI/手動データから取得され、
           TOML形式でキャッシュに保存される
      """
      result = subprocess.run(
          ["llm-discovery", "list"],
          capture_output=True,
          text=True
      )
      assert result.returncode == 0
      assert "openai" in result.stdout
      assert "google" in result.stdout
      assert "anthropic" in result.stdout

      # キャッシュファイルが作成されたことを確認
      cache_path = Path.home() / ".cache/llm-discovery/models_cache.toml"
      assert cache_path.exists()
  ```

- `tests/contract/test_python_api.py`:
  - User Story 4のAcceptance Scenarios（全4シナリオ）

  ```python
  @pytest.mark.asyncio
  async def test_user_story_4_scenario_2_python_api():
      """
      Given Pythonスクリプト
      When `from llm_discovery import DiscoveryClient` でインポート
      Then CLIと同じ機能をPython APIとして利用できる
      """
      from llm_discovery import DiscoveryClient

      client = DiscoveryClient()
      models = await client.fetch_models()

      assert isinstance(models, list)
      assert len(models) > 0
      assert all(isinstance(m, Model) for m in models)
  ```

- `tests/contract/test_data_formats.py`:
  - User Story 2のAcceptance Scenariosを各形式ごとに検証

  ```python
  def test_user_story_2_scenario_1_json_export():
      """
      Given モデルデータが存在する状態
      When `uvx llm-discovery export --format json` を実行
      Then CI/CD統合に最適化されたJSON形式でデータが出力される
      """
      result = subprocess.run(
          ["llm-discovery", "export", "--format", "json"],
          capture_output=True,
          text=True
      )
      assert result.returncode == 0

      # JSONスキーマ検証
      data = json.loads(result.stdout)
      assert "metadata" in data
      assert "models" in data
      assert data["metadata"]["version"] == "1.0"
  ```

#### Category 2: Integration Tests

**目的**: 複数のコンポーネントの統合動作を検証

**配置**: `tests/integration/`

**テスト対象**:
- API取得→キャッシュ保存→読み込みの一連のフロー
- エクスポート→ファイル生成→内容検証
- 差分検出→changes.json生成→CHANGELOG.md更新

**テストファイル**:

- `tests/integration/cli/test_cli_workflow.py`:
  - 初回実行→キャッシュ→差分検出の一連のフロー

  ```python
  def test_full_cli_workflow(tmp_path, monkeypatch):
      """完全なCLIワークフローを検証"""
      # 環境変数設定
      monkeypatch.setenv("LLM_DISCOVERY_CACHE_DIR", str(tmp_path))

      # 初回実行
      result1 = subprocess.run(
          ["llm-discovery", "list"],
          capture_output=True,
          text=True
      )
      assert result1.returncode == 0

      # キャッシュ確認
      cache_file = tmp_path / "models_cache.toml"
      assert cache_file.exists()

      # 差分検出
      result2 = subprocess.run(
          ["llm-discovery", "list", "--detect-changes"],
          capture_output=True,
          text=True
      )
      assert result2.returncode == 0
  ```

- `tests/integration/api/test_api_workflow.py`:
  - Python API経由の取得→エクスポート→保存

  ```python
  @pytest.mark.asyncio
  async def test_api_export_workflow(tmp_path):
      """Python APIのエクスポートワークフローを検証"""
      from llm_discovery import DiscoveryClient, export_json

      client = DiscoveryClient()
      models = await client.fetch_models()

      # JSON形式でエクスポート
      json_str = export_json(models)

      # ファイルに保存
      output_path = tmp_path / "models.json"
      output_path.write_text(json_str)

      # 内容検証
      data = json.loads(json_str)
      assert len(data["models"]) == len(models)
  ```

#### Category 3: Unit Tests

**目的**: 個別のモジュール・関数・クラスの動作を検証

**配置**: `tests/unit/`

**テスト対象**:
- Pydanticモデルのバリデーション
- エクスポート関数の出力形式
- エラーハンドリングロジック
- キャッシュの読み書き

**テストファイル**:

- `tests/unit/models/test_model.py`:
  - `Model`クラスのバリデーション

  ```python
  def test_model_validation_success():
      """正常なモデル作成"""
      model = Model(
          model_id="gpt-4",
          model_name="GPT-4",
          provider_name="openai",
          source=ModelSource.API,
          fetched_at=datetime.now(),
          metadata={"context_window": 8192}
      )
      assert model.model_id == "gpt-4"

  def test_model_validation_empty_id():
      """空のmodel_idはエラー"""
      with pytest.raises(ValueError, match="model_id cannot be empty"):
          Model(
              model_id="",
              model_name="GPT-4",
              provider_name="openai",
              source=ModelSource.API
          )
  ```

- `tests/unit/export/test_json_export.py`:
  - JSON形式のエクスポート

  ```python
  def test_json_export_format():
      """JSON形式の正確性"""
      models = [
          Model(
              model_id="gpt-4",
              model_name="GPT-4",
              provider_name="openai",
              source=ModelSource.API,
              fetched_at=datetime.now()
          )
      ]

      json_str = export_json(models)
      data = json.loads(json_str)

      assert "metadata" in data
      assert "models" in data
      assert len(data["models"]) == 1
  ```

- `tests/unit/errors/test_error_messages.py`:
  - エラーメッセージの内容

  ```python
  def test_provider_fetch_error_message():
      """ProviderFetchErrorのメッセージ形式"""
      error = ProviderFetchError(
          provider_name="openai",
          cause="Connection timeout"
      )

      assert "openai" in str(error)
      assert "Connection timeout" in str(error)
  ```

#### Category 4: Error Handling Tests

**目的**: エラー処理の正確性を検証

**配置**: `tests/error/`

**テスト対象**:
- 各エラークラスの生成と属性
- エラーメッセージの内容
- 例外チェーン（`raise ... from e`）
- リカバリ戦略

**テストファイル**:

- `tests/error/test_cli_errors.py`:
  - CLI実行時のエラー

  ```python
  def test_api_failure_error_message():
      """API障害時のエラーメッセージ"""
      # OpenAI APIを障害状態にモック
      with patch("httpx.AsyncClient.get", side_effect=httpx.TimeoutException):
          result = subprocess.run(
              ["llm-discovery", "list"],
              capture_output=True,
              text=True
          )

          assert result.returncode == 1
          assert "Failed to fetch models from OpenAI API" in result.stderr
          assert "Suggested actions" in result.stderr
  ```

- `tests/error/test_api_exceptions.py`:
  - Python APIの例外

  ```python
  @pytest.mark.asyncio
  async def test_partial_fetch_error_attributes():
      """PartialFetchErrorの属性"""
      error = PartialFetchError(
          successful_providers=["openai", "anthropic"],
          failed_providers=["google"]
      )

      assert error.successful_providers == ["openai", "anthropic"]
      assert error.failed_providers == ["google"]
      assert "openai" in str(error)
  ```

#### Category 5: Edge Case Tests

**目的**: エッジケースの処理を検証

**配置**: `tests/edge/`

**テスト対象**:
- 空のモデルリスト
- 特殊文字を含むモデル名
- 大量データ（1000モデル以上）
- Unicode文字列（日本語、絵文字等）
- メタデータなしのモデル

**テストファイル**:

- `tests/edge/test_edge_cases.py`:

  ```python
  def test_empty_model_list():
      """空のモデルリストのエクスポート"""
      models = []

      with pytest.raises(ValueError, match="models cannot be empty"):
          export_json(models)

  def test_special_characters_in_model_name():
      """特殊文字を含むモデル名"""
      model = Model(
          model_id="model-with-special-chars-🚀",
          model_name="Model with \"quotes\" and, commas",
          provider_name="openai",
          source=ModelSource.API
      )

      json_str = export_json([model])
      data = json.loads(json_str)

      assert data["models"][0]["model_id"] == "model-with-special-chars-🚀"
  ```

### Test Execution Strategy

#### Local Development

```bash
# すべてのテストを実行
pytest

# カバレッジレポート付き
pytest --cov=llm_discovery --cov-report=html --cov-report=term

# 特定のカテゴリのみ実行
pytest tests/contract/
pytest tests/unit/
pytest tests/integration/

# 特定のマーカーのみ実行
pytest -m "not slow"
```

#### CI/CD Pipeline

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.13'

      - name: Install dependencies
        run: |
          pip install uv
          uv pip install -e ".[dev]"

      - name: Run tests
        run: |
          pytest --cov=llm_discovery --cov-report=xml --cov-report=term

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
```

### Test Fixtures

**共通フィクスチャ**: `tests/conftest.py`

```python
import pytest
from pathlib import Path
from llm_discovery.models import Model, ModelSource
from datetime import datetime

@pytest.fixture
def sample_models():
    """サンプルモデルのリスト"""
    return [
        Model(
            model_id="gpt-4",
            model_name="GPT-4",
            provider_name="openai",
            source=ModelSource.API,
            fetched_at=datetime.now()
        ),
        Model(
            model_id="gemini-1.5-pro",
            model_name="Gemini 1.5 Pro",
            provider_name="google",
            source=ModelSource.API,
            fetched_at=datetime.now()
        ),
        Model(
            model_id="claude-3-opus",
            model_name="Claude 3 Opus",
            provider_name="anthropic",
            source=ModelSource.MANUAL,
            fetched_at=datetime.now()
        )
    ]

@pytest.fixture
def temp_cache_dir(tmp_path, monkeypatch):
    """一時キャッシュディレクトリ"""
    cache_dir = tmp_path / "llm-discovery"
    cache_dir.mkdir()
    monkeypatch.setenv("LLM_DISCOVERY_CACHE_DIR", str(cache_dir))
    return cache_dir
```

### Test Markers

**カスタムマーカー**: `pytest.ini`

```ini
[pytest]
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: integration tests
    contract: contract tests
    unit: unit tests
    edge: edge case tests
```

**使用例**:

```python
@pytest.mark.slow
@pytest.mark.integration
async def test_large_dataset_export():
    """大量データのエクスポート（時間がかかる）"""
    models = [create_sample_model() for _ in range(10000)]
    json_str = export_json(models)
    assert len(json.loads(json_str)["models"]) == 10000
```

### Coverage Enforcement

**pytest-cov設定**: `pyproject.toml`

```toml
[tool.coverage.run]
source = ["llm_discovery"]
omit = [
    "*/tests/*",
    "*/conftest.py",
    "*/__main__.py"
]

[tool.coverage.report]
fail_under = 90
precision = 2
show_missing = true
skip_covered = false

[tool.coverage.html]
directory = "htmlcov"
```

**CI/CDでの強制**:

```yaml
- name: Check coverage threshold
  run: |
    pytest --cov=llm_discovery --cov-report=term --cov-fail-under=90
```

### Test Documentation

**必須ドキュメント**: 各テストにdocstring

```python
def test_json_export_schema_compliance():
    """
    JSON形式のエクスポートがJSONSchemaに準拠していることを検証

    Given: 有効なモデルのリスト
    When: export_json()を実行
    Then: 出力がJSONSchemaに準拠し、必須フィールドが含まれる

    Reference: User Story 2 Scenario 1
    """
    models = [create_sample_model()]
    json_str = export_json(models)

    # JSONSchemaで検証
    schema = load_json_schema()
    validate(json.loads(json_str), schema)
```

## Test Requirements Summary

| Test Category       | Location              | Priority | Coverage Target | Count (Est.) |
|---------------------|-----------------------|----------|-----------------|--------------|
| Contract Tests      | `tests/contract/`     | P0       | 100%            | 20+          |
| Integration Tests   | `tests/integration/`  | P1       | 95%             | 15+          |
| Unit Tests          | `tests/unit/`         | P1       | 95%             | 100+         |
| Error Handling      | `tests/error/`        | P1       | 100%            | 20+          |
| Edge Cases          | `tests/edge/`         | P2       | 90%             | 10+          |
| **Total**           | **All**               | -        | **90%+**        | **165+**     |

## References

- **FR-020**: テストカバレッジ90%以上
- **User Story 1**: リアルタイムモデル一覧取得（6シナリオ）
- **User Story 2**: マルチフォーマットエクスポート（5シナリオ）
- **User Story 3**: 新モデル検知と差分レポート（4シナリオ）
- **User Story 4**: CI/CD統合とPython API利用（4シナリオ）
- **pytest Documentation**: https://docs.pytest.org/
- **pytest-cov Documentation**: https://pytest-cov.readthedocs.io/
