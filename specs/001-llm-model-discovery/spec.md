# Feature Specification: LLMモデル発見・追跡システム

**Feature Branch**: `001-llm-model-discovery`
**Created**: 2025-10-19
**Status**: Draft
**Input**: User description: "plans/speckit-input.txt を日本語で要件・仕様定義してください"

## Clarifications

### Session 2025-10-19

- Q: export --formatにTOML形式を追加してください → A: TOML形式のエクスポート機能を追加。TOML形式は他ツールとの相互運用性を重視した構造で出力され、User Story 2のAcceptance Scenarioに具体的なテストケースを追加しました。

- Q: FR-017とFR-018のエラーハンドリング方針の明確化 → A: フォールバック動作を禁止し、API障害時および部分的取得失敗時は明確なエラーメッセージを表示して処理を終了する（ゼロ以外の終了コードで終了）。これにより、ユーザーは問題を即座に認識でき、外部のリトライメカニズム（cron、CI/CD）で対処可能になります。

- Q: GoogleプロバイダーのVertex AI対応 → A: GoogleプロバイダーにVertex AIのサポートを追加。環境変数GOOGLE_GENAI_USE_VERTEXAI=trueでVertex AIを有効化し、GOOGLE_APPLICATION_CREDENTIALSでGCP認証情報を指定する。未設定の場合はGoogle AI Studioを使用する。FR-001、FR-002、FR-021を更新し、Edge Casesに認証エラーの処理を追加しました。

- Q: data-model.mdのPydanticバージョンはv2に準拠していますか → A: Pydantic v2構文に完全移行する（`@field_validator`, `model_config`, `ConfigDict`を使用）。Python 3.13を対象とし、パフォーマンス向上と型安全性強化のため、Pydantic v2（メンテナンス中）を採用します。

- Q: バージョン情報の取得方法 → A: importlib.metadataでpyproject.tomlから動的取得（Primary Data Non-Assumption Principle準拠）。ハードコーディングを禁止し、pyproject.tomlをSingle Source of Truthとして維持します。

- Q: `--version`フラグの出力形式 → A: `llm-discovery, version X.Y.Z`形式。多くのCLIツールが採用する標準的な形式で、パッケージ名とバージョンが明確に区別され、CI/CDスクリプトでのパースが容易です。

- Q: バージョン取得失敗時の動作 → A: エラーメッセージを表示して終了（Primary Data Non-Assumption準拠）。"unknown"や"dev"といったフォールバック値を返さず、パッケージのインストール状態を確認するようユーザーに促します。

- Q: editable install時のバージョン取得動作 → A: 通常インストールと同じ動作（importlib.metadataで取得、失敗時はエラー）。開発環境でも本番環境と同じ動作を保証し、Primary Data Non-Assumption Principleを維持します。

- Q: pyproject.tomlのバージョン管理方針 → A: 静的バージョン（pyproject.tomlに直接記述、手動更新）。シンプルで予測可能、レビュー可能なバージョン管理を実現し、uvxとの互換性を確保します。リリースプロセスは「バージョン更新→コミット→タグ→リリース」の順で行います。

- Q: `update`コマンドの基本的な責任範囲をどのように定義しますか？ → A: キャッシュ更新に責任を限定し、表示機能は完全に削除する。責任の分離原則（Single Responsibility Principle）を徹底し、`update`=Write操作、`list`=Read操作として明確に区別する。業界標準（apt update、brew update等）との一貫性を保つ。

- Q: `update`コマンドが成功時に表示するサマリー情報の具体的な内容は何ですか？ → A: モデル総数 + プロバイダー別モデル数 + キャッシュパス（例: "OpenAI: 15, Google: 20, Anthropic: 7 / Total: 42 / Cached to: ~/.cache/..."）。ユーザーが更新の成果を即座に確認でき、トラブルシューティング時にキャッシュの場所が分かる必要十分な情報を提供する。

- Q: `update --detect-changes`で変更が検出された場合、画面に表示する情報の詳細レベルはどの程度ですか？ → A: 変更タイプ別のカウント + 各変更のモデルID/名前をグループ化して表示（例: "Added models (3): openai/gpt-4.5, google/gemini-2.0, ..."）。変更の概要を素早く把握でき、詳細も確認できるバランスの良い出力を提供する。CI/CDログでも読みやすく、手動確認時にも十分な情報を提供する。

