# Research: `update`コマンド実装調査

**作成日**: 2025-10-19
**関連仕様**: [spec.md](./spec.md) (FR-024, FR-025, FR-026)
**実装計画**: [plan.md](./plan.md)

## 1. 既存`list`コマンド分析

### Current Implementation

既存の`list.py`（203行）は、以下の責任を持つ：

1. **キャッシュ読み込み試行** (行44-51)
   - `DiscoveryService.get_cached_models()`でキャッシュ読み込み
   - 成功時はキャッシュパスを表示し、`providers`と`models`を設定

2. **キャッシュ不在時のAPI取得** (行52-103)
   - `CacheNotFoundError`または`CacheCorruptedError`をキャッチ
   - 破損時は警告メッセージを表示（"Cache file is corrupted. Fetching fresh data..."）
   - `asyncio.run(service.fetch_all_models())`でAPI取得
   - `service.save_to_cache(providers)`でキャッシュ保存
   - エラーハンドリング:
     - `PartialFetchError`: 終了コード1、明確なエラーメッセージ
     - `ProviderFetchError`: 終了コード1、提案アクション付きエラーメッセージ
     - `AuthenticationError`: 終了コード2、認証エラーメッセージ

3. **変更検知機能** (行105-186, `--detect-changes`オプション)
   - スナップショット一覧取得
   - 初回実行時: 現在の状態をベースラインとして保存
   - 2回目以降: 前回スナップショットと比較、変更を検出
   - 変更があればconsoleに表示、changes.jsonとCHANGELOG.mdに保存
   - 30日以上古いスナップショットを自動削除

4. **結果表示** (行188-195)
   - 変更検知モードでない場合のみ`create_models_table()`で表形式表示
   - 総モデル数を表示

### Code to Move to `update` Command

以下のコードブロックを新規`update.py`に移動:

**1. API取得ロジック** (list.py 行58-103)
```python
# Fetch from APIs
try:
    providers = asyncio.run(service.fetch_all_models())

    # Save to cache
    service.save_to_cache(providers)
    console.print(
        f"[dim]Cached to: {config.llm_discovery_cache_dir / 'models_cache.toml'}[/dim]"
    )

    # Extract all models
    models = []
    for provider in providers:
        models.extend(provider.models)

except PartialFetchError as e:
    display_error(
        "Partial failure during model fetch.",
        f"Successful providers: {', '.join(e.successful_providers)}\n"
        f"Failed providers: {', '.join(e.failed_providers)}\n\n"
        "To ensure data consistency, processing has been aborted.\n"
        "Please resolve the issue with the failed provider and retry.",
    )
    raise typer.Exit(1)

except ProviderFetchError as e:
    display_error(
        f"Failed to fetch models from {e.provider_name} API.",
        f"Cause: {e.cause}\n\n"
        "Suggested actions:\n"
        "  1. Check your internet connection\n"
        "  2. Verify API keys are set correctly\n"
        "  3. Check provider status pages\n"
        "  4. Retry the command later",
    )
    raise typer.Exit(1)

except AuthenticationError as e:
    display_error(
        f"Authentication failed for {e.provider_name}.",
        f"Details: {e.details}\n\n"
        "Please check your API keys and credentials.",
    )
    raise typer.Exit(2)
```

