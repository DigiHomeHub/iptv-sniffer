from __future__ import annotations

import logging
import re
from typing import Dict, List, Optional, Tuple

from .models import M3UChannel, M3UPlaylist

logger = logging.getLogger(__name__)


class M3UParser:
    """Parser for M3U/M3U8 playlists with extended attribute support."""

    _ATTRIBUTE_PATTERN = re.compile(r'(?P<key>[a-zA-Z0-9\-]+)="(?P<value>[^"]*)"')
    _ATTRIBUTE_KEY_MAP: Dict[str, str] = {
        "tvg-id": "tvg_id",
        "tvg-name": "tvg_name",
        "tvg-logo": "tvg_logo",
        "group-title": "group_title",
    }
    _EXTINF_PREFIX = "#EXTINF"
    _EXTGRP_PREFIX = "#EXTGRP"

    def parse(self, content: str) -> M3UPlaylist:
        """
        Parse raw M3U content and return a playlist representation.

        Args:
            content: Raw playlist text.

        Returns:
            Parsed playlist containing channel entries.
        """
        if not content:
            return M3UPlaylist()

        lines = content.splitlines()
        channels: List[M3UChannel] = []

        index = 0
        total_lines = len(lines)

        while index < total_lines:
            line = lines[index].strip()
            if not line:
                index += 1
                continue

            if line.startswith(self._EXTINF_PREFIX):
                parsed_attrs = self._parse_extinf(line)
                raw_name = parsed_attrs.pop("name", None)
                name = raw_name.strip() if isinstance(raw_name, str) else ""

                if not name:
                    logger.warning(
                        "Skipping EXTINF entry with missing channel name: %s", line
                    )
                    index += 1
                    continue

                url, group_from_extgrp, next_index = self._consume_metadata(
                    lines, index + 1
                )
                if not url:
                    logger.warning(
                        "Skipping channel '%s' due to missing stream URL.", name
                    )
                    index = next_index
                    continue

                group_title_attr = parsed_attrs.pop("group_title", None)
                group_title = group_title_attr or group_from_extgrp

                channel = M3UChannel(
                    name=name,
                    url=url,
                    tvg_id=parsed_attrs.get("tvg_id"),
                    tvg_name=parsed_attrs.get("tvg_name"),
                    tvg_logo=parsed_attrs.get("tvg_logo"),
                    group_title=group_title or None,
                )
                channels.append(channel)

                index = next_index
                continue

            index += 1

        return M3UPlaylist(channels=channels)

    def _parse_extinf(self, line: str) -> Dict[str, Optional[str]]:
        """Extract attributes from an EXTINF line."""
        attributes: Dict[str, Optional[str]] = {}

        for match in self._ATTRIBUTE_PATTERN.finditer(line):
            raw_key = match.group("key").strip().lower()
            value = match.group("value").strip()
            mapped_key = self._ATTRIBUTE_KEY_MAP.get(raw_key)
            if mapped_key:
                attributes[mapped_key] = value or None

        if "," in line:
            attributes["name"] = line.rsplit(",", 1)[-1].strip()
        else:
            attributes["name"] = ""

        return attributes

    def _consume_metadata(
        self,
        lines: List[str],
        start_index: int,
    ) -> Tuple[Optional[str], Optional[str], int]:
        """
        Consume metadata lines following an EXTINF directive to locate the URL.

        Returns:
            Tuple of (url, group_from_extgrp, next_index).
        """
        group_from_extgrp: Optional[str] = None
        index = start_index
        total_lines = len(lines)

        while index < total_lines:
            raw_line = lines[index]
            stripped = raw_line.strip()

            if not stripped:
                index += 1
                continue

            if stripped.startswith(self._EXTINF_PREFIX):
                return None, group_from_extgrp, index

            if stripped.startswith("#"):
                if stripped.startswith(self._EXTGRP_PREFIX):
                    group_value = (
                        stripped[len(self._EXTGRP_PREFIX) :].lstrip(":").strip()
                    )
                    if group_value:
                        group_from_extgrp = group_value
                index += 1
                continue

            return stripped, group_from_extgrp, index + 1

        return None, group_from_extgrp, total_lines
