"""Application configuration using Pydantic with hierarchical overrides."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Literal, Optional, Sequence

from pydantic import Field, HttpUrl, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8000
MIN_PORT = 1
MAX_PORT = 65_535
MIN_CONCURRENCY = 1
MAX_CONCURRENCY = 50
MIN_TIMEOUT = 1
MAX_TIMEOUT = 60
MAX_RETRY_ATTEMPTS = 5
MIN_RETRY_BACKOFF = 1.0
MAX_RETRY_BACKOFF = 3.0

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR"]
LogFormat = Literal["json", "text"]
HwAccel = Literal["vaapi", "cuda"]


class AppConfig(BaseSettings):
    """
    Application configuration with environment variable overrides.

    Priority order: CLI arguments > environment variables > .env file > defaults.
    Numeric limits align with network safety requirements from the design spec.
    """

    model_config = SettingsConfigDict(
        env_prefix="IPTV_SNIFFER_",
        env_file=".env",
        env_file_encoding="utf-8",
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    # Network scanning
    max_concurrency: int = Field(
        default=10,
        ge=MIN_CONCURRENCY,
        le=MAX_CONCURRENCY,
        description="Maximum simultaneous network requests during scanning.",
    )
    timeout: int = Field(
        default=10,
        ge=MIN_TIMEOUT,
        le=MAX_TIMEOUT,
        description="Network timeout in seconds for discovery requests.",
    )
    retry_attempts: int = Field(
        default=3,
        ge=0,
        le=MAX_RETRY_ATTEMPTS,
        description="Maximum retry attempts per channel probe.",
    )
    retry_backoff: float = Field(
        default=1.5,
        ge=MIN_RETRY_BACKOFF,
        le=MAX_RETRY_BACKOFF,
        description="Exponential backoff factor between retries.",
    )

    # FFmpeg
    ffmpeg_timeout: int = Field(
        default=10,
        ge=MIN_TIMEOUT,
        le=MAX_TIMEOUT,
        description="Timeout in seconds for FFmpeg validation jobs.",
    )
    ffmpeg_hwaccel: Optional[HwAccel] = Field(
        default=None,
        description="Hardware acceleration driver for FFmpeg processing.",
    )
    ffmpeg_custom_args: List[str] = Field(
        default_factory=list,
        description="Additional arguments appended to FFmpeg invocation.",
    )

    # Storage
    data_dir: Path = Field(
        default=Path("./data"),
        description="Directory for persistent data storage.",
    )
    screenshot_dir: Path = Field(
        default=Path("./screenshots"),
        description="Directory where channel screenshots are stored.",
    )

    # Web server
    host: str = Field(
        default=DEFAULT_HOST,
        description="IP address the web server binds to.",
    )
    port: int = Field(
        default=DEFAULT_PORT,
        ge=MIN_PORT,
        le=MAX_PORT,
        description="Port number for the web server.",
    )

    # AI integration
    ai_enabled: bool = Field(
        default=False,
        description="Toggle for optional AI-assisted metadata enrichment.",
    )
    ai_api_url: Optional[HttpUrl] = Field(
        default=None,
        description="Endpoint for AI integration services.",
    )
    ai_api_key: Optional[SecretStr] = Field(
        default=None,
        description="API key for AI integration (masked in logs).",
    )

    # Logging
    log_level: LogLevel = Field(
        default="INFO",
        description="Logging verbosity level.",
    )
    log_format: LogFormat = Field(
        default="json",
        description="Logging output format.",
    )

    @field_validator("ffmpeg_custom_args", mode="before")
    @classmethod
    def parse_custom_args(cls, value: Optional[object]) -> Sequence[str]:
        """Normalize FFmpeg custom arguments from environment inputs."""
        if value is None or value == "":
            return []
        if isinstance(value, (list, tuple)):
            return [str(item) for item in value]
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return []
            try:
                decoded = json.loads(stripped)
            except json.JSONDecodeError:
                return [part.strip() for part in stripped.split(",") if part.strip()]
            if isinstance(decoded, (list, tuple)):
                return [str(item) for item in decoded]
            return [str(decoded)]
        raise ValueError(
            "ffmpeg_custom_args must be a sequence or JSON serialisable string."
        )

    @field_validator("data_dir", "screenshot_dir", mode="before")
    @classmethod
    def expand_path(cls, value: object) -> Path:
        """Ensure path fields are converted into Path instances."""
        if isinstance(value, Path):
            return value
        if isinstance(value, str):
            return Path(value)
        raise ValueError("Path fields expect string or Path inputs.")

    @field_validator("retry_backoff")
    @classmethod
    def validate_backoff(cls, value: float) -> float:
        """
        Ensure backoff is within bounds and greater than zero.

        This hook primarily protects against misconfigured floats parsed from
        environment variables.
        """
        if value <= 0:
            raise ValueError("retry_backoff must be greater than zero.")
        return value
