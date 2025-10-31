"""Async screenshot capture from IPTV streams using ffmpeg-python."""

from __future__ import annotations

import asyncio
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, Optional

import ffmpeg  # type: ignore[import]

from iptv_sniffer.utils.ffmpeg import FFmpegNotFoundError, check_ffmpeg_installed

logger = logging.getLogger(__name__)

_EXECUTOR = ThreadPoolExecutor(max_workers=4)
_MAX_TIMEOUT = 60
_DEFAULT_TIMEOUT = 10
_FRAME_SEEK_SECONDS = 5


def _sanitize_output_path(path: Path) -> Path:
    expanded = path.expanduser()
    if expanded.suffix.lower() != ".png":
        expanded = expanded.with_suffix(".png")
    parent = expanded.parent
    parent.mkdir(parents=True, exist_ok=True)
    return expanded.resolve()


def _build_hwaccel_options(hwaccel: Optional[str]) -> Dict[str, str]:
    if not hwaccel:
        return {}

    hwaccel_lower = hwaccel.lower()
    if hwaccel_lower == "vaapi":
        return {
            "hwaccel": "vaapi",
            "hwaccel_device": os.environ.get(
                "FFMPEG_VAAPI_DEVICE", "/dev/dri/renderD128"
            ),
        }
    if hwaccel_lower == "cuda":
        return {"hwaccel": "cuda"}
    logger.warning(
        "Unknown hardware acceleration option '%s'. Falling back to software.", hwaccel
    )
    return {}


def _run_ffmpeg(
    url: str,
    output_path: Path,
    timeout: int,
    hwaccel: Optional[str],
) -> None:
    input_kwargs: Dict[str, object] = {"ss": _FRAME_SEEK_SECONDS}
    input_kwargs.update(_build_hwaccel_options(hwaccel))
    input_kwargs.setdefault("stimeout", int(timeout * 1_000_000))

    stream = ffmpeg.input(url, **input_kwargs)
    output_kwargs = {
        "vframes": 1,
        "format": "image2",
        "vcodec": "png",
    }
    output = stream.output(str(output_path), **output_kwargs)
    ffmpeg.run(
        output,
        capture_stdout=True,
        capture_stderr=True,
        overwrite_output=True,
    )


def _sync_capture_screenshot(
    url: str,
    output_path: Path,
    timeout: int,
    hwaccel: Optional[str],
) -> None:
    try:
        _run_ffmpeg(url, output_path, timeout, hwaccel)
    except Exception as exc:
        if hwaccel:
            logger.warning(
                "Hardware acceleration '%s' failed for %s: %s. Retrying with software decoding.",
                hwaccel,
                url,
                exc,
            )
            _run_ffmpeg(url, output_path, timeout, None)
        else:
            raise


async def capture_screenshot(
    url: str,
    output_path: Path,
    timeout: int = _DEFAULT_TIMEOUT,
    hwaccel: Optional[str] = None,
) -> None:
    """
    Capture a single video frame from the stream and store it as PNG.

    Args:
        url: Stream URL.
        output_path: Destination PNG path.
        timeout: Timeout in seconds (1-60).
        hwaccel: Optional hardware acceleration hint ("vaapi" or "cuda").

    Raises:
        ValueError: If timeout is outside allowed range.
        FFmpegNotFoundError: If FFmpeg is not installed.
        asyncio.TimeoutError: If capture exceeds timeout.
        ffmpeg.Error: If FFmpeg execution fails.
    """

    if timeout <= 0 or timeout > _MAX_TIMEOUT:
        raise ValueError(f"timeout must be between 1 and {_MAX_TIMEOUT} seconds.")

    if not check_ffmpeg_installed():
        raise FFmpegNotFoundError("FFmpeg is required for screenshot capture.")

    safe_path = _sanitize_output_path(output_path)
    loop = asyncio.get_running_loop()

    logger.debug(
        "Capturing screenshot from %s -> %s (timeout=%s, hwaccel=%s)",
        url,
        safe_path,
        timeout,
        hwaccel,
    )
    await asyncio.wait_for(
        loop.run_in_executor(
            _EXECUTOR,
            _sync_capture_screenshot,
            url,
            safe_path,
            timeout,
            hwaccel,
        ),
        timeout=timeout,
    )
    logger.info("Screenshot saved to %s", safe_path)


__all__ = ["capture_screenshot"]