**2. 変更検知ロジック全体** (list.py 行105-186)
```python
# Handle change detection
if detect_changes:
    # Get list of snapshots
    snapshots = service.snapshot_service.list_snapshots()

    if len(snapshots) < 1:
        # No previous snapshot - save current as baseline
        snapshot_id = service.snapshot_service.save_snapshot(providers)
        console.print(
            "[yellow]No previous snapshot found. Saving current state as baseline.[/yellow]"
        )
        console.print(
            "Next run with --detect-changes will detect changes from this baseline.\n"
        )
        console.print(f"[dim]Snapshot ID: {snapshot_id}[/dim]")
    else:
        # Load previous snapshot and detect changes
        previous_snapshot_id, _ = snapshots[0]
        previous_snapshot = service.snapshot_service.load_snapshot(previous_snapshot_id)

        # Create current snapshot
        from llm_discovery.models import Snapshot
        current_snapshot = Snapshot(providers=providers)

        # Detect changes
        changes = service.change_detector.detect_changes(
            previous_snapshot, current_snapshot
        )

        if changes:
            console.print("[bold green]Changes detected![/bold green]\n")

            # Group changes by type
            added = [c for c in changes if c.change_type == ChangeType.ADDED]
            removed = [c for c in changes if c.change_type == ChangeType.REMOVED]

            if added:
                console.print(f"[green]Added models ({len(added)}):[/green]")
                for change in added:
                    console.print(f"  {change.provider_name}/{change.model_id}")

            if removed:
                console.print(f"\n[red]Removed models ({len(removed)}):[/red]")
                for change in removed:
                    console.print(f"  {change.provider_name}/{change.model_id}")

            # Save changes.json
            changes_file = config.llm_discovery_cache_dir / "changes.json"
            changes_data = {
                "previous_snapshot_id": str(previous_snapshot.snapshot_id),
                "current_snapshot_id": str(current_snapshot.snapshot_id),
                "detected_at": datetime.now(UTC).isoformat(),
                "changes": [
                    {
                        "type": c.change_type.value,
                        "model_id": c.model_id,
                        "model_name": c.model_name,
                        "provider_name": c.provider_name,
                    }
                    for c in changes
                ],
            }
            changes_file.write_text(json.dumps(changes_data, indent=2), encoding="utf-8")

            # Update CHANGELOG.md
            changelog_file = config.llm_discovery_cache_dir / "CHANGELOG.md"
            changelog_gen = ChangelogGenerator(changelog_file)
            changelog_gen.append_to_changelog(changes, datetime.now(UTC))

            console.print("\n[dim]Details saved to:[/dim]")
            console.print(f"[dim]  - {changes_file}[/dim]")
            console.print(f"[dim]  - {changelog_file}[/dim]")

            # Save new snapshot
            service.snapshot_service.save_snapshot(providers)
        else:
            console.print("[dim]No changes detected.[/dim]")

        # Cleanup old snapshots
        deleted = service.snapshot_service.cleanup_old_snapshots()
        if deleted > 0:
            console.print(f"\n[dim]Cleaned up {deleted} old snapshot(s)[/dim]")
```

**3. キャッシュ破損時のリカバリロジック** (list.py 行53-57)
```python
if isinstance(e, CacheCorruptedError):
    console.print(
        "[yellow]Warning: Cache file is corrupted. Fetching fresh data from APIs...[/yellow]"
    )
else:
    console.print("[dim]Fetching models from APIs...[/dim]")
```

### Code to Keep in `list` Command

以下のコードブロックを`list.py`に残す（大幅に簡素化）：

**1. キャッシュ読み込みのみ** (簡素化版)
```python
try:
    # Load configuration
    config = Config.from_env()
    service = DiscoveryService(config)

    # Load from cache
    console.print("[dim]Loading from cache...[/dim]")
    models = service.get_cached_models()
    console.print(
        f"[dim](Loaded from cache: {config.llm_discovery_cache_dir / 'models_cache.toml'})[/dim]"
    )

except CacheNotFoundError:
    display_error(
        "No cached data available. Please run 'llm-discovery update' first to fetch model data."
    )
    raise typer.Exit(1)

except CacheCorruptedError as e:
    display_error(
        "Cache file is corrupted.",
        f"Cache path: {e.cache_path}\n"
        f"Error: {e.parse_error}\n\n"
        "Please run 'llm-discovery update' to re-fetch and rebuild the cache.",
    )
    raise typer.Exit(1)
```

**2. 結果表示** (変更検知モード条件を削除)
```python
# Display results
if models:
    table = create_models_table(models)
    console.print(table)
    console.print(f"\n[bold]Total models: {len(models)}[/bold]")
else:
    console.print("[yellow]No models found.[/yellow]")
```

### Migration Strategy

**Step 1: 新規ファイル作成**
- `/home/driller/repo/llm-discovery/llm_discovery/cli/commands/update.py`を作成
- 上記「Code to Move to `update` Command」のロジックを実装
- `detect_changes`オプションを追加（typer.Option）

