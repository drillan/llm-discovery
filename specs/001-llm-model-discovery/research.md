# Research: LLMモデル発見・追跡システム技術調査

**Date**: 2025-10-19 | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

このドキュメントは、LLMモデル発見・追跡システムの実装に必要な技術選択とその根拠をまとめた調査結果です。各項目について、Decision（決定）、Rationale（理由）、Alternatives considered（検討した代替案）の形式で記録しています。

---

## 1. OpenAI APIクライアントライブラリ

**Decision**: 公式`openai-python` (v1.x以降) を使用

**Rationale**:
- 公式ライブラリが`AsyncOpenAI`クライアントをネイティブサポート（Python 3.8+対応）
- httpxベースの型安全な実装（すべてのリクエスト/レスポンスに型定義）
- 同期・非同期の両方をサポート（`OpenAI`と`AsyncOpenAI`で機能は同一）
- 2025年時点で活発にメンテナンス、コミュニティ標準として確立
- Models List API (`GET /v1/models`) をネイティブサポート
- asyncio.gather()による並行リクエスト対応、セマフォによるレート制限管理が容易
- バックオフライブラリ（`backoff`）との統合によるエクスポネンシャルバックオフ実装が可能

**Alternatives considered**:
1. **httpx直接実装**:
   - 利点: 依存関係削減、完全なコントロール
   - 欠点: 型定義の自己実装が必要、APIの変更追従コスト、認証・リトライロジックの自己実装
   - 却下理由: 公式SDKの型安全性とメンテナンス性を失うコストが高い

2. **aiohttp直接実装**:
   - 利点: 高速、WebSocketサポート
   - 欠点: httpxより型安全性が低い、公式SDKとの統合不可
   - 却下理由: OpenAI APIにWebSocketは不要、公式SDKのhttpxで十分高速

**具体的な使用例**:
```python
from openai import AsyncOpenAI
import asyncio

async def fetch_openai_models(api_key: str) -> list[dict]:
    client = AsyncOpenAI(api_key=api_key)
    response = await client.models.list()
    return [model.model_dump() for model in response.data]
```

**バージョン**: `openai>=1.0.0` (2025年安定版)

---

## 2. Google AI/Vertex AIクライアントライブラリ

**Decision**:
- Google AI Studio: `google-generativeai` (新しい統合SDK)
- Vertex AI: `google-cloud-aiplatform` または新しい`@google/genai` SDK

**Rationale**:
- **2025年6月の重大な変更**: Vertex AI SDKのGenerative AIモジュール（`vertexai.generative_models`等）は2025年6月24日に非推奨化、2026年6月24日に削除予定
- **新しい統合SDK**: GoogleがGoogle GenAI SDKをリリース、Google AI StudioとVertex AIの切り替えが可能
- **環境変数による切り替え**: `GOOGLE_GENAI_USE_VERTEXAI`で環境切り替えが可能（FR-002要件を満たす）
- **認証方法の違い**:
  - Google AI Studio: APIキーによるシンプルな認証
  - Vertex AI: IAM、サービスアカウント、複雑な権限管理（エンタープライズ向け）
- **Models List API**: `models.list()`メソッドで利用可能モデルの一覧取得が可能（ページネーション対応、デフォルト50件/ページ）

**Alternatives considered**:
1. **google-generativeai単独**:
   - 利点: シンプル、APIキー認証のみ、モバイル/Firebase対応
   - 欠点: Vertex AIの高度な機能（MLOps、監視）にアクセス不可
   - 却下理由: FR-002でVertex AI切り替え要件がある

2. **google-cloud-aiplatform単独**:
   - 利点: エンタープライズ機能、Cloud統合
   - 欠点: 複雑な認証、Google AI Studioには使用不可
   - 却下理由: Google AI Studio対応が必須

3. **両方のライブラリを常時インストール**:
   - 利点: 完全な機能カバレッジ
   - 欠点: 依存関係の肥大化、新SDK移行の遅れ
   - 採用理由: **現時点での推奨アプローチ**（2026年6月まで移行期間）

**具体的な使用例**:
```python
import os
from google import genai

async def fetch_google_models() -> list[dict]:
    use_vertex = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "false").lower() == "true"

    if use_vertex:
        # Vertex AI認証（Application Default Credentials）
        client = genai.Client(
            vertexai=True,
            project=os.environ["GOOGLE_CLOUD_PROJECT"],
            location=os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
        )
    else:
        # Google AI Studio認証（APIキー）
        client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])

    models = []
    for model in client.models.list():
        for action in model.supported_actions:
            if action == "generateContent":
                models.append({
                    "name": model.name,
                    "display_name": model.display_name,
                    "description": model.description,
                })
    return models
```

