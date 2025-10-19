"""Core data models for llm-discovery."""

from datetime import UTC, datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator, model_validator


class ModelSource(str, Enum):
    """Source of model data."""

    API = "api"
    MANUAL = "manual"


class Model(BaseModel):
    """LLM model entity."""

    model_config = {"frozen": True}

    model_id: str = Field(..., description="Unique model identifier")
    model_name: str = Field(..., description="Human-readable model name")
    provider_name: str = Field(..., description="Provider name (openai, google, anthropic)")
    source: ModelSource = Field(..., description="Data source (api or manual)")
    fetched_at: datetime = Field(..., description="Timestamp when model was fetched")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional model metadata"
    )

    @field_validator("model_id", "model_name", "provider_name")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        """Validate that string fields are not empty."""
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()

    @field_validator("fetched_at")
    @classmethod
    def validate_utc_timezone(cls, v: datetime) -> datetime:
        """Ensure datetime is in UTC."""
        if v.tzinfo is None:
            return v.replace(tzinfo=UTC)
        return v.astimezone(UTC)


class ProviderType(str, Enum):
    """Supported LLM providers."""

    OPENAI = "openai"
    GOOGLE = "google"
    ANTHROPIC = "anthropic"


class GoogleBackend(str, Enum):
    """Google AI backends."""

    AI_STUDIO = "ai_studio"
    VERTEX_AI = "vertex_ai"


class Provider(BaseModel):
    """Provider entity."""

    model_config = {"frozen": True}

    name: ProviderType = Field(..., description="Provider name")
    api_endpoint: str | None = Field(None, description="API endpoint URL")
    fetch_method: ModelSource = Field(..., description="Fetch method (api or manual)")
    google_backend: GoogleBackend | None = Field(None, description="Google backend type")
    models_count: int = Field(0, description="Number of models from this provider")

    @model_validator(mode="after")
    def validate_google_backend(self) -> "Provider":
        """Validate Google backend consistency."""
        if self.name == ProviderType.GOOGLE:
            if self.google_backend is None:
                raise ValueError("Google provider must specify google_backend")
        elif self.google_backend is not None:
            raise ValueError("google_backend can only be set for Google provider")
        return self


class FetchStatus(str, Enum):
    """Fetch operation status."""

    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"


class ProviderSnapshot(BaseModel):
    """Snapshot of a single provider's models."""

    model_config = {"frozen": True}

    provider_name: str = Field(..., description="Provider name")
    models: list[Model] = Field(default_factory=list, description="Models from provider")
    fetch_status: FetchStatus = Field(..., description="Fetch operation status")
    fetched_at: datetime = Field(..., description="Timestamp of fetch")
    error_message: str | None = Field(None, description="Error message if fetch failed")

    @field_validator("fetched_at")
    @classmethod
    def validate_utc_timezone(cls, v: datetime) -> datetime:
        """Ensure datetime is in UTC."""
        if v.tzinfo is None:
            return v.replace(tzinfo=UTC)
        return v.astimezone(UTC)


class Snapshot(BaseModel):
    """Complete snapshot of all providers' models."""

    model_config = {"frozen": True}

    snapshot_id: UUID = Field(default_factory=uuid4, description="Unique snapshot ID")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    providers: list[ProviderSnapshot] = Field(
        default_factory=list, description="Provider snapshots"
    )

    @field_validator("providers")
    @classmethod
    def validate_non_empty_models(cls, v: list[ProviderSnapshot]) -> list[ProviderSnapshot]:
        """Ensure at least one provider snapshot exists."""
        if not v:
            raise ValueError("Snapshot must contain at least one provider")
        return v

    @field_validator("timestamp")
    @classmethod
    def validate_utc_timezone(cls, v: datetime) -> datetime:
        """Ensure datetime is in UTC."""
        if v.tzinfo is None:
            return v.replace(tzinfo=UTC)
        return v.astimezone(UTC)


class ChangeType(str, Enum):
    """Type of model change."""

    ADDED = "added"
    REMOVED = "removed"


class Change(BaseModel):
    """Model change record."""

    model_config = {"frozen": True}

    change_id: UUID = Field(default_factory=uuid4, description="Unique change ID")
    change_type: ChangeType = Field(..., description="Type of change")
    model_id: str = Field(..., description="Model ID that changed")
    model_name: str = Field(..., description="Model name")
    provider_name: str = Field(..., description="Provider name")
    detected_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Detection timestamp"
    )
    previous_snapshot_id: UUID = Field(..., description="Previous snapshot ID")
    current_snapshot_id: UUID = Field(..., description="Current snapshot ID")

    @field_validator("detected_at")
    @classmethod
    def validate_utc_timezone(cls, v: datetime) -> datetime:
        """Ensure datetime is in UTC."""
        if v.tzinfo is None:
            return v.replace(tzinfo=UTC)
        return v.astimezone(UTC)


class CacheMetadata(BaseModel):
    """Cache metadata."""

    version: str = Field(..., description="Cache format version (semantic versioning)")
    created_at: datetime = Field(..., description="Cache creation timestamp")
    last_updated: datetime = Field(..., description="Last update timestamp")

    @field_validator("version")
    @classmethod
    def validate_semantic_version(cls, v: str) -> str:
        """Validate semantic version format (x.y.z)."""
        parts = v.split(".")
        if len(parts) != 3:
            raise ValueError("Version must be in semantic versioning format (x.y.z)")
        for part in parts:
            if not part.isdigit():
                raise ValueError("Version parts must be numeric")
        return v

    @field_validator("created_at", "last_updated")
    @classmethod
    def validate_utc_timezone(cls, v: datetime) -> datetime:
        """Ensure datetime is in UTC."""
        if v.tzinfo is None:
            return v.replace(tzinfo=UTC)
        return v.astimezone(UTC)


class Cache(BaseModel):
    """Cache structure for TOML persistence."""

    metadata: CacheMetadata = Field(..., description="Cache metadata")
    providers: list[ProviderSnapshot] = Field(
        default_factory=list, description="Cached provider snapshots"
    )

    @model_validator(mode="after")
    def validate_provider_consistency(self) -> "Cache":
        """Validate provider name consistency."""
        provider_names = [p.provider_name for p in self.providers]
        if len(provider_names) != len(set(provider_names)):
            raise ValueError("Duplicate provider names in cache")
        return self