**Step 2: 既存ファイル変更**
- `list.py`を簡素化（上記「Code to Keep in `list` Command」のみ残す）
- `--detect-changes`オプションを削除
- API取得関連のimport文を削除（`asyncio`、`json`、`datetime`等）

**Step 3: main.pyにupdateコマンド登録**
- `llm_discovery/cli/main.py`に`update_command`をインポート
- `app.command("update")(update_command)`で登録

**Step 4: 出力形式の調整**
- `update`コマンド: プロバイダー別モデル数、総数、キャッシュパスを表示
- `update --detect-changes`: 変更内容 + プロバイダー別モデル数、総数、キャッシュパス
- `list`コマンド: 表形式でモデル一覧のみ表示

**Step 5: テスト移行**
- 既存の`test_cli.py`の`TestCLIList`クラスを更新
- 新規`TestCLIUpdate`クラスを追加
- API取得関連のテストを`TestCLIUpdate`に移動
- キャッシュ読み込み専用テストを`TestCLIList`に残す

## 2. エラーメッセージ設計

### Error Message Templates

**EM-001: キャッシュ不在エラー（`list`コマンド）**
```
Error: No cached data available. Please run 'llm-discovery update' first to fetch model data.
```
- 終了コード: 1
- 使用箇所: `list`コマンドでキャッシュが存在しない場合
- 根拠: FR-025要件、明確なアクションを提示

**EM-002: キャッシュ破損エラー（`list`コマンド）**
```
Error: Cache file is corrupted.

Cache path: {cache_path}
Error: {parse_error}

Please run 'llm-discovery update' to re-fetch and rebuild the cache.
```
- 終了コード: 1
- 使用箇所: `list`コマンドでキャッシュが破損している場合
- 根拠: FR-019要件、エラー詳細と復旧手順を提示

**EM-003: キャッシュ破損警告（`update`コマンド）**
```
Warning: Cache file is corrupted. Fetching fresh data from APIs...
```
- 終了コード: N/A（警告のみ、処理継続）
- 使用箇所: `update`コマンドでキャッシュが破損しているが再取得可能な場合
- 根拠: FR-019要件、自動リカバリ動作をユーザーに通知

**EM-004: 部分的取得失敗エラー（`update`コマンド）**
```
Error: Partial failure during model fetch.

Successful providers: {successful_providers}
Failed providers: {failed_providers}

To ensure data consistency, processing has been aborted.
Please resolve the issue with the failed provider and retry.
```
- 終了コード: 1
- 使用箇所: 一部のプロバイダーでAPI取得が失敗した場合
- 根拠: FR-018要件、部分成功での継続禁止、明確な状況説明

**EM-005: プロバイダー取得失敗エラー（`update`コマンド）**
```
Error: Failed to fetch models from {provider_name} API.

Cause: {cause}

Suggested actions:
  1. Check your internet connection
  2. Verify API keys are set correctly
  3. Check provider status pages
  4. Retry the command later
```
- 終了コード: 1
- 使用箇所: 特定のプロバイダーでAPI取得が失敗した場合
- 根拠: FR-017要件、具体的なトラブルシューティング手順を提示

**EM-006: 認証失敗エラー（`update`コマンド）**
```
Error: Authentication failed for {provider_name}.

Details: {details}

Please check your API keys and credentials.
```
- 終了コード: 2
- 使用箇所: API認証に失敗した場合
- 根拠: FR-017要件、認証専用の終了コード（外部スクリプトで区別可能）

**EM-007: 一般的なエラー（両コマンド）**
```
Error: {error_message}
```
- 終了コード: 1
- 使用箇所: ValueErrorや予期しない例外
- 根拠: 一般的なエラーハンドリング

### Exit Code Strategy

**終了コード体系**:
- `0`: 成功（正常終了）
- `1`: 一般的なエラー（キャッシュ不在、API障害、部分失敗、その他）
- `2`: 認証エラー（API認証失敗、GCP認証情報不正等）