**バージョン**:
- `google-generativeai>=0.8.0`（新しい統合SDK対応版）
- `google-cloud-aiplatform>=1.70.0`（移行期間のフォールバック）

---

## 3. Anthropicモデルリストの手動管理方式

**Decision**: TOMLファイルによるリポジトリ内管理

**Rationale**:
- **APIが存在しない**: Anthropic APIにはモデル一覧取得エンドポイントが存在しない（2025年10月時点）
- **TOML選択理由**:
  - Python 3.11+で`tomllib`が標準ライブラリ化（読み込み）
  - 人間が読みやすく、コメント記述可能（モデルの説明、リリース日等を記録）
  - 階層構造とデータ型のネイティブサポート（日付型、配列、テーブル）
  - `pyproject.toml`との一貫性（プロジェクト全体でTOML使用）
- **リポジトリ内管理**:
  - バージョン管理可能（変更履歴の追跡）
  - オフラインアクセス可能
  - CI/CDでの検証可能（スキーマバリデーション）

**Alternatives considered**:
1. **JSON形式**:
   - 利点: 標準ライブラリのみ、パース高速
   - 欠点: コメント不可、日付型なし、人間可読性が低い
   - 却下理由: 手動メンテナンスに不向き

2. **YAML形式**:
   - 利点: 可読性高い、複雑な構造サポート
   - 欠点: 標準ライブラリなし（PyYAML依存）、インデント厳格でエラー起きやすい
   - 却下理由: 余分な依存関係、トラブルシューティング困難

3. **外部ソース（GitHub Gist等）**:
   - 利点: リポジトリ肥大化防止
   - 欠点: ネットワーク依存、バージョン管理困難、信頼性低下
   - 却下理由: オフライン動作不可、Primary Data Non-Assumption違反

**データ構造例**:
```toml
# src/llm_discovery/data/anthropic_models.toml
version = "2025-10-19"

[[models]]
name = "claude-sonnet-4-5-20250929"
display_name = "Claude Sonnet 4.5"
release_date = 2025-09-29
description = "Best coding model in the world"
input_price_per_million = 3.0
output_price_per_million = 15.0

[[models]]
name = "claude-haiku-4-5"
display_name = "Claude Haiku 4.5"
release_date = 2025-10-15
description = "Fast, cost-effective model"
input_price_per_million = 1.0
output_price_per_million = 5.0
```

**更新戦略**:
- 手動更新（Anthropic公式ドキュメント監視）
- バージョン番号による更新追跡
- CI/CDでのスキーマバリデーション（Pydanticモデル）
- 変更履歴はGitコミットで管理

---

## 4. キャッシュディレクトリの配置

**Decision**: `platformdirs`ライブラリを使用したXDG Base Directory仕様準拠

**Rationale**:
- **クロスプラットフォーム対応**: Linux、macOS、Windowsで適切なキャッシュディレクトリを自動選択
  - Linux: `~/.cache/llm-discovery/` (XDG_CACHE_HOME準拠)
  - macOS: `~/Library/Caches/llm-discovery/`
  - Windows: `%LOCALAPPDATA%\llm-discovery\Cache`
- **標準準拠**: XDG Base Directory仕様（Linux）、各OSのガイドライン準拠
- **platformdirs採用理由**:
  - Debian公式パッケージとして採用（python3-platformdirs）
  - `user_cache_dir()`、`user_data_dir()`、`user_config_dir()`等の包括的なAPI
  - アクティブにメンテナンス、多くのPythonプロジェクトで採用実績
- **手動実装との比較**: OSごとの環境変数処理、パス結合、ディレクトリ作成を自動化

**Alternatives considered**:
1. **xdg-base-dirs**:
   - 利点: XDG仕様専用、シンプル
   - 欠点: Linux専用（macOS、Windows非対応）
   - 却下理由: クロスプラットフォーム要件を満たせない

2. **PyXDG**:
   - 利点: 歴史が長い、機能豊富
   - 欠点: Linux専用、メンテナンス頻度が低い
   - 却下理由: platformdirsが後継として推奨されている

3. **手動実装**:
   - 利点: 依存関係なし
   - 欠点: OSごとの環境変数、パス処理の自己実装、バグリスク
   - 却下理由: 車輪の再発明、テスト負荷増大

