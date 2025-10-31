"""Stream validation logic using ffmpeg-python."""

from __future__ import annotations

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Callable, Dict, Optional
from urllib.parse import urlparse

import ffmpeg  # type: ignore[import]

from iptv_sniffer.utils.ffmpeg import check_ffmpeg_installed

logger = logging.getLogger(__name__)


class ErrorCategory(str, Enum):
    """Categorization of validation failures."""

    NETWORK_UNREACHABLE = "network_unreachable"
    TIMEOUT = "timeout"
    NO_VIDEO_STREAM = "no_video_stream"
    UNSUPPORTED_CODEC = "unsupported_codec"
    UNSUPPORTED_PROTOCOL = "unsupported_protocol"
    MULTICAST_NOT_SUPPORTED = "multicast_not_supported"


@dataclass
class StreamValidationResult:
    """Structured result returned by stream validator."""

    url: str
    is_valid: bool
    protocol: str
    resolution: Optional[str] = None
    codec_video: Optional[str] = None
    codec_audio: Optional[str] = None
    error_category: Optional[ErrorCategory] = None
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class StreamValidator:
    """Validate IPTV streams using ffmpeg probe in a thread pool."""

    _DEFAULT_TIMEOUT = 10
    _RTP_TIMEOUT = 20

    def __init__(self, max_workers: int = 10) -> None:
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._validators: Dict[str, Callable[[str, int], StreamValidationResult]] = {
            "http": self._validate_http,
            "https": self._validate_http,
            "rtsp": self._validate_rtsp,
            "rtp": self._validate_rtp,
            "udp": self._validate_udp,
        }

    async def validate(
        self, url: str, timeout: int = _DEFAULT_TIMEOUT
    ) -> StreamValidationResult:
        """
        Validate IPTV stream referenced by URL.

        Detection is based on URL scheme and runs ffmpeg probe in a worker thread.
        """
        protocol = self._detect_protocol(url)

        if not protocol or protocol not in self._validators:
            logger.warning("Unsupported protocol for URL %s", url)
            return StreamValidationResult(
                url=url,
                protocol=protocol or "unknown",
                is_valid=False,
                error_category=ErrorCategory.UNSUPPORTED_PROTOCOL,
                error_message="Protocol not supported by stream validator.",
            )

        if not check_ffmpeg_installed():
            logger.error("FFmpeg must be installed for stream validation.")
            return StreamValidationResult(
                url=url,
                protocol=protocol,
                is_valid=False,
                error_category=ErrorCategory.UNSUPPORTED_PROTOCOL,
                error_message="FFmpeg is not installed.",
            )

        validator = self._validators[protocol]
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self._executor, validator, url, timeout)

    @staticmethod
    def _detect_protocol(url: str) -> Optional[str]:
        parsed = urlparse(url)
        return parsed.scheme.lower() if parsed.scheme else None

    def _validate_http(self, url: str, timeout: int) -> StreamValidationResult:
        return self._probe_with_ffmpeg(url, "http", timeout)

    def _validate_rtsp(self, url: str, timeout: int) -> StreamValidationResult:
        return self._probe_with_ffmpeg(
            url,
            "rtsp",
            timeout,
            options={"rtsp_transport": "tcp"},
        )

    def _validate_rtp(self, url: str, timeout: int) -> StreamValidationResult:
        probe_timeout = max(timeout, self._RTP_TIMEOUT)
        return self._probe_with_ffmpeg(
            url,
            "rtp",
            probe_timeout,
            options={
                "analyzeduration": "10M",
                "probesize": "10M",
                "rtbufsize": "2048k",
            },
        )

    def _validate_udp(self, url: str, timeout: int) -> StreamValidationResult:
        return self._probe_with_ffmpeg(
            url,
            "udp",
            timeout,
            options={
                "analyzeduration": "5M",
                "probesize": "5M",
            },
        )

    def _probe_with_ffmpeg(
        self,
        url: str,
        protocol: str,
        timeout: int,
        options: Optional[Dict[str, str]] = None,
    ) -> StreamValidationResult:
        logger.debug("Running ffmpeg probe for %s (%s)", url, protocol)
        probe_kwargs = options or {}
        try:
            probe_result = ffmpeg.probe(url, timeout=timeout, **probe_kwargs)
            return self._parse_probe_result(url, protocol, probe_result)
        except Exception as exc:
            stderr = ""
            raw_stderr = getattr(exc, "stderr", None)
            if isinstance(raw_stderr, bytes):
                stderr = raw_stderr.decode("utf-8", errors="ignore")
            elif isinstance(raw_stderr, str):
                stderr = raw_stderr
            else:
                stderr = str(exc)
            logger.warning("FFmpeg error for %s: %s", url, stderr.strip())
            return self._handle_ffmpeg_error(url, protocol, stderr)

    def _parse_probe_result(
        self,
        url: str,
        protocol: str,
        probe: Dict[str, object],
    ) -> StreamValidationResult:
        streams_data = probe.get("streams", [])
        if not isinstance(streams_data, list):
            streams_list: list = []
        else:
            streams_list = streams_data
        video_stream = next(
            (
                stream
                for stream in streams_list
                if isinstance(stream, dict) and stream.get("codec_type") == "video"
            ),
            None,
        )
        audio_stream = next(
            (
                stream
                for stream in streams_list
                if isinstance(stream, dict) and stream.get("codec_type") == "audio"
            ),
            None,
        )

        if not video_stream:
            logger.info("No video stream detected for %s", url)
            return StreamValidationResult(
                url=url,
                protocol=protocol,
                is_valid=False,
                error_category=ErrorCategory.NO_VIDEO_STREAM,
                error_message="No video stream detected.",
            )

        width = video_stream.get("width")
        height = video_stream.get("height")
        resolution = f"{width}x{height}" if width and height else None

        result = StreamValidationResult(
            url=url,
            protocol=protocol,
            is_valid=True,
            resolution=resolution,
            codec_video=video_stream.get("codec_name"),
            codec_audio=audio_stream.get("codec_name") if audio_stream else None,
        )

        logger.debug("Validation success for %s: %s", url, result)
        return result

    def _handle_ffmpeg_error(
        self,
        url: str,
        protocol: str,
        stderr: str,
    ) -> StreamValidationResult:
        category = self._categorize_error(stderr, protocol)
        return StreamValidationResult(
            url=url,
            protocol=protocol,
            is_valid=False,
            error_category=category,
            error_message=stderr.strip() or "Unknown FFmpeg error.",
        )

    @staticmethod
    def _categorize_error(stderr: str, protocol: str) -> ErrorCategory:
        stderr_lower = stderr.lower()
        if "timed out" in stderr_lower or "timeout" in stderr_lower:
            return ErrorCategory.TIMEOUT
        if any(
            keyword in stderr_lower
            for keyword in (
                "connection refused",
                "no route",
                "failed to resolve",
                "network unreachable",
            )
        ):
            return ErrorCategory.NETWORK_UNREACHABLE
        if protocol == "rtp" and "multicast" in stderr_lower:
            return ErrorCategory.MULTICAST_NOT_SUPPORTED
        if "codec" in stderr_lower and "unsupported" in stderr_lower:
            return ErrorCategory.UNSUPPORTED_CODEC
        return ErrorCategory.NETWORK_UNREACHABLE