**根拠**:
- 業界標準のUNIX終了コード規約に準拠
- CI/CDスクリプトで認証エラーを区別可能（exit code 2をトリガーに認証情報の再設定をフロー化）
- シンプルな3段階（成功・一般エラー・認証エラー）で理解しやすい

## 3. 出力フォーマット設計

### `update` Command Output (Normal)

**通常成功時（変更検知なし）**:
```
Fetching models from APIs...
Cached to: /home/user/.cache/llm-discovery/models_cache.toml

OpenAI: 15, Google: 20, Anthropic: 7
Total: 42 models
```

**実装詳細**:
- 行1: API取得中のメッセージ（`[dim]...[/dim]`スタイル）
- 行2: キャッシュパス（`[dim]...[/dim]`スタイル、トラブルシューティング用）
- 行3: 空行（視認性向上）
- 行4: プロバイダー別モデル数（カンマ区切り）
- 行5: 総数（`[bold]...[/bold]`スタイル）

**コード例**:
```python
console.print("[dim]Fetching models from APIs...[/dim]")
# API取得・キャッシュ保存処理
console.print(f"[dim]Cached to: {config.llm_discovery_cache_dir / 'models_cache.toml'}[/dim]")
console.print()  # 空行

# プロバイダー別カウント
provider_counts = {}
for provider in providers:
    provider_counts[provider.provider_name.capitalize()] = len(provider.models)

# プロバイダー別表示
counts_str = ", ".join([f"{name}: {count}" for name, count in provider_counts.items()])
console.print(counts_str)

# 総数表示
total_models = sum(len(p.models) for p in providers)
console.print(f"[bold]Total: {total_models} models[/bold]")
```

### `update --detect-changes` Output

**変更検出時**:
```
Fetching models from APIs...
Cached to: /home/user/.cache/llm-discovery/models_cache.toml

Changes detected!

Added models (3):
  openai/gpt-4.5
  google/gemini-2.0-pro
  anthropic/claude-3.5-opus

Removed models (1):
  openai/gpt-3.5-turbo-0301

Details saved to:
  - /home/user/.cache/llm-discovery/changes.json
  - /home/user/.cache/llm-discovery/CHANGELOG.md

OpenAI: 15, Google: 21, Anthropic: 8
Total: 44 models

Cleaned up 2 old snapshot(s)
```

**変更なし時**:
```
Fetching models from APIs...
Cached to: /home/user/.cache/llm-discovery/models_cache.toml

No changes detected.

OpenAI: 15, Google: 20, Anthropic: 7
Total: 42 models
```

**初回実行時（ベースライン保存）**:
```
Fetching models from APIs...
Cached to: /home/user/.cache/llm-discovery/models_cache.toml

No previous snapshot found. Saving current state as baseline.
Next run with --detect-changes will detect changes from this baseline.

Snapshot ID: 20251019_143022_abc123

OpenAI: 15, Google: 20, Anthropic: 7
Total: 42 models
```

**実装詳細**:
- 既存の変更検知ロジックを維持
- 最後にプロバイダー別モデル数と総数を追加表示
- richライブラリの`[green]`、`[red]`、`[bold green]`スタイルを活用

### `list` Command Output (Read-only)

**通常表示**:
```
Loading from cache...
(Loaded from cache: /home/user/.cache/llm-discovery/models_cache.toml)

┌─────────────┬──────────────────────┬─────────────────────┬────────┬──────────────────┐
│ Provider    │ Model ID             │ Model Name          │ Source │ Fetched At       │
├─────────────┼──────────────────────┼─────────────────────┼────────┼──────────────────┤
│ openai      │ gpt-4                │ GPT-4               │ api    │ 2025-10-19 14:30 │
│ openai      │ gpt-3.5-turbo        │ GPT-3.5 Turbo       │ api    │ 2025-10-19 14:30 │
│ google      │ gemini-pro           │ Gemini Pro          │ api    │ 2025-10-19 14:30 │
│ anthropic   │ claude-3-opus-20240229│ Claude 3 Opus       │ manual │ 2025-10-19 14:30 │
...
└─────────────┴──────────────────────┴─────────────────────┴────────┴──────────────────┘

Total models: 42
```