- Q: `update`コマンドで特定のプロバイダーのみを更新するオプション（例: `--provider openai`）を提供しますか？ → A: Phase 1では提供せず、将来的な拡張として検討する。MVP段階では基本的なワークフロー（全プロバイダー一括更新）を安定させることを優先し、特定プロバイダーのみの更新は高度な使用例として需要を見極めてからPhase 2以降で追加する。

- Q: `update`コマンドがAPIからデータを取得中、ユーザーへのプログレス表示（進行状況）をどのように行いますか？ → A: プログレス表示なし（API取得完了後にサマリーのみ表示）。非同期並行取得により数秒で完了する想定のため、シンプルさを優先し、実装の複雑さを避ける。API取得が完了した時点でプロバイダー別モデル数、総数、キャッシュパスを表示する。

## User Scenarios & Testing *(mandatory)*

### User Story 1 - キャッシュ更新とモデル一覧表示 (Priority: P1)

DevOpsエンジニアは、複数のLLMプロバイダーから利用可能なモデル一覧を取得してキャッシュに保存し（`update`コマンド）、保存されたデータを表示する（`list`コマンド）ことで、現在のモデルラインナップを把握する。

**Why this priority**: システムの基盤機能であり、すべての機能がこれに依存する。この機能単体でも「現在利用可能なモデルの把握」という価値を提供できる。

**Independent Test**: `uvx llm-discovery update` でキャッシュを作成し、`uvx llm-discovery list` で表示されることで検証可能。オフラインキャッシュの存在確認も独立してテストできる。

**Acceptance Scenarios**:

1. **Given** 初回実行時、**When** `uvx llm-discovery update` を実行、**Then** OpenAI、Google（Google AI StudioまたはVertex AI）、AnthropicのモデルがAPI/手動データから取得され、TOML形式でキャッシュに保存される。プロバイダー別モデル数、総数、キャッシュパスが表示される（例: "OpenAI: 15, Google: 20, Anthropic: 7 / Total: 42 / Cached to: ~/.cache/llm-discovery/models_cache.toml"）
2. **Given** キャッシュが存在する状態、**When** `uvx llm-discovery update` を実行、**Then** 最新のモデルデータでキャッシュが更新され、更新後のプロバイダー別モデル数、総数、キャッシュパスが表示される
3. **Given** キャッシュが存在する状態、**When** オフライン環境で `uvx llm-discovery list` を実行、**Then** キャッシュからモデル一覧が表形式で表示される
4. **Given** キャッシュが存在しない状態、**When** `uvx llm-discovery list` を実行、**Then** 明確なエラーメッセージ「No cached data available. Please run 'llm-discovery update' first to fetch model data.」が表示され、処理が終了する（ゼロ以外の終了コード）
5. **Given** API障害発生中、**When** `uvx llm-discovery update` を実行、**Then** 明確なエラーメッセージが表示され、処理が終了する（ゼロ以外の終了コードで終了）
6. **Given** 一部のプロバイダーでAPI障害、**When** `uvx llm-discovery update` を実行、**Then** 明確なエラーメッセージが表示され、処理が終了する（部分成功での継続は行わない）
7. **Given** GOOGLE_GENAI_USE_VERTEXAI=trueとGOOGLE_APPLICATION_CREDENTIALSが設定されている、**When** `uvx llm-discovery update` を実行、**Then** Vertex AI経由でGoogleのモデル一覧が取得される
8. **Given** GOOGLE_GENAI_USE_VERTEXAI=trueだがGOOGLE_APPLICATION_CREDENTIALSが未設定、**When** `uvx llm-discovery update` を実行、**Then** 明確なエラーメッセージ（環境変数の設定方法と認証情報の取得手順を含む）が表示され、処理が終了する

---

### User Story 2 - マルチフォーマットエクスポート (Priority: P2)

データサイエンティストは、モデル一覧を分析用にCSV形式で、CI/CD統合用にJSON形式で、ドキュメント用にMarkdown形式で、設定ファイル用にTOML/YAML形式でエクスポートする。

