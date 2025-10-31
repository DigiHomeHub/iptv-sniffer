"""Pydantic models representing IPTV channels and validation lifecycle."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import ClassVar, Optional, Set, Union
from urllib.parse import urlparse
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ValidationStatus(str, Enum):
    """Lifecycle states for channel validation."""

    UNKNOWN = "unknown"
    VALIDATING = "validating"
    ONLINE = "online"
    OFFLINE = "offline"
    ERROR = "error"


class Channel(BaseModel):
    """
    IPTV channel model with multi-protocol stream support.

    Fields default to sensible values to support automated discovery workflows
    while preserving user edits through the :attr:`manually_edited` flag.
    All timestamp fields are stored in UTC.
    """

    SUPPORTED_PROTOCOLS: ClassVar[Set[str]] = {
        "http",
        "https",
        "rtp",
        "rtsp",
        "udp",
        "mms",
    }

    model_config = ConfigDict(
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    url: str
    tvg_id: Optional[str] = None
    tvg_logo: Optional[str] = None
    group: Optional[str] = None
    resolution: Optional[str] = None
    is_online: bool = False
    validation_status: ValidationStatus = Field(default=ValidationStatus.UNKNOWN)
    last_validated: Optional[datetime] = None
    screenshot_path: Optional[str] = None
    manually_edited: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(tz=timezone.utc))

    @field_validator("url")
    def validate_stream_url(cls, value: str) -> str:
        """Ensure channel URLs use supported IPTV protocols."""
        parsed = urlparse(value)
        scheme = parsed.scheme.lower()

        if scheme not in cls.SUPPORTED_PROTOCOLS:
            supported = ", ".join(sorted(cls.SUPPORTED_PROTOCOLS))
            raise ValueError(
                f"Unsupported protocol: {parsed.scheme or 'missing'}. "
                f"Supported protocols: {supported}"
            )

        if not parsed.netloc:
            raise ValueError("URL must include host information.")

        return value

    @field_validator("last_validated", mode="before")
    def enforce_timezone(
        cls, value: Optional[Union[datetime, str]]
    ) -> Optional[datetime]:
        """Ensure optional datetime fields are timezone aware."""
        if value is None:
            return None
        coerced = cls._coerce_datetime(value)
        return cls._normalize_timezone(coerced)

    @field_validator("created_at", "updated_at", mode="before")
    def default_to_utc_now(cls, value: Optional[Union[datetime, str]]) -> datetime:
        """Apply UTC timezone to created/updated timestamps when missing."""
        if value is None:
            return datetime.now(tz=timezone.utc)
        coerced = cls._coerce_datetime(value)
        return cls._normalize_timezone(coerced)

    @staticmethod
    def _coerce_datetime(value: Union[datetime, str]) -> datetime:
        """Convert supported input types to datetime."""
        if isinstance(value, datetime):
            return value
        sanitized = value.strip()
        if sanitized.endswith("Z"):
            sanitized = sanitized[:-1] + "+00:00"
        try:
            return datetime.fromisoformat(sanitized)
        except ValueError as ex:
            raise ValueError(f"Invalid datetime format: {value}") from ex

    @staticmethod
    def _normalize_timezone(value: datetime) -> datetime:
        """Ensure datetime is timezone-aware and normalized to UTC."""
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