**具体的な使用例**:
```python
from platformdirs import user_cache_dir
from pathlib import Path

def get_cache_dir() -> Path:
    """
    Get the cache directory for llm-discovery.

    Returns:
        Path object for the cache directory (e.g., ~/.cache/llm-discovery/)
    """
    cache_dir = Path(user_cache_dir("llm-discovery", "llm-discovery"))
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir
```

**バージョン**: `platformdirs>=4.0.0`

---

## 5. TOMLライブラリ選定

**Decision**: `tomllib` (標準ライブラリ、読み込み) + `tomli-w` (PyPI、書き込み)

**Rationale**:
- **Python 3.11+標準化**: PEP 680により`tomllib`が標準ライブラリに追加（TOML 1.0.0完全準拠）
- **読み書き分離**:
  - `tomllib`: 読み込み専用、標準ライブラリのため追加依存なし
  - `tomli-w`: 書き込み専用（`tomllib`の公式推奨パートナー）
  - `marshal`、`pickle`モジュールと同様のAPI設計
- **後方互換性**: `tomli` (PyPI) がPython 3.11未満のバックポートとして利用可能
- **2025年1月リリース**: `tomli-w` v1.2.0が最新（活発にメンテナンス）

**Alternatives considered**:
1. **toml (PyPI)**:
   - 利点: 読み書き両対応、古いPythonバージョン対応
   - 欠点: メンテナンス頻度低い、Python 3.11+では不要
   - 却下理由: 標準ライブラリ優先原則

2. **tomli単独**:
   - 利点: 読み込みのみならシンプル
   - 欠点: 書き込み不可（キャッシュ保存に必要）
   - 却下理由: 書き込み機能が必須（FR-010、FR-011）

3. **tomlkit**:
   - 利点: フォーマット保持、コメント保持
   - 欠点: パフォーマンス低い、複雑
   - 却下理由: オーバースペック（単純な読み書きで十分）

**具体的な使用例**:
```python
import tomllib  # Python 3.11+標準ライブラリ
import tomli_w
from pathlib import Path

# 読み込み
def load_cache(cache_file: Path) -> dict:
    with open(cache_file, "rb") as f:
        return tomllib.load(f)

# 書き込み
def save_cache(cache_file: Path, data: dict) -> None:
    with open(cache_file, "wb") as f:
        tomli_w.dump(data, f)
```

**バージョン**:
- `tomllib`: 標準ライブラリ（Python 3.11+）
- `tomli-w>=1.2.0`

---

## 6. Pydantic v2のバリデーション戦略

**Decision**:
- フィールド単位の検証: `@field_validator` (デコレータ)
- 複数フィールド間の検証: `@model_validator(mode='after')`
- 再利用可能な検証: `Annotated`パターン + `AfterValidator`

**Rationale**:
- **Pydantic v2の強化機能**:
  - `@field_validator`: フィールド検証、他フィールドへのアクセス（`ValidationInfo.data`経由）
  - `@model_validator`: モデル全体の検証、クロスフィールド検証に最適
  - `mode='after'`: Pydantic内部検証後に実行（型強制後の検証）
- **エラーハンドリング**:
  - `ValidationError`を直接raiseしない（`ValueError`または`AssertionError`を使用）
  - Pydanticが自動的に`ValidationError`に変換、詳細なエラーメッセージ生成
- **常時検証**: `Field(validate_default=True)`でデフォルト値も検証
- **型安全性**: すべてのフィールドに型ヒント必須、厳格な型チェック

**Alternatives considered**:
1. **@field_validator単独**:
   - 利点: シンプル、フィールド順序制御可能
   - 欠点: クロスフィールド検証が煩雑、フィールド順序依存
   - 却下理由: `@model_validator`の方が明示的

2. **カスタムバリデータ関数（非デコレータ）**:
   - 利点: 再利用可能
   - 欠点: Pydantic v2では非推奨、`Annotated`パターン推奨
   - 却下理由: v2のベストプラクティス違反

3. **手動検証（__init__内）**:
   - 利点: 完全なコントロール
   - 欠点: Pydanticの機能を無視、型安全性の喪失
   - 却下理由: Pydanticを使う意味がない

**具体的な使用例**:
```python
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Annotated
from pydantic.functional_validators import AfterValidator

# フィールド検証
class ModelInfo(BaseModel):
    name: str
    display_name: str
    context_window: int = Field(gt=0, validate_default=True)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Model name cannot be empty")
        return v.lower()  # 正規化

# クロスフィールド検証
class PricingInfo(BaseModel):
    input_price: float = Field(ge=0)
    output_price: float = Field(ge=0)

    @model_validator(mode='after')
    def validate_pricing(self) -> 'PricingInfo':
        if self.output_price < self.input_price:
            raise ValueError("Output price should be >= input price")
        return self

# 再利用可能な検証（Annotatedパターン）
def validate_positive(v: float) -> float:
    if v <= 0:
        raise ValueError("Value must be positive")
    return v

PositiveFloat = Annotated[float, AfterValidator(validate_positive)]

class TokenLimit(BaseModel):
    max_tokens: PositiveFloat
```