**Why this priority**: ユーザーが取得したデータを実際に活用するための重要機能。Story 1で取得したデータを様々な用途に応じて出力できる。

**Independent Test**: 各形式へのエクスポートコマンド（例: `uvx llm-discovery export --format csv`）を実行し、正しいフォーマットでファイルが生成されることで検証可能。

**Acceptance Scenarios**:

1. **Given** モデルデータが存在する状態、**When** `uvx llm-discovery export --format json` を実行、**Then** CI/CD統合に最適化されたJSON形式でデータが出力される
2. **Given** モデルデータが存在する状態、**When** `uvx llm-discovery export --format csv` を実行、**Then** 表計算ソフトで分析可能なCSV形式でデータが出力される
3. **Given** モデルデータが存在する状態、**When** `uvx llm-discovery export --format yaml` を実行、**Then** 設定ファイル用のYAML形式でデータが出力される
4. **Given** モデルデータが存在する状態、**When** `uvx llm-discovery export --format markdown` を実行、**Then** 人間が読みやすいMarkdown形式でドキュメントが出力される
5. **Given** モデルデータが存在する状態、**When** `uvx llm-discovery export --format toml` を実行、**Then** 他ツールとの相互運用性を考慮したTOML形式でデータが出力される

---

### User Story 3 - 新モデル検知と差分レポート (Priority: P3)

MLOpsエンジニアは、定期的にモデル一覧を取得し、前回からの変更（新規追加・削除されたモデル）を検知して、変更内容を記録・通知する。

**Why this priority**: 継続的な監視とトラッキング機能。Story 1とStory 2が完成していれば、この機能を独立して追加できる。

**Independent Test**: モデル一覧を2回取得し、2回目の取得時に `--detect-changes` フラグを使用して、changes.jsonとCHANGELOG.mdが生成されることで検証可能。

**Acceptance Scenarios**:

1. **Given** 前回のスナップショットが存在する状態、**When** `uvx llm-discovery update --detect-changes` を実行、**Then** 新規追加されたモデルと削除されたモデルが検出され、changes.jsonに記録される。変更タイプ別のカウントと各変更のモデルID/名前がグループ化されて画面に表示される（例: "Added models (3): openai/gpt-4.5, google/gemini-2.0, anthropic/claude-3.5-opus / Removed models (1): openai/gpt-3.5-turbo-0301"）
2. **Given** 新モデルが検出された状態、**When** 変更検知が完了、**Then** CHANGELOG.mdに日付付きで変更内容が自動追記される
3. **Given** 初回実行時（前回データなし）、**When** `uvx llm-discovery update --detect-changes` を実行、**Then** 「前回データが存在しないため差分検出不可」というメッセージが表示され、現在のデータがベースラインとして保存される
4. **Given** 30日以上前のスナップショット、**When** スナップショット管理が実行、**Then** デフォルトの保持期間を超えたスナップショットが自動削除される

---

### User Story 4 - CI/CD統合とPython API利用 (Priority: P4)

DevOpsエンジニアは、GitHub ActionsのワークフローにLLMモデル監視を組み込み、新モデルが検出された際にSlackへ通知を送信する。データサイエンティストは、Pythonスクリプト内でモデル一覧を取得し、独自の分析パイプラインを構築する。

**Why this priority**: ユーザーが既存のワークフローに統合するための機能。基本機能（Story 1-3）が完成していれば、後から追加できる。

**Independent Test**: GitHub ActionsのYAMLファイルを作成し、ワークフローが正常に実行されて通知が送信されることで検証可能。Python APIについては、スクリプト内でインポートして使用できることで検証可能。

**Acceptance Scenarios**:

1. **Given** GitHub Actionsワークフロー設定、**When** cronジョブが実行、**Then** 10行以内のYAML設定で新モデル検知とSlack通知が完了する
2. **Given** Pythonスクリプト、**When** `from llm_discovery import DiscoveryClient` でインポート、**Then** CLIと同じ機能をPython APIとして利用できる
3. **Given** changes.jsonファイル、**When** CI/CDパイプラインで読み込み、**Then** 標準化されたJSON形式で変更情報を処理できる
4. **Given** ドキュメント例、**When** Slack/Discord/Email統合を設定、**Then** 提供されたサンプルコードを参考に通知システムを構築できる

