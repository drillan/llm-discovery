# Versioning Contract

**Feature**: [spec.md](../spec.md)
**Data Model**: [data-model.md](../data-model.md)

## Purpose

このドキュメントは、`llm-discovery`のセマンティックバージョニングポリシーを定義します。パッケージバージョン、CLI契約、Python API契約、データフォーマットバージョンの管理方針を規定し、ユーザーへの後方互換性保証を明確化します。

## Specification

### Semantic Versioning Policy

**形式**: `MAJOR.MINOR.PATCH`

llm-discoveryは[Semantic Versioning 2.0.0](https://semver.org/)に準拠します。

**バージョン番号の意味**:

- **MAJOR**: 後方互換性のない変更
- **MINOR**: 後方互換性のある機能追加
- **PATCH**: 後方互換性のあるバグ修正

### Version Management Strategy

**Single Source of Truth**: `pyproject.toml`

すべてのバージョン情報は`pyproject.toml`で静的に管理され、以下の方法で取得されます:

```toml
[project]
name = "llm-discovery"
version = "0.1.0"  # 手動更新（静的バージョン）
```

**取得方法**:
- CLI: `llm-discovery --version`（importlib.metadataで取得）
- Python API: `llm_discovery.__version__`（importlib.metadataで取得）

**ハードコーディング禁止**: Primary Data Non-Assumption Principle準拠

### Version Increment Criteria

#### MAJOR Version (X.0.0)

**変更内容**: 後方互換性のない破壊的変更

**CLI契約への影響**:
- コマンド名の変更または削除
- 必須オプションの追加
- 出力形式の破壊的変更
- 終了コードの意味変更

**Python API契約への影響**:
- クラス名・メソッド名の変更または削除
- メソッドシグネチャの変更（引数の削除、型変更）
- 例外階層の破壊的変更
- 戻り値の型変更

**データフォーマット契約への影響**:
- JSONスキーマの必須フィールド削除
- CSVカラムの削除または順序変更
- エクスポート形式の廃止

**例**:
- `0.9.0` → `1.0.0`: 安定版リリース（初回MAJOR）
- `1.5.0` → `2.0.0`: `DiscoveryClient.fetch_models()`が同期APIに変更
- `2.3.0` → `3.0.0`: `list`コマンドの出力形式が変更

#### MINOR Version (x.Y.0)

**変更内容**: 後方互換性のある機能追加

**CLI契約への影響**:
- 新しいコマンドの追加
- オプショナルなオプションの追加
- 新しいエクスポート形式の追加

**Python API契約への影響**:
- 新しいクラス・メソッドの追加
- デフォルト引数の追加
- 新しい例外クラスの追加（既存の例外階層を維持）

**データフォーマット契約への影響**:
- JSONスキーマへの任意フィールド追加
- CSVへの新しいカラム追加（末尾のみ）

**例**:
- `0.1.0` → `0.2.0`: YAML形式のエクスポート追加
- `1.0.0` → `1.1.0`: Vertex AI対応追加
- `1.2.0` → `1.3.0`: `DiscoveryClient.export_to_file()`メソッド追加

#### PATCH Version (x.y.Z)

**変更内容**: 後方互換性のあるバグ修正、パフォーマンス改善

**対象**:
- バグ修正
- パフォーマンス最適化
- ドキュメント修正
- 内部実装の改善（外部契約に影響なし）

**例**:
- `0.1.0` → `0.1.1`: キャッシュファイルのパース失敗を修正
- `1.0.0` → `1.0.1`: API呼び出しのタイムアウト値を最適化
- `1.2.3` → `1.2.4`: エラーメッセージの誤字を修正

### Data Format Versioning

**独立管理**: データフォーマットバージョンはパッケージバージョンとは別管理

キャッシュファイル（`models_cache.toml`）は独自のバージョン管理を持ちます:

```toml
[metadata]
version = "1.0"  # データフォーマットバージョン
package_version = "0.1.0"  # パッケージバージョン
```

**データフォーマットバージョンのインクリメント基準**:

- **Major（X.0）**: キャッシュファイルの構造変更（後方互換性なし）
- **Minor（x.Y）**: 新しいフィールド追加（後方互換性あり）

**後方互換性保証**:
- パッケージバージョン`1.x.x`は、データフォーマットバージョン`1.0`〜`1.Y`のキャッシュファイルを読み込める
- データフォーマットバージョン`2.0`への移行は、パッケージのMAJORバージョンアップ（`2.0.0`）と同時に行う

### CLI Backward Compatibility

**後方互換性保証（MINOR以下）**:

MINOR・PATCHバージョンでは、以下を保証します:

1. **既存コマンドの動作維持**:
   - `llm-discovery list`は同じ出力形式を保持
   - `llm-discovery export --format json`は同じJSONスキーマを出力

2. **オプションの互換性**:
   - 既存のオプションは削除されない
   - オプションのデフォルト値は変更されない
   - 新しいオプションはすべてオプショナル

3. **終了コードの一貫性**:
   - 0: 成功（変更なし）
   - 1: 一般エラー（変更なし）
   - 2: コマンドライン引数エラー（変更なし）

**非推奨化プロセス（Deprecation）**:

機能を削除する場合、少なくとも1つのMINORバージョンで非推奨警告を表示:

```bash
# v1.5.0で非推奨警告
$ llm-discovery old-command
Warning: 'old-command' is deprecated and will be removed in v2.0.0.
Please use 'new-command' instead.

# v2.0.0で削除
$ llm-discovery old-command
Error: 'old-command' has been removed. Please use 'new-command'.
```

### Python API Backward Compatibility

**後方互換性保証（MINOR以下）**:

MINOR・PATCHバージョンでは、以下を保証します:

1. **クラス・メソッドの維持**:
   - `DiscoveryClient`クラスは削除されない
   - `fetch_models()`メソッドは削除されない

2. **メソッドシグネチャの互換性**:
   - 既存の引数は削除されない
   - 新しい引数はデフォルト値を持つ

3. **戻り値の型一貫性**:
   - `fetch_models() -> list[Model]`の戻り値型は変更されない

4. **例外階層の維持**:
   - 既存の例外クラスは削除されない
   - 新しい例外は既存の階層に追加

**非推奨化プロセス（Deprecation）**:

```python
import warnings

class DiscoveryClient:
    def old_method(self):
        warnings.warn(
            "old_method() is deprecated and will be removed in v2.0.0. "
            "Use new_method() instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return self.new_method()
```

### Release Process

**手動リリースプロセス**:

1. **バージョン更新**:
   - `pyproject.toml`の`version`フィールドを手動で更新

   ```toml
   [project]
   version = "0.2.0"  # 0.1.0 → 0.2.0
   ```

2. **変更ログ更新**:
   - `CHANGELOG.md`に変更内容を記録

3. **コミット**:
   ```bash
   git add pyproject.toml CHANGELOG.md
   git commit -m "Release v0.2.0"
   ```

4. **Gitタグ作成**:
   ```bash
   git tag v0.2.0
   git push origin v0.2.0
   ```

5. **PyPIリリース**:
   ```bash
   uv build
   uv publish
   ```

**リリース順序**: バージョン更新 → コミット → タグ → リリース

### Version Compatibility Matrix

| Package Version | Data Format Version | CLI Contract Version | Python API Version | Python Version |
|-----------------|---------------------|----------------------|--------------------|----------------|
| 0.1.0           | 1.0                 | 1.0.0                | 1.0.0              | 3.13+          |
| 0.2.0           | 1.0                 | 1.1.0                | 1.1.0              | 3.13+          |
| 1.0.0           | 1.0                 | 1.2.0                | 1.2.0              | 3.13+          |
| 1.1.0           | 1.1                 | 1.3.0                | 1.3.0              | 3.13+          |
| 2.0.0           | 2.0                 | 2.0.0                | 2.0.0              | 3.13+          |

**注意**: パッケージバージョンとCLI/Python API契約バージョンは独立して管理されますが、通常は同期します。

## Examples

### Example 1: バージョン確認

```bash
# CLI経由
$ llm-discovery --version
llm-discovery, version 0.1.0

# Python API経由
$ python -c "from llm_discovery import __version__; print(__version__)"
0.1.0
```

### Example 2: 互換性のある機能追加（MINOR）

```python
# v0.1.0
class DiscoveryClient:
    async def fetch_models(self) -> list[Model]:
        ...

# v0.2.0（後方互換性あり）
class DiscoveryClient:
    async def fetch_models(self) -> list[Model]:
        ...

    # 新メソッド追加
    async def fetch_models_by_provider(self, provider: str) -> list[Model]:
        ...
```

### Example 3: 非推奨化とMAJOR変更

```python
# v1.5.0（非推奨警告）
class DiscoveryClient:
    def old_sync_fetch(self) -> list[Model]:
        warnings.warn(
            "old_sync_fetch() is deprecated. Use async fetch_models() instead.",
            DeprecationWarning
        )
        ...

# v2.0.0（削除）
class DiscoveryClient:
    # old_sync_fetch()は削除
    async def fetch_models(self) -> list[Model]:
        ...
```

### Example 4: データフォーマットバージョン移行

```toml
# v0.1.0のキャッシュ（format version 1.0）
[metadata]
version = "1.0"
package_version = "0.1.0"

# v1.0.0のキャッシュ（format version 1.1、後方互換性あり）
[metadata]
version = "1.1"
package_version = "1.0.0"
new_field = "value"  # 新フィールド追加

# v2.0.0のキャッシュ（format version 2.0、破壊的変更）
[metadata]
format_version = "2.0"  # キー名変更
package_version = "2.0.0"
```

## Test Requirements

### Version Consistency Tests

- `tests/unit/version/test_version_consistency.py`:
  - `pyproject.toml`のバージョンと`__version__`の一致確認
  - CLI `--version`とPython API `__version__`の一致確認

### Backward Compatibility Tests

- `tests/contract/test_backward_compatibility.py`:
  - 旧バージョンのキャッシュファイル読み込み可能性
  - 非推奨警告の表示確認
  - 既存APIの動作維持確認

### Deprecation Tests

- `tests/unit/version/test_deprecation_warnings.py`:
  - DeprecationWarningが正しく発生
  - 警告メッセージに移行方法が含まれる

## References

- **Semantic Versioning 2.0.0**: https://semver.org/
- **PEP 440**: Python version identification and dependency specification
- **spec.md Clarifications**: バージョン管理方針（静的バージョン、手動更新）
- **FR-022**: `--version`フラグ
- **FR-023**: `__version__`属性