**バージョン**: `pydantic>=2.0.0`

---

## 7. 非同期HTTPクライアント

**Decision**:
- OpenAI/Google公式SDK（内部でhttpx使用）を優先
- 直接HTTP通信が必要な場合: `httpx` (HTTP/2対応)

**Rationale**:
- **パフォーマンス比較**（2025年ベンチマーク）:
  - aiohttp: 最速（20並行リクエストでhttpxの10倍以上高速）
  - httpx: 同期・非同期統一API、HTTP/2対応
  - requests: 同期のみ
- **しかし公式SDK優先の理由**:
  - 型安全性（すべてのAPI応答に型定義）
  - 認証、リトライ、エラーハンドリングの標準実装
  - APIの変更への自動追従
  - メンテナンスコストの削減
- **httpx選択理由**（直接通信時）:
  - 同期・非同期の統一API（OpenAI/Google SDKと一貫性）
  - HTTP/2対応（将来的なパフォーマンス向上）
  - 公式SDKがhttpxベース（依存関係の共通化）
- **aiohttpを不採用**:
  - 最速だが非同期専用（同期APIなし）
  - 型安全性がhttpxより低い
  - 公式SDKとの統合不可
  - WebSocket不要（LLM API用途）

**Alternatives considered**:
1. **aiohttp直接使用**:
   - 利点: 最高速、WebSocketサポート、高並行性能
   - 欠点: 公式SDK不使用、型定義自己実装、メンテナンス負荷
   - 却下理由: 速度よりも型安全性とメンテナンス性を優先

2. **requests (同期)**:
   - 利点: シンプル、広く使用
   - 欠点: 非同期非対応、並行取得不可（SC-007違反）
   - 却下理由: パフォーマンス要件を満たせない

3. **複数ライブラリ混在**:
   - 利点: 用途別最適化
   - 欠点: 依存関係肥大化、コード複雑化
   - 却下理由: Simplicity原則違反

**具体的な使用例**:
```python
import asyncio
from openai import AsyncOpenAI
from google import genai

# 公式SDK使用（推奨）
async def fetch_all_models():
    # OpenAI（内部でhttpx使用）
    openai_client = AsyncOpenAI(api_key=api_key)
    openai_models = await openai_client.models.list()

    # Google（内部でhttpx使用）
    google_client = genai.Client(api_key=google_key)
    google_models = list(google_client.models.list())

    return openai_models, google_models

# 直接httpx使用（公式SDK未対応の場合のみ）
import httpx

async def fetch_with_httpx(url: str, headers: dict) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
```

**バージョン**:
- 公式SDK依存（`openai>=1.0.0`、`google-generativeai>=0.8.0`）
- `httpx>=0.27.0`（直接通信時のみ）

---

## 8. Rich出力のカスタマイズ方針

**Decision**:
- モデル一覧: `rich.table.Table`
- 処理状況: `rich.progress.Progress`
- ログ/エラー: `rich.console.Console`

**Rationale**:
- **Rich選択理由**:
  - Python 3.8+対応、Jupyter完全サポート
  - Unicode box描画、自動列リサイズ、テキスト折り返し
  - CI/CD環境での動作保証（色なし端末への自動フォールバック）
- **Table使用場面**:
  - `llm-discovery list`のモデル一覧表示
  - 列の自動リサイズ（ターミナル幅に適応）
  - カスタマイズ可能なスタイル、セル配置、境界線
- **Progress使用場面**:
  - 複数プロバイダーからの並行取得時の進捗表示
  - フリッカーフリー（ちらつきなし）
  - `progress.console`への出力で進捗バーの上にメッセージ表示
- **Console使用場面**:
  - エラーメッセージ（stderr）
  - 詳細ログ（`--verbose`フラグ時）
  - 変更検知結果の差分表示

**Alternatives considered**:
1. **標準print()のみ**:
   - 利点: 依存関係なし、シンプル
   - 欠点: 美しい出力不可、表形式の手動整形
   - 却下理由: ユーザー体験低下

2. **prettytable**:
   - 利点: 軽量、テーブル特化
   - 欠点: 進捗バー、カラー出力が限定的
   - 却下理由: Richの方が包括的