**実装詳細**:
- 既存の`create_models_table()`を使用
- `--detect-changes`オプション削除により表示ロジックがシンプル化
- キャッシュパス表示を維持（トラブルシューティング用）

## 4. テスト戦略

### Test Coverage Plan

**カバレッジ目標**: 90%以上維持

**カバレッジ確保方法**:
1. **統合テストによるCLI層カバレッジ確保**
   - `pytest.ini`で`llm_discovery/cli/`をomitしている場合、統合テストでカバー
   - `CliRunner`を使用したend-to-endテストで実際のコマンド実行パスを検証

2. **モックを最小限に抑えた実践的テスト**
   - `DiscoveryService`、`CacheService`、`SnapshotService`は実際のインスタンスを使用
   - 外部API呼び出しのみをモック（`monkeypatch`または`pytest-mock`）

3. **エラーパスの網羅的テスト**
   - 各例外タイプ（`CacheNotFoundError`、`PartialFetchError`等）を意図的に発生させる
   - 終了コードと出力メッセージを検証

4. **境界値・エッジケースの明示的テスト**
   - キャッシュ不在、キャッシュ破損、空のキャッシュ、プロバイダー0件等

### Test Cases for `update` Command

**TC-U-001: 基本的なキャッシュ更新（成功）**
- Given: 環境変数設定済み、API正常
- When: `llm-discovery update` 実行
- Then: 終了コード0、プロバイダー別モデル数と総数が表示される
- Verify: キャッシュファイルが作成され、正しいTOML形式で保存される

**TC-U-002: キャッシュ破損からの自動リカバリ**
- Given: 既存のキャッシュが破損している
- When: `llm-discovery update` 実行
- Then: 警告メッセージ表示、API再取得、キャッシュ再構築、終了コード0

**TC-U-003: 部分的取得失敗（フェイルファスト）**
- Given: OpenAI成功、Google失敗
- When: `llm-discovery update` 実行
- Then: 終了コード1、EM-004エラーメッセージ表示、キャッシュ更新なし

**TC-U-004: 全プロバイダー取得失敗**
- Given: すべてのプロバイダーでAPI障害
- When: `llm-discovery update` 実行
- Then: 終了コード1、EM-005エラーメッセージ表示

**TC-U-005: 認証エラー**
- Given: OpenAIのAPIキーが不正
- When: `llm-discovery update` 実行
- Then: 終了コード2、EM-006エラーメッセージ表示

**TC-U-006: 変更検知（初回実行・ベースライン保存）**
- Given: スナップショット未作成
- When: `llm-discovery update --detect-changes` 実行
- Then: 終了コード0、ベースライン保存メッセージ表示、スナップショットID表示

**TC-U-007: 変更検知（変更あり）**
- Given: 前回スナップショット存在、新モデル追加
- When: `llm-discovery update --detect-changes` 実行
- Then: 終了コード0、変更検出メッセージ表示、changes.json/CHANGELOG.md生成

**TC-U-008: 変更検知（変更なし）**
- Given: 前回スナップショット存在、モデル変更なし
- When: `llm-discovery update --detect-changes` 実行
- Then: 終了コード0、"No changes detected."メッセージ表示

**TC-U-009: スナップショット自動削除**
- Given: 30日以上前のスナップショット存在
- When: `llm-discovery update --detect-changes` 実行
- Then: 古いスナップショット削除、削除数がメッセージ表示

**TC-U-010: 空のプロバイダー（Anthropic手動データ不在等の想定外ケース）**
- Given: プロバイダーがモデル0件を返す
- When: `llm-discovery update` 実行
- Then: 終了コード0、該当プロバイダーのカウントが0

### Test Cases for `list` Command (Modified)

**TC-L-001: 基本的なキャッシュ表示（成功）**
- Given: キャッシュ存在
- When: `llm-discovery list` 実行
- Then: 終了コード0、表形式でモデル一覧表示、総数表示

**TC-L-002: キャッシュ不在エラー**
- Given: キャッシュ未作成
- When: `llm-discovery list` 実行
- Then: 終了コード1、EM-001エラーメッセージ表示

