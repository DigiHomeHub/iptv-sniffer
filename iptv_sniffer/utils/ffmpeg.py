"""FFmpeg availability and version detection utilities."""

from __future__ import annotations

import logging
import shutil
import subprocess
import sys
from typing import Optional

logger = logging.getLogger(__name__)


class FFmpegNotFoundError(RuntimeError):
    """Raised when FFmpeg is required but not installed."""


def check_ffmpeg_installed(raise_on_missing: bool = False) -> bool:
    """
    Check if FFmpeg is available on the system PATH.

    Args:
        raise_on_missing: When True, raise FFmpegNotFoundError if FFmpeg is not
            detected.

    Returns:
        True when FFmpeg is found, False otherwise.

    Raises:
        FFmpegNotFoundError: If FFmpeg is missing and raise_on_missing is True.
    """
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        logger.debug("FFmpeg detected at %s", ffmpeg_path)
        return True

    logger.warning("FFmpeg executable not found on system PATH.")
    if raise_on_missing:
        instructions = get_install_instructions()
        message = (
            "FFmpeg is required but was not found on your PATH.\n"
            f"Install FFmpeg using:\n  {instructions}"
        )
        logger.error(message)
        raise FFmpegNotFoundError(message)
    return False


def get_ffmpeg_version() -> Optional[str]:
    """
    Retrieve the FFmpeg version string, if available.

    Returns:
        The first line of `ffmpeg -version` output, or None if FFmpeg is not
        installed or the command fails.
    """
    if not check_ffmpeg_installed():
        return None

    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError, ValueError) as exc:
        logger.error("Failed to execute 'ffmpeg -version': %s", exc)
        return None

    if result.returncode != 0:
        logger.error(
            "ffmpeg -version exited with code %s: %s",
            result.returncode,
            result.stderr.strip(),
        )
        return None

    first_line = result.stdout.splitlines()[0] if result.stdout else ""
    if not first_line:
        logger.warning("No version information returned by ffmpeg.")
        return None
    return first_line.strip()


def get_install_instructions() -> str:
    """
    Provide platform-specific instructions for installing FFmpeg.

    Returns:
        A command string or guidance suitable for the current platform.
    """
    platform = sys.platform
    if platform.startswith("linux"):
        return "sudo apt-get update && sudo apt-get install -y ffmpeg libavcodec-extra"
    if platform == "darwin":
        return "brew install ffmpeg"
    if platform.startswith(("win32", "cygwin")):
        return "choco install ffmpeg"
    return "See https://ffmpeg.org/download.html for installation instructions."


__all__ = [
    "FFmpegNotFoundError",
    "check_ffmpeg_installed",
    "get_ffmpeg_version",
    "get_install_instructions",
]