3. **tqdm (進捗バー)**:
   - 利点: 軽量、広く使用
   - 欠点: テーブル、コンソールログ機能なし
   - 却下理由: 複数機能の統合にRichが適切

**具体的な使用例**:
```python
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

# テーブル出力
def display_models(models: list[dict]) -> None:
    table = Table(title="Available LLM Models", show_header=True, header_style="bold magenta")
    table.add_column("Provider", style="cyan", no_wrap=True)
    table.add_column("Model Name", style="green")
    table.add_column("Context Window", justify="right", style="yellow")

    for model in models:
        table.add_row(model["provider"], model["name"], str(model["context_window"]))

    console.print(table)

# 進捗バー
async def fetch_all_with_progress() -> dict:
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Fetching models...", total=3)

        openai_task = progress.add_task("OpenAI", total=None)
        openai_models = await fetch_openai_models()
        progress.update(task, advance=1)

        google_task = progress.add_task("Google", total=None)
        google_models = await fetch_google_models()
        progress.update(task, advance=1)

        anthropic_task = progress.add_task("Anthropic", total=None)
        anthropic_models = load_anthropic_models()
        progress.update(task, advance=1)

    return {"openai": openai_models, "google": google_models, "anthropic": anthropic_models}

# エラー出力
def handle_error(error: Exception) -> None:
    console.print(f"[bold red]Error:[/bold red] {str(error)}", style="red")
```

**バージョン**: `rich>=13.0.0`

---

## 9. pytest設定（カバレッジ90%達成戦略）

**Decision**: `pytest-cov`による自動カバレッジ測定、CI統合、80%閾値/90%目標

**Rationale**:
- **90%目標の根拠**:
  - FR-020要件（カバレッジ90%以上）
  - 業界標準（Google: 90%を模範的、75%を称賛、60%を許容）
  - コアビジネスロジックは90-100%、ユーティリティ関数は70-80%
- **pytest-cov選択理由**:
  - pytest公式プラグイン、広く採用
  - 複数形式のレポート（terminal、HTML、XML）
  - CI/CDパイプラインへの統合容易（GitHub Actions、Codecov等）
  - `--cov`オプションでパッケージ指定可能
- **閾値設定戦略**:
  - 目標: 90%（理想）
  - 閾値: 80%（ビルド失敗ライン）
  - 理由: 90%固定だとビルドが頻繁に失敗、開発速度低下
- **品質重視**:
  - カバレッジは手段であり目的ではない
  - 重要なコードパス（エラーハンドリング、API統合）を優先
  - 未テストの10%が重要機能を含まないこと確認

**Alternatives considered**:
1. **coverage.py直接使用**:
   - 利点: pytest依存なし
   - 欠点: pytest統合の手動実装、レポート生成の煩雑さ
   - 却下理由: pytest-covが標準、統合が容易

2. **100%カバレッジ要求**:
   - 利点: 完全なテスト
   - 欠点: 非現実的、開発速度低下、無意味なテスト増加
   - 却下理由: 品質より数値を追う本末転倒

3. **カバレッジ測定なし**:
   - 利点: シンプル、高速
   - 欠点: テスト品質の可視化不可、FR-020違反
   - 却下理由: 要件違反

**具体的な設定例**:
```toml
# pyproject.toml
[tool.pytest.ini_options]
minversion = "8.0"
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "--cov=llm_discovery",
    "--cov-report=term-missing:skip-covered",
    "--cov-report=html",
    "--cov-report=xml",
    "--cov-fail-under=80",  # 閾値: 80%（ビルド失敗）
    "--strict-markers",
    "--strict-config",
    "-ra",
]

[tool.coverage.run]
source = ["src"]
omit = [
    "*/tests/*",
    "*/__pycache__/*",
    "*/site-packages/*",
]

[tool.coverage.report]
precision = 2
show_missing = true
skip_covered = false
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
]
```

**GitHub Actions統合**:
```yaml
# .github/workflows/test.yml
- name: Run tests with coverage
  run: |
    uv run pytest --cov=llm_discovery --cov-report=xml

- name: Upload coverage to Codecov
  uses: codecov/codecov-action@v4
  with:
    file: ./coverage.xml
    fail_ci_if_error: true
    flags: unittests
```

**バージョン**: `pytest>=8.0.0`, `pytest-cov>=6.0.0`

---

## 10. セマンティックバージョニング実装

**Decision**: `pyproject.toml`での静的バージョン管理

**Rationale**:
- **静的バージョンの利点**:
  - シンプル: `pyproject.toml`の`version = "X.Y.Z"`のみ
  - レビュー可能: バージョン変更がPull Requestで明確
  - uvx互換性: 動的バージョンでも動作するが、静的が推奨
  - 標準準拠: PyPA（Python Packaging Authority）の推奨