**TC-L-003: キャッシュ破損エラー**
- Given: キャッシュが破損
- When: `llm-discovery list` 実行
- Then: 終了コード1、EM-002エラーメッセージ表示（キャッシュパスとエラー詳細を含む）

**TC-L-004: 空のキャッシュ（モデル0件）**
- Given: キャッシュ存在、モデルデータ0件
- When: `llm-discovery list` 実行
- Then: 終了コード0、"No models found."メッセージ表示

**TC-L-005: 大量モデル表示（パフォーマンステスト）**
- Given: キャッシュに100件以上のモデル
- When: `llm-discovery list` 実行
- Then: 終了コード0、1秒未満で表示完了

### Edge Cases

**EC-001: API取得中のネットワーク切断**
- `update`コマンドが`ProviderFetchError`をraiseし、終了コード1で終了
- エラーメッセージ内で「Check your internet connection」を提示

**EC-002: キャッシュディレクトリの書き込み権限なし**
- キャッシュ保存時に`PermissionError`発生
- 一般的なエラーハンドリング（EM-007）で終了コード1

**EC-003: 複数プロバイダーのうち一部が認証エラー**
- `PartialFetchError`としてハンドリング（認証エラーもフェイルファストの対象）
- 終了コード1（認証専用の終了コード2ではない、部分失敗として扱う）

**EC-004: changes.json/CHANGELOG.mdの書き込み失敗**
- ファイル書き込み失敗時は一般エラー（終了コード1）
- トラブルシューティング用のメッセージで書き込み失敗を通知

**EC-005: スナップショット削除中のエラー**
- 削除失敗は警告のみ、処理継続（非致命的エラー）
- 削除数カウントに失敗分を含めない

**EC-006: プロバイダー名の大文字小文字不一致**
- プロバイダー名は既存コードで小文字に統一されている（`provider_name="openai"`等）
- 出力時は`capitalize()`で表示形式を統一（"OpenAI"、"Google"、"Anthropic"）

## Decisions Summary

### Decision 1: 責任の完全分離（Read/Write明確化）

- **Chosen**: `update`コマンド=Write専用、`list`コマンド=Read専用に完全分離
- **Rationale**:
  - 業界標準（apt update/apt list、brew update/brew list、npm update/npm list）との一貫性
  - Single Responsibility Principle（単一責任の原則）の徹底
  - テストの容易さ向上（各コマンドが独立したテストケースで検証可能）
  - ユーザーの理解しやすさ（コマンド名から動作が明確）
- **Alternatives Considered**:
  - (A) `list --refresh`オプション追加: 責任が不明瞭、オプションの増加による複雑化
  - (B) `list`コマンドでキャッシュなし時に自動取得: 責任の分離が不徹底、予期しないAPI呼び出し

### Decision 2: 破壊的変更の採用（V2クラス作成を回避）

- **Chosen**: 既存`list`コマンドから`--detect-changes`オプションと自動API取得機能を削除
- **Rationale**:
  - Article XII（Destructive Refactoring）準拠
  - `ListCommandV2`のような並行実装を避け、コードベースをシンプルに保つ
  - 移行パスを明確にし、ユーザーにエラーメッセージで新コマンドを案内
- **Alternatives Considered**:
  - (A) `list_v2.py`を作成し、既存の`list.py`を維持: コード重複、保守コスト増加
  - (B) `list`コマンドに後方互換性を持たせる（Deprecation Warning）: 責任分離が不徹底

### Decision 3: 出力形式の設計（サマリー重視）

- **Chosen**: `update`コマンドはプロバイダー別モデル数、総数、キャッシュパスのみ表示（表形式なし）
- **Rationale**:
  - FR-024/FR-026要件に準拠（「サマリーのみ表示」）
  - 責任の分離を徹底（詳細表示は`list`コマンドの責任）
  - CI/CDログでの視認性向上（簡潔な出力）
- **Alternatives Considered**:
  - (A) `update`コマンドでも表形式を表示: 責任の重複、出力の冗長性
  - (B) `update`コマンドで総数のみ表示: プロバイダー別の状況が不明瞭

### Decision 4: エラーハンドリングの厳格性（フェイルファスト原則）

