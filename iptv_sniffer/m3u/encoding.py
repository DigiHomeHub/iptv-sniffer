from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable, Optional, Tuple

import chardet

logger = logging.getLogger(__name__)

CJK_RANGES: Tuple[Tuple[int, int], ...] = (
    (0x3400, 0x4DBF),  # Extension A
    (0x4E00, 0x9FFF),  # Unified ideographs
    (0x20000, 0x2A6DF),  # Extension B
)


def detect_encoding(raw_bytes: bytes) -> str:
    """Detect best-effort encoding for M3U byte content."""
    if not raw_bytes:
        return "utf-8"

    detection = chardet.detect(raw_bytes)
    encoding: Optional[str] = detection.get("encoding")
    confidence: Optional[float] = detection.get("confidence")

    if encoding:
        logger.info(
            "Detected encoding '%s' (confidence=%.2f).",
            encoding,
            confidence if confidence is not None else 0.0,
        )
        return encoding

    logger.warning("Unable to detect encoding; defaulting to latin-1.")
    return "latin-1"


def _contains_cjk_characters(text: str) -> bool:
    """Return True when the decoded text includes common CJK characters."""
    for char in text:
        codepoint = ord(char)
        for lower, upper in CJK_RANGES:
            if lower <= codepoint <= upper:
                return True
    return False


def decode_m3u_bytes(raw_bytes: bytes) -> str:
    """
    Decode raw playlist bytes into text using heuristics for common encodings.

    The function prioritises UTF-8, then leverages chardet detection and falls
    back through a curated list of encodings known to be used for IPTV playlists.
    CJK (Chinese-Japanese-Korean) characters are used as a heuristic to pick the
    most suitable decoding when multiple options succeed.
    """
    if not raw_bytes:
        return ""

    detected = detect_encoding(raw_bytes)
    candidates: Iterable[str] = [
        "utf-8",
        detected,
        "gb18030",
        "gbk",
        "gb2312",
        "big5",
        "latin-1",
    ]

    seen: set[str] = set()
    best_guess: Optional[Tuple[str, str]] = None

    for candidate in candidates:
        if not candidate:
            continue
        normalized = candidate.lower()
        if normalized in seen:
            continue
        seen.add(normalized)

        try:
            decoded = raw_bytes.decode(candidate)
            used_encoding = candidate
        except LookupError:
            try:
                decoded = raw_bytes.decode(normalized)
                used_encoding = normalized
            except (LookupError, UnicodeDecodeError):
                continue
        except UnicodeDecodeError:
            continue

        if normalized == "utf-8":
            logger.info("Decoded playlist using UTF-8 encoding.")
            return decoded

        if _contains_cjk_characters(decoded):
            logger.info("Decoded playlist using %s (CJK heuristic).", used_encoding)
            return decoded

        if best_guess is None:
            best_guess = (decoded, used_encoding)

    if best_guess is not None:
        decoded, encoding = best_guess
        logger.info("Decoded playlist using fallback encoding %s.", encoding)
        return decoded

    fallback = raw_bytes.decode("latin-1", errors="replace")
    logger.info("Decoded playlist using ultimate latin-1 fallback with replacement.")
    return fallback


def read_m3u_file(path: Path) -> str:
    """
    Read an M3U file handling potential non-UTF-8 encodings.

    The function first attempts to decode using UTF-8 since most playlists adopt
    it. If that fails, it leverages chardet to detect the encoding and decode
    accordingly, logging the detected encoding for observability.
    """
    raw_bytes = path.read_bytes()
    return decode_m3u_bytes(raw_bytes)
