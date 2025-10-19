# Research: Prebuilt Model Data Support

**Phase**: 0 - Outline & Research
**Date**: 2025-10-19
**Status**: Complete

## Overview

この調査フェーズでは、事前生成データ機能の実装に必要な技術選択、ベストプラクティス、設計パターンを評価します。

## Research Areas

### 1. JSON Schema Design for Prebuilt Data

**Decision**: シンプルなJSON構造、メタデータ埋め込み方式を採用

**Rationale**:
- Pydanticモデルとの互換性確保
- 人間が読みやすい形式
- バージョン管理システム（Git）でのdiff確認が容易
- 標準ライブラリのjsonモジュールで処理可能

**Schema Structure**:
```json
{
  "metadata": {
    "generated_at": "2025-10-19T00:00:00Z",
    "generator": "llm-discovery",
    "version": "0.1.0"
  },
  "providers": [
    {
      "provider_name": "openai",
      "fetched_at": "2025-10-19T00:00:00Z",
      "models": [
        {
          "model_id": "gpt-4",
          "model_name": "GPT-4",
          "provider_name": "openai",
          "source": "api",
          "fetched_at": "2025-10-19T00:00:00Z",
          "metadata": {}
        }
      ]
    }
  ]
}
```

**Alternatives Considered**:
- TOML形式: 既存のAnthropicデータで使用しているが、ネストが深い構造には不向き
- YAML形式: 冗長で、標準ライブラリサポートなし（PyYAML依存）
- MessagePack: バイナリ形式でdiff確認が困難

### 2. Data Freshness Calculation Best Practices

**Decision**: ISO 8601形式のUTCタイムスタンプ、経過時間は実行時に計算

**Rationale**:
- ISO 8601はPythonのdatetime.isoformat()と互換性あり
- UTCを使用することでタイムゾーン問題を回避
- 経過時間の事前計算は不要（表示時に計算）
- 標準的で広く採用されている形式

**Implementation**:
```python
from datetime import datetime, UTC

# 生成時
generated_at = datetime.now(UTC).isoformat()

# 読み込み時
generated_time = datetime.fromisoformat(metadata["generated_at"])
age_hours = (datetime.now(UTC) - generated_time).total_seconds() / 3600
```

**Alternatives Considered**:
- UNIXタイムスタンプ: 人間が読めない、デバッグが困難
- ローカルタイムゾーン: タイムゾーン変換の複雑さ、移植性の問題
- 相対時間（"2 hours ago"）: 経過時間の正確な計算が困難

### 3. GitHub Actions Workflow Design

**Decision**: Scheduled workflow with failure notification, artifact preservation

**Rationale**:
- `schedule`トリガーで定期実行（cron式）
- `workflow_dispatch`で手動実行可能
- エラー時はGitHub Issues APIでIssue自動作成
- 最後に成功したデータを保持（失敗時は更新しない）

**Workflow Structure**:
```yaml
on:
  schedule:
    - cron: '0 0 * * *'  # 毎日0:00 UTC
  workflow_dispatch:     # 手動実行

jobs:
  update-data:
    runs-on: ubuntu-latest
    steps:
      - Checkout
      - Install dependencies
      - Fetch models (with API keys from secrets)
      - Generate JSON with metadata
      - Commit and push (if changes detected)
      - Create issue on failure
```

**Alternatives Considered**:
- GitLab CI: プロジェクトがGitHub上にあるため不適
- 外部Cron + WebHook: 複雑性が高く、メンテナンスコスト増
- GitHub Actions Matrix Strategy: データ生成は単一ジョブで十分

### 4. Error Handling Strategy for Missing/Corrupt Data

**Decision**: Explicit error with actionable guidance, no silent fallback

**Rationale**:
- 憲法Article X（Data Accuracy）に準拠
- エラーを隠蔽せず、明示的に表示
- ユーザーに次のアクションを明確に案内
- デバッグとトラブルシューティングが容易