---

### Edge Cases

- **API障害・レート制限時の対応**: プロバイダーのAPI障害やレート制限が発生した場合、明確なエラーメッセージ（障害の原因、影響を受けたプロバイダー名、推奨される対処法）を表示し、ゼロ以外の終了コードで処理を終了する。リトライ戦略は実装しない（外部のcron/CI/CDで管理）。
- **部分的取得失敗の処理**: マルチプロバイダー環境において、1つでもプロバイダーの取得が失敗した場合、明確なエラーメッセージを表示し、処理を終了する（部分成功での継続は行わない）。
- **TOMLファイル破損時のリカバリ**: キャッシュファイルが破損している場合、警告を表示し、APIから再取得を試みる。再取得不可の場合はエラーで終了する。
- **初回実行時の前回データ不在**: 差分検出機能を初回実行時に使用した場合、「ベースラインとして現在のデータを保存」というメッセージを表示し、次回以降の実行で差分検出が可能になる。
- **モデル名変更の検知**: モデル名の変更は「削除」と「追加」として検出される。プロバイダーが提供するモデルIDが変更された場合も同様に扱う。
- **スナップショット履歴の肥大化**: デフォルトで30日間のスナップショットを保持し、それ以上古いものは自動削除される。ユーザーは設定で保持期間を変更可能。
- **Vertex AI認証情報の欠如・不正**: GOOGLE_GENAI_USE_VERTEXAI=trueが設定されているが、GOOGLE_APPLICATION_CREDENTIALSが未設定または無効なパスを指している場合、明確なエラーメッセージ（必要な環境変数名、設定方法、GCP認証情報の取得手順へのリンク）を表示し、処理を終了する。
- **Google AI Studio/Vertex AIの切り替え**: GOOGLE_GENAI_USE_VERTEXAI環境変数の値によって、Google AI StudioとVertex AIを切り替える。未設定またはfalseの場合はGoogle AI Studioを使用し、trueの場合はVertex AIを使用する。
- **バージョン情報取得の失敗**: importlib.metadataがパッケージメタデータを取得できない場合（不正なインストール、開発環境での問題等）、明確なエラーメッセージ（パッケージの再インストール手順、editable installの確認方法を含む）を表示し、ゼロ以外の終了コードで処理を終了する。フォールバック値（"unknown"、"dev"等）は使用しない。editable install（`uv pip install -e .`）時も通常インストールと同じ動作を保証し、開発環境と本番環境で一貫性を維持する。

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: システムは、OpenAI、Google（Google AI StudioおよびVertex AI）、Anthropicの各プロバイダーから利用可能なモデル一覧を取得しなければならない
- **FR-002**: システムは、API経由での動的取得（OpenAI、Google）と手動管理データ（Anthropic）のハイブリッド方式をサポートしなければならない。Googleプロバイダーは環境変数（GOOGLE_GENAI_USE_VERTEXAI）によってGoogle AI StudioまたはVertex AIを選択可能でなければならない
- **FR-003**: システムは、取得したモデルデータをTOML形式でローカルにキャッシュし、オフライン動作を可能にしなければならない
- **FR-004**: システムは、各モデルの取得方法（api/manual）とタイムスタンプをメタデータとして管理しなければならない
- **FR-005**: システムは、JSON、CSV、YAML、Markdown、TOMLの各形式でモデルデータをエクスポート可能でなければならない
- **FR-006**: システムは、各エクスポート形式に最適化された構造で出力しなければならない（例: JSON→CI/CD統合、CSV→分析、Markdown→ドキュメント、TOML→相互運用性・設定ファイル、YAML→設定ファイル）
- **FR-007**: システムは、前回取得時との差分を検出し、新規追加・削除されたモデルを識別しなければならない
- **FR-008**: システムは、スナップショット履歴をデフォルトで30日間保持し、それ以上古いものは自動削除しなければならない
- **FR-009**: システムは、モデル変更を検知した際にCHANGELOG.mdを自動生成・更新しなければならない
- **FR-010**: システムは、CI/CD統合用の標準形式としてchanges.jsonを出力しなければならない
- **FR-011**: システムは、Slack、Discord、Email等の通知システム統合例をドキュメントで提供しなければならない
- **FR-012**: システムは、GitHub Actions cronやsystemd timer等の監視機能実装例をドキュメントで提供しなければならない
- **FR-013**: システムは、typerフレームワークを使用したCLIインターフェースを提供しなければならない
- **FR-014**: システムは、Python APIとして同等の機能をプログラムから利用可能にしなければならない
- **FR-024**: システムは、`update`コマンドを提供し、APIからモデルデータを取得してキャッシュに保存しなければならない。updateコマンドは表示機能を持たず、プロバイダー別モデル数、総数、キャッシュパスのみを出力する（例: "OpenAI: 15, Google: 20, Anthropic: 7 / Total: 42 / Cached to: ~/.cache/llm-discovery/models_cache.toml"）。責任の分離原則に準拠する
- **FR-025**: システムは、`list`コマンドを提供し、キャッシュからモデルデータを読み込んで表形式で表示しなければならない。listコマンドはキャッシュが存在しない場合、明確なエラーメッセージ「No cached data available. Please run 'llm-discovery update' first to fetch model data.」を表示してゼロ以外の終了コードで終了する
- **FR-026**: システムは、`update`コマンドに`--detect-changes`オプションを提供し、変更検知機能を実行しなければならない。変更が検出された場合、変更タイプ別のカウントと各変更のモデルID/名前をグループ化して画面に表示し（例: "Added models (3): openai/gpt-4.5, google/gemini-2.0, ..."）、changes.jsonとCHANGELOG.mdに記録する
- **FR-015**: システムは、uvxによるインストール不要の即座実行をサポートしなければならない
- **FR-016**: システムは、非同期API（asyncio）を使用して複数プロバイダーからの並行取得を実現しなければならない
- **FR-017**: システムは、API障害時に明確なエラーメッセージを表示して処理を終了しなければならない（フォールバック禁止）
- **FR-018**: システムは、部分的取得失敗時に明確なエラーメッセージを表示して処理を終了しなければならない（部分成功の継続禁止）
- **FR-019**: システムは、TOMLキャッシュファイル破損時のリカバリ機能を提供しなければならない
- **FR-020**: システムは、テストカバレッジ90%以上を維持しなければならない
- **FR-021**: システムは、Vertex AIを使用する場合、環境変数GOOGLE_APPLICATION_CREDENTIALSで指定されたGCPサービスアカウント認証情報を使用しなければならない
- **FR-022**: システムは、`--version`フラグでパッケージバージョン情報を`llm-discovery, version X.Y.Z`形式で表示しなければならない。バージョン情報はimportlib.metadataを使用してpyproject.tomlから動的に取得し、ハードコーディングを禁止する。バージョン取得に失敗した場合、明確なエラーメッセージを表示して終了する（フォールバック値の使用禁止）
- **FR-023**: システムは、Python APIとして`llm_discovery.__version__`属性を公開しなければならない。この属性もimportlib.metadataから取得し、pyproject.tomlをSingle Source of Truthとして維持する。バージョン取得に失敗した場合、PackageNotFoundErrorまたはAttributeErrorが発生する

