from __future__ import annotations

from typing import Iterable, List, Optional

from iptv_sniffer.channel.models import Channel


class M3UGenerator:
    """
    Generate M3U/M3U8 playlists from channel definitions.

    This implementation mirrors the attribute support used by popular players by
    including extended fields such as tvg-id, tvg-name, tvg-logo, and group-title.
    Quotes within attribute values are escaped to maintain valid M3U syntax.
    """

    def generate(self, channels: Iterable[Channel]) -> str:
        """
        Generate M3U content for the provided channels.

        Args:
            channels: Iterable of Channel models to serialize.

        Returns:
            A string containing the playlist in M3U format.
        """
        lines: List[str] = ["#EXTM3U"]

        for channel in channels:
            lines.extend(self._serialize_channel(channel))

        return "\n".join(lines)

    def _serialize_channel(self, channel: Channel) -> List[str]:
        extinf_parts: List[str] = ["#EXTINF:-1"]

        self._append_attribute(extinf_parts, "tvg-id", channel.tvg_id)

        tvg_name: Optional[str] = getattr(channel, "tvg_name", None)  # type: ignore[attr-defined]
        self._append_attribute(extinf_parts, "tvg-name", tvg_name or channel.name)
        self._append_attribute(extinf_parts, "tvg-logo", channel.tvg_logo)
        self._append_attribute(extinf_parts, "group-title", channel.group)

        escaped_name = self._escape_text(channel.name)
        metadata_line = f"{' '.join(extinf_parts)},{escaped_name}"

        channel_lines = [metadata_line]
        if channel.group:
            channel_lines.append(f"#EXTGRP:{self._escape_text(channel.group)}")
        channel_lines.append(str(channel.url))
        return channel_lines

    @staticmethod
    def _format_attribute(key: str, value: str) -> str:
        return f'{key}="{M3UGenerator._escape_text(value)}"'

    @staticmethod
    def _escape_text(value: str) -> str:
        return value.replace('"', '\\"').replace("\n", " ").strip()

    @staticmethod
    def _append_attribute(container: List[str], key: str, value: Optional[str]) -> None:
        if value:
            container.append(M3UGenerator._format_attribute(key, value))
