from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import chardet

logger = logging.getLogger(__name__)


def read_m3u_file(path: Path) -> str:
    """
    Read an M3U file handling potential non-UTF-8 encodings.

    The function first attempts to decode using UTF-8 since most playlists adopt
    it. If that fails, it leverages chardet to detect the encoding and decode
    accordingly, logging the detected encoding for observability.
    """
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raw_bytes = path.read_bytes()

        detection = chardet.detect(raw_bytes)
        encoding: Optional[str] = detection.get("encoding")
        confidence: Optional[float] = detection.get("confidence")

        if not encoding:
            logger.warning(
                "Unable to detect encoding for playlist %s; defaulting to latin-1.",
                path,
            )
            encoding = "latin-1"
            confidence = None
        else:
            logger.info(
                "Detected encoding '%s' for playlist %s (confidence=%.2f).",
                encoding,
                path,
                confidence if confidence is not None else 0.0,
            )

        try:
            return raw_bytes.decode(encoding)
        except (LookupError, UnicodeDecodeError):
            logger.error(
                "Failed decoding playlist %s using detected encoding '%s'. Falling back to latin-1.",
                path,
                encoding,
            )
            return raw_bytes.decode("latin-1", errors="replace")