### Key Entities

- **Model（モデル）**: LLMプロバイダーが提供する機械学習モデル。主要属性は、モデルID（一意識別子）、モデル名、プロバイダー名、取得方法（api/manual）、取得タイムスタンプ、メタデータ（利用可能な機能、制限事項等）。
- **Provider（プロバイダー）**: LLMサービスを提供する企業（OpenAI、Anthropic、Google等）。主要属性は、プロバイダー名、APIエンドポイント（該当する場合）、取得方式（API/手動）、サポートされるモデルのリスト。Googleプロバイダーは、Google AI StudioまたはVertex AIのいずれかのバックエンドを使用する。
- **Snapshot（スナップショット）**: 特定時点でのモデル一覧の記録。主要属性は、スナップショットID、取得日時、プロバイダー別モデル一覧、メタデータ（取得成功/失敗ステータス）。スナップショット間の比較により変更検知を実現。
- **Change（変更）**: スナップショット間のモデル差分情報。主要属性は、変更タイプ（追加/削除）、対象モデル、検出日時、関連するスナップショットID。
- **Cache（キャッシュ）**: オフライン動作を可能にするローカルストレージ。TOML形式で保存され、最新のモデル情報と取得メタデータを含む。

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: ユーザーは、インストール不要で `uvx llm-discovery update` を実行してモデルデータを取得し、`uvx llm-discovery list` で即座にモデル一覧を表示できる
- **SC-002**: ユーザーは、パッケージのインストールから初回実行まで5分以内に完了できる（従来のpip installを使用する場合）
- **SC-003**: ユーザーは、1つのコマンド実行で新モデル検知から結果の確認まで完結できる
- **SC-004**: ユーザーは、10行以内のYAML設定でCI/CDパイプラインにモデル監視を統合できる
- **SC-005**: パッケージは、リリース後6ヶ月以内に月間ダウンロード数1,000件を達成する
- **SC-006**: GitHubリポジトリは、リリース後3ヶ月以内にStar数100件を達成する
- **SC-007**: システムは、複数プロバイダーからのモデル取得を並行実行し、全体の取得時間が最も遅いプロバイダーの応答時間と同等になる
- **SC-008**: システムは、テストカバレッジ90%以上を維持し、主要機能の動作が自動テストで保証される
- **SC-009**: ユーザーは、API障害時に明確なエラーメッセージと適切な終了コードを受け取り、問題の原因と対処法を理解できる
- **SC-010**: ユーザーは、提供されたドキュメント例を参考に、30分以内にSlack/Discord通知を設定できる

