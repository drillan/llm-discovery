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
    def from_env(cls, require_api_keys: bool = True) -> "Config":
        """Create Config from environment variables.

        Args:
            require_api_keys: If True, require API keys to be set. If False, allow None.

        Raises:
            ValueError: If required environment variables are not set
        """
        # Get API keys
        openai_api_key = os.environ.get("OPENAI_API_KEY")
        google_api_key = os.environ.get("GOOGLE_API_KEY")
        google_use_vertexai = os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "").lower() == "true"
        google_credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")

        # Validate API keys if required (for update command)
        if require_api_keys:
            missing_configs = []

            # Check OpenAI
            if not openai_api_key:
                missing_configs.append(
                    "1. OpenAI API Key\n"
                    "   export OPENAI_API_KEY=sk-...\n"
                    "   Get your API key from: https://platform.openai.com/api-keys"
                )

            # Check Google
            if not google_api_key and not (google_use_vertexai and google_credentials_path):
                missing_configs.append(
                    "2. Google AI API Configuration\n"
                    "   Option A - Google AI Studio (recommended):\n"
                    "     export GOOGLE_API_KEY=...\n"
                    "     Get your API key from: https://aistudio.google.com/apikey\n\n"
                    "   Option B - Vertex AI:\n"
                    "     export GOOGLE_GENAI_USE_VERTEXAI=true\n"
                    "     export GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json\n"
                    "     See: https://cloud.google.com/vertex-ai/docs/authentication"
                )

            # Raise error if any configs are missing
            if missing_configs:
                error_message = (
                    "Required API keys not configured.\n\n"
                    "The following API keys are required:\n\n"
                    + "\n\n".join(missing_configs)
                    + "\n\nPlease set the required environment variables and try again."
                )
                raise ValueError(error_message)

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
            openai_api_key=openai_api_key,
            google_api_key=google_api_key,
            google_genai_use_vertexai=google_use_vertexai,
            google_application_credentials=(
                Path(google_credentials_path)
                if google_credentials_path
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
