# Data Model: Prebuilt Model Data Support

**Phase**: 1 - Design & Contracts
**Date**: 2025-10-19
**Status**: Complete

## Overview

この機能で導入する新規エンティティと、既存エンティティの拡張を定義します。

## Entities

### PrebuiltDataMetadata (New)

事前生成データファイルのメタデータを表すエンティティ。

**Fields**:
- `generated_at`: `datetime` - データ生成日時（ISO 8601形式、UTC）
- `generator`: `str` - データ生成ツール名（"llm-discovery"）
- `version`: `str` - ツールバージョン（例: "0.1.0"）

**Validation Rules**:
- `generated_at`は必須、未来の日時は不可
- `generator`は必須、空文字列不可
- `version`はセマンティックバージョニング形式（例: "X.Y.Z"）

**Relationships**:
- PrebuiltModelDataに1対1で関連付け

**State Transitions**: なし（イミュータブル）

**Pydantic Model**:
```python
from datetime import datetime
from pydantic import BaseModel, Field, field_validator

class PrebuiltDataMetadata(BaseModel):
    generated_at: datetime = Field(description="Data generation timestamp (UTC)")
    generator: str = Field(description="Generator tool name")
    version: str = Field(description="Tool version")

    @field_validator("generated_at")
    @classmethod
    def validate_not_future(cls, v: datetime) -> datetime:
        if v > datetime.now(UTC):
            raise ValueError("generated_at cannot be in the future")
        return v

    @field_validator("version")
    @classmethod
    def validate_semver(cls, v: str) -> str:
        import re
        if not re.match(r'^\d+\.\d+\.\d+$', v):
            raise ValueError("version must be in semver format (X.Y.Z)")
        return v
```

---

### PrebuiltModelData (New)

事前生成されたモデルデータ全体を表すエンティティ。

**Fields**:
- `metadata`: `PrebuiltDataMetadata` - メタデータ
- `providers`: `list[ProviderSnapshot]` - プロバイダーごとのモデルスナップショット

**Validation Rules**:
- `metadata`は必須
- `providers`は必須、空リスト不可
- 各`ProviderSnapshot`のプロバイダー名は一意であること

**Relationships**:
- PrebuiltDataMetadata: 1対1
- ProviderSnapshot: 1対多（既存エンティティを再利用）

**State Transitions**: なし（イミュータブル、ファイル全体を再生成）

**Pydantic Model**:
```python
from pydantic import BaseModel, Field, model_validator

class PrebuiltModelData(BaseModel):
    metadata: PrebuiltDataMetadata
    providers: list[ProviderSnapshot] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_unique_providers(self) -> "PrebuiltModelData":
        provider_names = [p.provider_name for p in self.providers]
        if len(provider_names) != len(set(provider_names)):
            raise ValueError("Provider names must be unique")
        return self
```

---

### DataSourceType (New Enum)

データの取得元を示す列挙型。

**Values**:
- `API`: リアルタイムAPI取得
- `PREBUILT`: 事前生成データ

**Usage**:
```python
from enum import Enum

class DataSourceType(str, Enum):
    API = "api"
    PREBUILT = "prebuilt"
```

---

### DataSourceInfo (New)

データソース情報を表すエンティティ。UIメッセージ生成に使用。

**Fields**:
- `source_type`: `DataSourceType` - データソースタイプ
- `timestamp`: `datetime` - データ取得/生成日時
- `age_hours`: `float` - データ経過時間（時間単位）
- `provider_name`: `str` - プロバイダー名

**Validation Rules**:
- `timestamp`は必須
- `age_hours`は0以上
- `provider_name`は必須、空文字列不可

**Calculated Fields**:
- `age_hours`は`timestamp`から自動計算

**Pydantic Model**:
```python
from datetime import datetime, UTC
from pydantic import BaseModel, computed_field

class DataSourceInfo(BaseModel):
    source_type: DataSourceType
    timestamp: datetime
    provider_name: str

    @computed_field
    @property
    def age_hours(self) -> float:
        return (datetime.now(UTC) - self.timestamp).total_seconds() / 3600

    def format_message(self) -> str:
        """Format user-friendly message."""
        if self.source_type == DataSourceType.PREBUILT:
            return (
                f"[yellow]ℹ Using prebuilt data "
                f"(updated: {self.timestamp.isoformat()}, "
                f"age: {self.age_hours:.1f}h)[/yellow]"
            )
        else:
            return "[green]✓ Using latest API data[/green]"
```

---

## Existing Entity Extensions

### Model (Existing - No Changes)

既存の`Model`クラスはそのまま使用します。`source`フィールドが既に`ModelSource`（api/manual）を持っているため、新規フィールド追加は不要。

### ProviderSnapshot (Existing - No Changes)

既存の`ProviderSnapshot`クラスをそのまま再利用します。

### Config (Existing - Extension)

既存の`Config`クラスに、APIキー有無チェック用のヘルパーメソッドを追加します。

**New Method**:
```python
def has_any_api_keys(self) -> bool:
    """Check if any API keys are configured."""
    return bool(
        self.openai_api_key or
        self.google_api_key or
        self.google_genai_use_vertexai
    )
```

---

## File Format Specification

### Prebuilt Data JSON Structure

```json
{
  "metadata": {
    "generated_at": "2025-10-19T00:00:00+00:00",
    "generator": "llm-discovery",
    "version": "0.1.0"
  },
  "providers": [
    {
      "provider_name": "openai",
      "fetched_at": "2025-10-19T00:00:00+00:00",
      "fetch_status": "success",
      "error_message": null,
      "models": [
        {
          "model_id": "gpt-4",
          "model_name": "GPT-4",
          "provider_name": "openai",
          "source": "api",
          "fetched_at": "2025-10-19T00:00:00+00:00",
          "metadata": {
            "created": 1234567890,
            "owned_by": "openai"
          }
        }
      ]
    }
  ]
}
```

### File Location

- **Path**: `data/prebuilt/models.json` (repository root)
- **Remote URL**: `https://raw.githubusercontent.com/drillan/llm-discovery/main/data/prebuilt/models.json`
- **Size Constraint**: < 500KB
- **Encoding**: UTF-8
- **Format**: JSON (minified for production)
- **Access Method**: HTTP GET request from PrebuiltDataLoader

---

## Data Volume Assumptions

- **Providers**: 3（OpenAI、Google、Anthropic）
- **Models per Provider**: 平均30モデル
- **Total Models**: 約100モデル
- **File Size**: 約200-300KB（メタデータ含む）
- **Update Frequency**: 1日1回

---

## Summary

新規エンティティ4つ（PrebuiltDataMetadata、PrebuiltModelData、DataSourceType、DataSourceInfo）と、既存Configクラスの拡張を定義しました。すべてpydanticでバリデーション可能で、型安全です。

## Next Steps

- contracts/prebuilt-data-loader.md: PrebuiltDataLoaderのAPIコントラクト定義
- quickstart.md: ユーザー向けガイド作成