- **手動更新プロセス**:
  1. 機能実装完了
  2. `pyproject.toml`の`version`を手動更新（SemVer準拠）
  3. Gitタグ作成（`git tag vX.Y.Z`）
  4. プッシュ（`git push --tags`）
- **SemVer準拠**:
  - MAJOR: 破壊的変更（例: 2.0.0）
  - MINOR: 新機能追加（後方互換性あり、例: 1.1.0）
  - PATCH: バグ修正（例: 1.0.1）

**Alternatives considered**:
1. **setuptools-scm（動的バージョン）**:
   - 利点: Gitタグから自動生成、開発版バージョンサポート
   - 欠点: ビルド時の複雑性、デバッグ困難、レビュー時の可視性低下
   - 却下理由: シンプル性原則違反、静的で十分

2. **bump2version（自動バンプ）**:
   - 利点: コマンド一発でバージョン更新
   - 欠点: 余分なツール、設定ファイル必要
   - 却下理由: 手動更新で十分、ツール肥大化防止

3. **python-semantic-release（完全自動）**:
   - 利点: コミットメッセージからバージョン自動決定
   - 欠点: コミットメッセージ形式の強制、複雑、レビューフロー変更
   - 却下理由: オーバーエンジニアリング、小規模プロジェクトに不適

**具体的な設定例**:
```toml
# pyproject.toml
[project]
name = "llm-discovery"
version = "0.1.0"  # 手動管理
description = "LLM model discovery and tracking system"
readme = "README.md"
requires-python = ">=3.13"
license = {text = "MIT"}
authors = [
    {name = "Your Name", email = "your.email@example.com"}
]

[project.scripts]
llm-discovery = "llm_discovery.cli:app"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

**バージョン取得（実装側）**:
```python
from importlib.metadata import version, PackageNotFoundError

def get_version() -> str:
    """
    Get the current version of llm-discovery.

    Returns:
        Version string (e.g., "0.1.0")

    Raises:
        RuntimeError: If version cannot be determined (FR-022)
    """
    try:
        return version("llm-discovery")
    except PackageNotFoundError as e:
        raise RuntimeError(
            "Cannot determine package version. "
            "Ensure llm-discovery is properly installed."
        ) from e
```

**更新フロー例**:
```bash
# 1. 機能実装完了
git add .
git commit -m "feat: add change detection feature"

# 2. バージョン更新（手動編集）
# pyproject.toml: version = "0.1.0" -> version = "0.2.0"

# 3. バージョン更新コミット
git add pyproject.toml
git commit -m "chore: bump version to 0.2.0"

# 4. Gitタグ作成
git tag v0.2.0 -m "Release version 0.2.0"

# 5. プッシュ
git push origin main
git push origin v0.2.0
```

**バージョン**: 静的管理（ツール依存なし）

---

## まとめ: 依存関係一覧

以下は、このプロジェクトで使用する主要な依存関係の一覧です。

### 必須依存関係（Production）

```toml
[project.dependencies]
# CLI・出力
typer = ">=0.15.0"          # CLIフレームワーク
rich = ">=13.0.0"           # 美しいターミナル出力

# データバリデーション
pydantic = ">=2.0.0"        # データモデル、型安全性

# API クライアント
openai = ">=1.0.0"          # OpenAI公式SDK（AsyncOpenAI対応）
google-generativeai = ">=0.8.0"  # Google AI Studio SDK（新統合SDK）
google-cloud-aiplatform = ">=1.70.0"  # Vertex AI SDK（移行期間）

# TOML処理
tomli-w = ">=1.2.0"         # TOML書き込み（tomllib読み込みは標準ライブラリ）

# ユーティリティ
platformdirs = ">=4.0.0"    # クロスプラットフォームディレクトリ
httpx = ">=0.27.0"          # HTTP/2対応クライアント（公式SDK補完）
```

### 開発依存関係（Development）

```toml
[project.optional-dependencies]
dev = [
    # テスト
    "pytest>=8.0.0",
    "pytest-cov>=6.0.0",
    "pytest-asyncio>=0.24.0",

    # リント・フォーマット
    "ruff>=0.8.0",

    # 型チェック
    "mypy>=1.13.0",
]
```

### Python バージョン要件

```toml
[project]
requires-python = ">=3.13"
```

**根拠**:
- Python 3.13: `tomllib`標準ライブラリ化（3.11+）、最新機能、長期サポート
- プロジェクト要件（plan.md Technical Context）: "Python 3.13以上"

---

## 追加調査項目: プロバイダー別モデルリストAPI

### OpenAI Models List API

**エンドポイント**: `GET https://api.openai.com/v1/models`