- **Chosen**: 部分失敗時も処理を終了し、キャッシュ更新しない（FR-018準拠）
- **Rationale**:
  - データ整合性の保証（全プロバイダーのデータが揃っていることを保証）
  - 明確なエラー状態の通知（ユーザーが問題を即座に認識可能）
  - 外部リトライメカニズム（cron、CI/CD）での対処を促す
- **Alternatives Considered**:
  - (A) 部分成功で継続し、成功したプロバイダーのみキャッシュ: データ不整合、予期しない動作
  - (B) 自動リトライ機能の実装: 複雑性の増加、外部メカニズムとの重複

### Decision 5: 終了コード体系（3段階方式）

- **Chosen**: 0=成功、1=一般エラー、2=認証エラー
- **Rationale**:
  - UNIX標準に準拠したシンプルな体系
  - CI/CDスクリプトでの認証エラー検出が容易
  - 将来の拡張性（必要に応じて終了コード追加可能）
- **Alternatives Considered**:
  - (A) 詳細な終了コード体系（3=キャッシュエラー、4=ネットワークエラー等）: 過剰な複雑化
  - (B) 0と1のみ: 認証エラーの区別が不可能

### Decision 6: テスト戦略（統合テスト重視）

- **Chosen**: `CliRunner`を使用したend-to-end統合テストを中心に、モックを最小限に抑える
- **Rationale**:
  - 実際のユーザー操作フローに近いテスト
  - リファクタリング時の安全性向上
  - Article IV（Integration-First）準拠
- **Alternatives Considered**:
  - (A) 各関数の単体テストを細かく作成: 過剰なモック、保守コスト増加
  - (B) 手動テストのみ: 自動化の欠如、リグレッションリスク

### Decision 7: キャッシュ破損時の動作差異（`update`と`list`）

- **Chosen**: `update`は自動リカバリ（警告後に再取得）、`list`はエラー表示して終了
- **Rationale**:
  - `update`はWrite操作の責任を持つため、自動修復が適切
  - `list`はRead専用であり、データ修復の責任を持たない
  - ユーザーに明確なアクション（`update`実行）を促す
- **Alternatives Considered**:
  - (A) 両方とも自動リカバリ: `list`コマンドがAPI呼び出しを行い、責任分離に反する
  - (B) 両方ともエラーで終了: `update`コマンドの利便性低下

### Decision 8: プログレス表示の省略

- **Chosen**: API取得中のプログレス表示なし（完了後にサマリーのみ）
- **Rationale**:
  - 仕様書の方針（「プログレス表示なし、シンプルさ優先」）に準拠
  - 非同期並行取得により数秒で完了する想定
  - 実装の複雑さを避ける
- **Alternatives Considered**:
  - (A) richライブラリの`Progress`バーを使用: 実装複雑化、数秒で完了するため不要
  - (B) 各プロバイダーの取得状況をリアルタイム表示: 過剰な情報、CI/CDログでの視認性低下

### Decision 9: `--detect-changes`の移動先

- **Chosen**: `update`コマンドに`--detect-changes`オプションを移動
- **Rationale**:
  - 変更検知機能はスナップショット作成（Write操作）を伴う
  - `update`コマンドの責任範囲に含まれる
  - `list`コマンドをRead専用に保つ
- **Alternatives Considered**:
  - (A) `list --detect-changes`を維持: 責任の分離に反する
  - (B) 新規`detect-changes`コマンドを作成: コマンド数の増加、複雑化

### Decision 10: 既存テストケースの移行方針

- **Chosen**: API取得関連テストを新規`TestCLIUpdate`クラスに移動、キャッシュ読み込みテストを`TestCLIList`に残す
- **Rationale**:
  - テストケースの責任をコマンドの責任に合わせる
  - 既存のテストフィクスチャ（`setup_cache`、`sample_models`）を再利用
  - 90%カバレッジ維持を確保
- **Alternatives Considered**:
  - (A) すべてのテストを書き直す: 不要な作業、既存のテスト資産を無駄にする
  - (B) 既存テストを変更せず、新規テストのみ追加: テストケースの重複、保守コスト増加
