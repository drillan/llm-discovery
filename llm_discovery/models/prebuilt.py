"""Prebuilt data models for llm-discovery."""

import re
from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel, Field, computed_field, field_validator, model_validator

from llm_discovery.models.provider import ProviderSnapshot


class PrebuiltDataMetadata(BaseModel):
    """Metadata for prebuilt model data."""

    generated_at: datetime = Field(description="Data generation timestamp (UTC)")
    generator: str = Field(description="Generator tool name")
    version: str = Field(description="Tool version")

    @field_validator("generated_at")
    @classmethod
    def validate_not_future(cls, v: datetime) -> datetime:
        """Validate that generated_at is not in the future."""
        if v > datetime.now(UTC):
            msg = "generated_at cannot be in the future"
            raise ValueError(msg)
        return v

    @field_validator("version")
    @classmethod
    def validate_semver(cls, v: str) -> str:
        """Validate that version is in semver format (X.Y.Z)."""
        if not re.match(r"^\d+\.\d+\.\d+$", v):
            msg = "version must be in semver format (X.Y.Z)"
            raise ValueError(msg)
        return v


class PrebuiltModelData(BaseModel):
    """Container for prebuilt model data with metadata."""

    metadata: PrebuiltDataMetadata
    providers: list[ProviderSnapshot] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_unique_providers(self) -> "PrebuiltModelData":
        """Validate that provider names are unique."""
        provider_names = [p.provider_name for p in self.providers]
        if len(provider_names) != len(set(provider_names)):
            msg = "Provider names must be unique"
            raise ValueError(msg)
        return self


class DataSourceType(str, Enum):
    """Type of data source (API or prebuilt)."""

    API = "api"
    PREBUILT = "prebuilt"


class DataSourceInfo(BaseModel):
    """Information about the data source for transparency."""

    source_type: DataSourceType
    timestamp: datetime
    provider_name: str

    @computed_field  # type: ignore[prop-decorator]
    @property
    def age_hours(self) -> float:
        """Calculate age of data in hours since timestamp."""
        return (datetime.now(UTC) - self.timestamp).total_seconds() / 3600

    def format_message(self) -> str:
        """Format user-friendly message about data source."""
        if self.source_type == DataSourceType.PREBUILT:
            return (
                f"[yellow]ℹ Using prebuilt data "
                f"(updated: {self.timestamp.isoformat()}, "
                f"age: {self.age_hours:.1f}h)[/yellow]"
            )
        return "[green]✓ Using latest API data[/green]"