**認証**: `Authorization: Bearer $OPENAI_API_KEY`

**レスポンス例**:
```json
{
  "data": [
    {
      "id": "gpt-4-turbo",
      "object": "model",
      "created": 1687882411,
      "owned_by": "openai"
    }
  ],
  "object": "list"
}
```

**注意点**:
- 約38モデルが返されるが、すべてが使用可能とは限らない
- 特定エンドポイント（`/v1/chat/completions`等）での利用可能性は別途確認必要
- エラーハンドリング必須（API障害、レート制限）

### Google Gemini Models List API

**エンドポイント**: `GET https://generativelanguage.googleapis.com/v1beta/models?key=${GEMINI_API_KEY}`

**認証**: URLパラメータ（Google AI Studio）またはIAM（Vertex AI）

**レスポンス情報**:
- モデル名、表示名、説明
- トークン制限、サポート機能（`generateContent`等）
- ページネーション対応（デフォルト50件/ページ、最大1000件）

**Python SDK使用例**:
```python
from google import genai

client = genai.Client(api_key=api_key)
for model in client.models.list():
    if "generateContent" in model.supported_actions:
        print(f"{model.name}: {model.description}")
```

### Anthropic Claude Models

**エンドポイント**: なし（2025年10月時点）

**データソース**:
- 公式ドキュメント（https://docs.anthropic.com/en/docs/about-claude/models）
- TOML手動管理（`src/llm_discovery/data/anthropic_models.toml`）

**最新モデル（2025年時点）**:
- claude-sonnet-4-5-20250929 ($3/$15 per million tokens)
- claude-haiku-4-5 ($1/$5 per million tokens)
- claude-opus-4-1 ($15/$75 per million tokens)

---

## 設定ファイル・データファイル構成案

```
src/llm_discovery/
├── data/
│   └── anthropic_models.toml  # 手動管理のAnthropicモデルリスト
├── models/
│   ├── __init__.py
│   ├── base.py               # Pydantic BaseModel定義
│   ├── openai.py             # OpenAI固有モデル
│   ├── google.py             # Google固有モデル
│   └── anthropic.py          # Anthropic固有モデル
├── services/
│   ├── __init__.py
│   ├── openai_client.py      # OpenAI API クライアント
│   ├── google_client.py      # Google API クライアント
│   ├── anthropic_loader.py   # Anthropic TOMLローダー
│   └── cache.py              # キャッシュ管理（platformdirs使用）
├── cli/
│   ├── __init__.py
│   └── main.py               # Typer CLI定義
└── lib/
    ├── __init__.py
    ├── version.py            # バージョン取得（importlib.metadata）
    └── utils.py              # ユーティリティ関数

~/.cache/llm-discovery/       # platformdirsで管理
├── models_cache.toml         # 最新キャッシュ
└── snapshots/                # 変更検知用スナップショット（30日保持）
    ├── 2025-10-19_120000.toml
    └── 2025-10-18_120000.toml
```

---

## テスト戦略詳細

### カバレッジ目標配分

| コンポーネント | 目標カバレッジ | 理由 |
|--------------|-------------|------|
| `models/` | 95-100% | コアデータモデル、Pydanticバリデーション |
| `services/` | 90-95% | API統合、エラーハンドリング重要 |
| `cli/` | 80-90% | ユーザー入力、エッジケース多い |
| `lib/` | 95-100% | ユーティリティ、バージョン取得 |

### テスト種別

1. **Unit Tests** (`tests/unit/`):
   - Pydanticモデルのバリデーション
   - ユーティリティ関数
   - モック使用（APIクライアント）

2. **Integration Tests** (`tests/integration/`):
   - 実際のAPI呼び出し（環境変数で制御）
   - キャッシュ読み書き
   - ファイルシステム操作

3. **Contract Tests** (`tests/contract/`):
   - OpenAI API応答形式
   - Google API応答形式
   - Anthropic TOMLスキーマ

4. **End-to-End Tests**:
   - CLIコマンド実行（`subprocess`）
   - エクスポート形式検証（JSON、CSV、YAML等）

---

## CI/CD パイプライン構成案