## Implementation Phases *(optional)*

### Phase 1 (MVP - Week 1-2)
- マルチプロバイダー対応のモデル取得機能
- TOML/JSON/CSV形式でのエクスポート
- 基本的なCLIインターフェース（update、list、exportコマンド）
- updateとlistの責任分離（update=Write、list=Read）
- uvx対応とPyPI配布準備
- 厳格なエラーハンドリング（API障害時・部分失敗時は明確なエラーメッセージで終了）

**成果物**: 実用可能な最小機能セット。ユーザーはモデル一覧を取得し、必要な形式でエクスポートできる。

### Phase 2 (Week 3-4)
- 変更検知機能の実装（差分検出アルゴリズム）
- スナップショット履歴管理（保存・削除ロジック）
- CHANGELOG.md自動生成
- changes.json標準形式の出力
- Python API公開

**成果物**: 継続的なモデル監視が可能なシステム。CI/CD統合の基盤が整う。

### Phase 3 (Month 2)
- 統合例ドキュメント（Slack/Discord/Email通知の実装例）
- GitHub Actions/systemd timer等の監視実装例
- YAML/Markdown形式のエクスポート追加
- 詳細なエラーメッセージとトラブルシューティングガイド（キャッシュ破損対応、API障害時の対処法）
- パフォーマンス最適化（並行取得の改善）

**成果物**: プロダクション環境で使用可能な完全版。ドキュメントと統合例により、ユーザーは簡単に自社システムへ組み込める。

## Scope Boundaries *(optional)*

### Out of Scope

以下の機能は本プロジェクトのスコープ外です：

- **モデル実行機能**: LLMモデルの実際の実行や推論は行わない（LiteLLM等の専用ツールを推奨）
- **性能ベンチマーク**: モデルの性能評価や品質測定は含まない
- **APIキー管理**: 認証情報の保存や管理機能は提供しない（ユーザーの環境変数管理に依存）
- **Web UI**: Phase 1では提供しない（将来的な拡張候補）
- **監視デーモン・定期実行機能**: 常駐プロセスとしての動作はサポートしない（CI/CDやcronでの実装例を提供）
- **モデルのフィルタリング・検索機能**: 複雑な条件でのモデル絞り込みは初期バージョンでは未対応
- **モデルメタデータの詳細管理**: 価格情報、トークン制限等の詳細情報の構造化管理は将来的な拡張
- **特定プロバイダーのみの更新機能**: Phase 1では全プロバイダー一括更新のみをサポート。`--provider`オプションによる特定プロバイダーのみの更新は、需要を見極めた上でPhase 2以降の拡張候補として検討

### Complementary Tools

- **llm-registry（yamanahlawat/llm-registry）**: 静的カタログとして「モデルが何をできるか」を提供。llm-discoveryは「何が存在するか」をリアルタイムで発見し、両者は補完的な関係。

