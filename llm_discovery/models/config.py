"""Configuration models for llm-discovery."""

import os
from pathlib import Path

from pydantic import BaseModel, Field, field_validator, model_validator


class Config(BaseModel):
    """Application configuration."""

    # API Keys
    openai_api_key: str | None = Field(None, description="OpenAI API key")
    google_api_key: str | None = Field(None, description="Google AI Studio API key")

    # Google Vertex AI
    google_genai_use_vertexai: bool = Field(
        False, description="Use Google Vertex AI instead of AI Studio"
    )
    google_application_credentials: Path | None = Field(
        None, description="Path to GCP service account credentials"
    )

    # Cache settings
    llm_discovery_cache_dir: Path = Field(
        ..., description="Cache directory path"
    )
    llm_discovery_retention_days: int = Field(
        30, description="Snapshot retention period in days"
    )

    @classmethod
    def from_env(cls) -> "Config":
        """Create Config from environment variables.

        Raises:
            ValueError: If required environment variables are not set
        """
        # Get cache directory
        cache_dir_env = os.environ.get("LLM_DISCOVERY_CACHE_DIR")
        if cache_dir_env:
            cache_dir = Path(cache_dir_env)
        else:
            # Default to ~/.cache/llm-discovery
            import platformdirs
            cache_dir = Path(platformdirs.user_cache_dir("llm-discovery"))

        # Get retention days
        retention_days_env = os.environ.get("LLM_DISCOVERY_RETENTION_DAYS")
        retention_days = int(retention_days_env) if retention_days_env else 30

        return cls(
            openai_api_key=os.environ.get("OPENAI_API_KEY"),
            google_api_key=os.environ.get("GOOGLE_API_KEY"),
            google_genai_use_vertexai=os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "").lower() == "true",
            google_application_credentials=(
                Path(os.environ["GOOGLE_APPLICATION_CREDENTIALS"])
                if "GOOGLE_APPLICATION_CREDENTIALS" in os.environ
                else None
            ),
            llm_discovery_cache_dir=cache_dir,
            llm_discovery_retention_days=retention_days,
        )

    @field_validator("google_application_credentials")
    @classmethod
    def validate_credentials_file(cls, v: Path | None) -> Path | None:
        """Validate that credentials file exists if specified."""
        if v is not None and not v.exists():
            raise ValueError(
                f"Google application credentials file not found: {v}. "
                "Please ensure GOOGLE_APPLICATION_CREDENTIALS points to a valid JSON file."
            )
        return v

    @field_validator("llm_discovery_retention_days")
    @classmethod
    def validate_retention_days(cls, v: int) -> int:
        """Validate retention days is positive."""
        if v <= 0:
            raise ValueError("Retention days must be positive")
        return v

    @model_validator(mode="after")
    def validate_vertex_ai_credentials(self) -> "Config":
        """Validate Vertex AI credentials when enabled."""
        if self.google_genai_use_vertexai and self.google_application_credentials is None:
            raise ValueError(
                "GOOGLE_GENAI_USE_VERTEXAI is set to 'true', "
                "but GOOGLE_APPLICATION_CREDENTIALS is not set. "
                "To use Vertex AI, you need to set up GCP authentication."
            )
        return self

    @model_validator(mode="after")
    def validate_cache_dir_writable(self) -> "Config":
        """Validate cache directory is writable."""
        # Create directory if it doesn't exist
        self.llm_discovery_cache_dir.mkdir(parents=True, exist_ok=True)

        # Check if writable
        if not os.access(self.llm_discovery_cache_dir, os.W_OK):
            raise ValueError(
                f"Cache directory is not writable: {self.llm_discovery_cache_dir}"
            )
        return self

    def has_any_api_keys(self) -> bool:
        """Check if any API keys are configured.

        Returns:
            True if at least one API key is configured (OpenAI, Google AI Studio, or Vertex AI)
        """
        return bool(
            self.openai_api_key
            or self.google_api_key
            or self.google_genai_use_vertexai
        )