```yaml
# .github/workflows/test.yml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.13"]

    steps:
    - uses: actions/checkout@v4

    - name: Install uv
      uses: astral-sh/setup-uv@v5

    - name: Set up Python
      run: uv python install ${{ matrix.python-version }}

    - name: Install dependencies
      run: uv sync --all-extras --all-groups

    - name: Run ruff
      run: uv run ruff check .

    - name: Run mypy
      run: uv run mypy src/

    - name: Run tests with coverage
      run: uv run pytest --cov=llm_discovery --cov-report=xml --cov-fail-under=80

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v4
      with:
        file: ./coverage.xml
        fail_ci_if_error: true
```

---

## パフォーマンス要件の実現方法

### SC-007: 並行取得（最も遅いプロバイダーの応答時間と同等）

**実装戦略**:
```python
import asyncio
from openai import AsyncOpenAI
from google import genai

async def fetch_all_models_concurrently() -> dict:
    """並行取得により、最も遅いプロバイダーの応答時間に収める"""
    tasks = [
        fetch_openai_models(),
        fetch_google_models(),
        load_anthropic_models_async(),  # TOMLロードも非同期化
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # エラーハンドリング（Primary Data Non-Assumption準拠）
    openai_result, google_result, anthropic_result = results
    if isinstance(openai_result, Exception):
        raise RuntimeError(f"OpenAI API failed: {openai_result}") from openai_result
    if isinstance(google_result, Exception):
        raise RuntimeError(f"Google API failed: {google_result}") from google_result
    if isinstance(anthropic_result, Exception):
        raise RuntimeError(f"Anthropic data load failed: {anthropic_result}") from anthropic_result

    return {
        "openai": openai_result,
        "google": google_result,
        "anthropic": anthropic_result,
    }
```

### CHK024: バージョン取得 < 10ms

**実装戦略**:
```python
from importlib.metadata import version
from functools import lru_cache

@lru_cache(maxsize=1)
def get_version_cached() -> str:
    """キャッシュにより、2回目以降はほぼ0ms"""
    try:
        return version("llm-discovery")
    except PackageNotFoundError as e:
        raise RuntimeError("Cannot determine package version") from e

# ベンチマーク
import time
start = time.perf_counter()
v = get_version_cached()
elapsed_ms = (time.perf_counter() - start) * 1000
assert elapsed_ms < 10, f"Version fetch took {elapsed_ms:.2f}ms (> 10ms)"
```

---

## エラーハンドリング戦略（Primary Data Non-Assumption準拠）

### 原則

1. **推測禁止**: デフォルト値で隠蔽しない
2. **明示的エラー**: 失敤時は明確なエラーメッセージ
3. **トレーサビリティ**: 例外チェーン（`raise ... from e`）

### 実装例

```python
import os
from openai import AsyncOpenAI, OpenAIError

async def fetch_openai_models() -> list[dict]:
    """
    Fetch OpenAI models.

    Raises:
        RuntimeError: If API key is missing or API call fails
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY environment variable is not set. "
            "Please set it to your OpenAI API key."
        )

    try:
        client = AsyncOpenAI(api_key=api_key)
        response = await client.models.list()
        return [model.model_dump() for model in response.data]
    except OpenAIError as e:
        raise RuntimeError(
            f"Failed to fetch OpenAI models: {e}. "
            "Check your API key and network connection."
        ) from e

# バージョン取得
from importlib.metadata import version, PackageNotFoundError

def get_version() -> str:
    try:
        return version("llm-discovery")
    except PackageNotFoundError as e:
        # フォールバック禁止（"0.0.0"等を返さない）
        raise RuntimeError(
            "Cannot determine package version. "
            "Ensure llm-discovery is properly installed with 'pip install -e .' or 'uv pip install -e .'"
        ) from e
```

---

## 結論

この技術調査により、LLMモデル発見・追跡システムの実装に必要なすべての技術選択が明確になりました。主要な決定事項:

1. **公式SDK優先**: OpenAI、Googleの公式クライアントライブラリを使用（型安全性、メンテナンス性）
2. **非同期処理**: `asyncio.gather()`による並行取得でパフォーマンス要件達成
3. **TOML統一**: 設定、キャッシュ、AnthropicデータすべてでTOML形式使用（Python 3.11+標準化）
4. **Pydantic v2**: 厳格なデータバリデーション、型安全性保証
5. **Rich出力**: 美しく使いやすいCLI体験
6. **高カバレッジ**: pytest-covで90%目標、80%閾値（品質重視）
7. **静的バージョン**: シンプルで明確な手動管理
8. **クロスプラットフォーム**: platformdirsによるOS間互換性

すべての選択は、憲章（Primary Data Non-Assumption、Test-First、Simplicity等）に準拠しており、Phase 1（データモデル設計）に進む準備が整いました。