## Assumptions *(optional)*

- ユーザーは、OpenAI/GoogleのAPIキーを環境変数として設定している（またはキャッシュデータのみで動作）。Googleプロバイダーについては、Google AI Studioの場合はAPIキー、Vertex AIの場合はGCPサービスアカウント認証情報（GOOGLE_APPLICATION_CREDENTIALS）を使用する
- Python 3.13以上の環境が利用可能
- インターネット接続が利用可能（初回取得時および差分検出時）。オフライン環境ではキャッシュデータを使用
- CI/CD環境はGitHub Actionsを想定しているが、他のCI/CDシステムでも応用可能
- スナップショット保持期間のデフォルト値（30日）は、ほとんどのユースケースで適切
- 通知システム（Slack/Discord/Email）の設定は、ユーザーが基本的な知識を持っていることを前提とする
- モデルIDの一意性はプロバイダー側で保証される
- Anthropicのモデルリストは手動管理データとして提供され、定期的に更新される
- パッケージバージョンはpyproject.tomlで静的に管理され、リリース時に手動で更新される。リリースプロセスは「pyproject.tomlのバージョン更新→コミット→Gitタグ作成→PyPIリリース」の順で行われる

## Target Users *(optional)*

- **DevOpsエンジニア**: 新モデルのリリースを監視し、コスト最適化の機会を発見する
- **MLOpsエンジニア**: CI/CDパイプラインにモデル監視を組み込み、自動化されたワークフローを構築する
- **データサイエンティスト**: モデルの比較分析や選定のために最新のモデル一覧を取得する
- **プロダクトマネージャー**: LLMプロバイダーのリリース状況を追跡し、製品戦略を検討する

## Dependencies *(optional)*

### External Dependencies

- **プロバイダーAPI**: OpenAI API、Google AI API（Google AI StudioおよびVertex AI）（モデル一覧取得に依存）
- **Python標準ライブラリ**: asyncio（非同期処理）、pathlib（ファイル操作）、json/csv/yaml（エクスポート）、importlib.metadata（バージョン情報取得、Python 3.8+標準ライブラリ）
- **サードパーティライブラリ**: typer（CLI）、rich（美しい出力）、pydantic v2（データバリデーション・型安全性）、toml（キャッシュ管理）
- **配布インフラ**: PyPI（パッケージ配布）、uvx（インストール不要実行）

### System Dependencies

- Python 3.13以上のランタイム
- uvパッケージマネージャー（推奨）
- インターネット接続（初回取得時）
- ファイルシステムへの読み書き権限（キャッシュ・スナップショット保存）
- GCPサービスアカウント認証情報（Vertex AIを使用する場合のみ、GOOGLE_APPLICATION_CREDENTIALSで指定）

### Potential Blockers

- プロバイダーのAPI仕様変更による互換性問題
- APIレート制限による取得頻度の制約
- プロバイダー側の障害による取得失敗
- Python 3.13未満の環境での互換性問題
- Vertex AI使用時のGCP認証情報の設定ミスや権限不足

## Risks & Mitigations *(optional)*

### Technical Risks

- **リスク**: プロバイダーのAPI仕様が予告なく変更される
  - **軽減策**: キャッシュデータへのフォールバック、バージョン管理されたAPIクライアント、定期的な互換性テスト

- **リスク**: APIレート制限により頻繁な取得ができない
  - **軽減策**: キャッシュの有効活用、取得頻度の推奨ガイドライン提供、段階的な再試行戦略

- **リスク**: 非同期処理のバグによるデータ整合性問題
  - **軽減策**: 高いテストカバレッジ（90%以上）、統合テストによる並行処理の検証

### Adoption Risks

- **リスク**: ユーザーがCI/CD統合方法を理解できない
  - **軽減策**: 詳細なドキュメント例、GitHub Actions用のサンプルワークフロー提供、10行以内のYAML設定を目標とした簡潔さ

- **リスク**: 競合ツールとの差別化が不明確
  - **軽減策**: llm-registryとの補完関係の明確化、リアルタイム発見・変更追跡の価値を強調

## Open Questions *(optional)*

現時点で明確化が必要な項目はありません。要件は十分に具体的で、実装に必要な情報が揃っています。