**Error Handling Protocol**:
1. URL不可: HTTPエラー、ネットワークエラー → APIキー設定を促すメッセージ、ネットワーク確認を促す
2. JSONパースエラー: json.JSONDecodeError → データ破損を通知、GitHub Issueへの報告を促す
3. スキーマ検証エラー: pydantic.ValidationError → データ構造の問題を通知
4. タイムアウト: HTTPタイムアウト → リトライまたはAPIキー使用を促す

**Implementation Example**:
```python
import urllib.request
import json

try:
    with urllib.request.urlopen(remote_url, timeout=10) as response:
        data = json.loads(response.read().decode('utf-8'))
    # Validate with pydantic
except urllib.error.HTTPError as e:
    raise PrebuiltDataNotFoundError(
        f"Prebuilt data not accessible (HTTP {e.code}). Please check network or set API keys."
    )
except urllib.error.URLError as e:
    raise PrebuiltDataCorruptedError(
        f"Network error: {e.reason}. Please check your connection."
    )
except json.JSONDecodeError as e:
    raise PrebuiltDataCorruptedError(
        f"Prebuilt data is corrupted: {e}. Please report this issue."
    )
```

**Alternatives Considered**:
- Silent fallback to empty list: エラーを隠蔽し、デバッグが困難
- Default データの埋め込み: データの正確性が保証されない
- 警告のみ表示: ユーザーがエラーを見逃す可能性

### 5. Data Source Transparency Messaging

**Decision**: Rich console library with color-coded messages, timestamp display

**Rationale**:
- 既存のrichライブラリを活用（新規依存なし）
- 色分けで視覚的に区別（事前生成=黄色、API=緑、エラー=赤）
- タイムスタンプと経過時間を常に表示
- 一貫性のあるメッセージフォーマット

**Message Format**:
```python
# 事前生成データ使用時
console.print(
    f"[yellow]ℹ Using prebuilt data (updated: {timestamp}, age: {age_hours:.1f}h)[/yellow]"
)

# API取得時
console.print("[green]✓ Fetching latest data from APIs...[/green]")

# エラー時
console.print("[red]✗ Error: {error_message}[/red]")
```

**Alternatives Considered**:
- プレーンテキスト: 視覚的な区別がなく、見落としやすい
- ログファイルのみ: ユーザーが即座に状態を確認できない
- JSON出力のみ: 人間が読みにくい

### 6. Metadata Script Design

**Decision**: Standalone Python script with clear responsibilities

**Rationale**:
- GitHub Actions内で実行可能
- 入力JSONに非破壊的にメタデータを追加
- テスト可能な設計
- CLIツール本体とは独立

**Script Responsibilities**:
1. 入力JSONの読み込み
2. メタデータセクションの生成（generated_at、version等）
3. 出力JSONへの書き込み
4. エラーハンドリング

**Alternatives Considered**:
- CLIコマンドの拡張: GitHub Actions専用の機能をCLIに含めるのは不適切
- シェルスクリプト + jq: 複雑な処理には不向き、エラーハンドリングが困難

### 7. Integration with Existing Export Functionality

**Decision**: Extend existing exporters to include data source metadata

**Rationale**:
- DRY原則遵守（Article XI）
- 既存のexporter構造を活用
- 新規exporterクラス不要
- メタデータフィールドの統一

**Extension Points**:
- JSON exporter: 既存の出力に`_metadata`フィールド追加
- CSV exporter: `data_source`カラム追加
- Markdown exporter: ヘッダーにデータソース情報追加

**Alternatives Considered**:
- 新規PrebuiltExporterクラス: コード重複、保守性低下
- Export時の条件分岐なし: データソースの透明性が失われる

## Summary

すべての調査項目で明確な技術選択が完了しました。既存の技術スタック（Python 3.13、pydantic、rich）を最大限活用し、新規依存を最小化します。憲法の全原則（特にArticle X: Data Accuracy、Article XI: DRY Principle）を遵守した設計です。

## Next Steps

Phase 1に進み、以下を作成します:
- data-model.md: PrebuiltModelDataとDataSourceIndicatorのエンティティ定義
- contracts/: PrebuiltDataLoaderのコントラクト定義
- quickstart.md: ユーザー向けクイックスタートガイド
