"""JSON-backed channel repository with async interface."""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Dict, List, Optional, Sequence

from iptv_sniffer.channel.models import Channel

logger = logging.getLogger(__name__)


class JSONChannelRepository:
    """Persist channels to a JSON file while exposing an async API."""

    def __init__(self, file_path: Path, *, encoding: str = "utf-8") -> None:
        self._file_path = file_path
        self._encoding = encoding
        self._lock = asyncio.Lock()
        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self._file_path.exists():
            self._file_path.write_text("[]\n", encoding=self._encoding)

    async def add(self, channel: Channel) -> Channel:
        """
        Add a channel or update an existing entry matched by URL.

        Deduplication follows Design.md Section 7: the first channel discovered
        for a URL controls the primary key and timestamps. Subsequent updates
        preserve the `manually_edited` flag to avoid erasing user changes.
        """
        async with self._lock:
            channels = await self._read_channels()
            normalized_url = self._normalize_url(channel.url)

            for index, existing in enumerate(channels):
                if self._normalize_url(existing.url) == normalized_url:
                    merged = self._merge_channels(existing, channel)
                    channels[index] = merged
                    await self._write_channels(channels)
                    logger.info(
                        "Channel updated",
                        extra={
                            "channel_id": merged.id,
                            "url": merged.url,
                            "repository": str(self._file_path),
                        },
                    )
                    return merged

            channels.append(channel)
            await self._write_channels(channels)
            logger.info(
                "Channel added",
                extra={
                    "channel_id": channel.id,
                    "url": channel.url,
                    "repository": str(self._file_path),
                },
            )
            return channel

    async def get_by_id(self, channel_id: str) -> Optional[Channel]:
        """Return a channel by its UUID identifier."""
        channels = await self._read_channels()
        for channel in channels:
            if channel.id == channel_id:
                return channel
        return None

    async def get_by_url(self, url: str) -> Optional[Channel]:
        """Return a channel using normalized URL matching."""
        channels = await self._read_channels()
        normalized = self._normalize_url(url)
        for channel in channels:
            if self._normalize_url(channel.url) == normalized:
                return channel
        return None

    async def find_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Channel]:
        """
        Return all channels optionally filtered by attributes.

        Supported filters:
            * group (str)
            * is_online (bool)
            * validation_status (str)
            * manually_edited (bool)
        """
        channels = await self._read_channels()
        if not filters:
            return channels

        filters_copy = dict(filters)
        return [
            channel
            for channel in channels
            if self._matches_filters(channel, filters_copy)
        ]

    async def delete(self, channel_id: str) -> bool:
        """Delete a channel by ID. Returns True if a record was removed."""
        async with self._lock:
            channels = await self._read_channels()
            remaining = [channel for channel in channels if channel.id != channel_id]
            if len(remaining) == len(channels):
                return False
            await self._write_channels(remaining)
            logger.info(
                "Channel deleted",
                extra={
                    "channel_id": channel_id,
                    "repository": str(self._file_path),
                },
            )
            return True

    async def _read_channels(self) -> List[Channel]:
        return await asyncio.to_thread(self._read_channels_sync)

    async def _write_channels(self, channels: Sequence[Channel]) -> None:
        await asyncio.to_thread(self._write_channels_sync, list(channels))

    def _read_channels_sync(self) -> List[Channel]:
        try:
            raw = self._file_path.read_text(encoding=self._encoding)
        except FileNotFoundError:
            logger.warning(
                "Channel repository missing file; initializing empty list",
                extra={"repository": str(self._file_path)},
            )
            return []

        if not raw.strip():
            return []

        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            logger.error(
                "Corrupted channel repository JSON",
                extra={"repository": str(self._file_path), "error": str(exc)},
            )
            return []

        if not isinstance(payload, list):
            logger.error(
                "Unexpected JSON payload type",
                extra={
                    "repository": str(self._file_path),
                    "payload_type": type(payload).__name__,
                },
            )
            return []

        channels: List[Channel] = []
        for item in payload:
            if not isinstance(item, dict):
                logger.warning(
                    "Skipping malformed channel entry",
                    extra={"repository": str(self._file_path), "entry": item},
                )
                continue
            try:
                channels.append(Channel(**item))
            except ValueError as exc:
                logger.warning(
                    "Invalid channel entry encountered",
                    extra={"repository": str(self._file_path), "error": str(exc)},
                )
        return channels

    def _write_channels_sync(self, channels: Sequence[Channel]) -> None:
        serialized = [channel.model_dump(mode="json") for channel in channels]
        json_payload = json.dumps(serialized, ensure_ascii=False, indent=2)

        with NamedTemporaryFile(
            "w",
            delete=False,
            encoding=self._encoding,
            dir=str(self._file_path.parent),
        ) as tmp_file:
            tmp_file.write(json_payload)
            tmp_file.flush()
            temp_name = tmp_file.name

        Path(temp_name).replace(self._file_path)

    @staticmethod
    def _normalize_url(url: str) -> str:
        return url.strip().lower()

    @staticmethod
    def _merge_channels(original: Channel, incoming: Channel) -> Channel:
        merged_data = original.model_dump()
        incoming_data = incoming.model_dump()
        merged_data.update(incoming_data)
        merged_data["id"] = original.id
        merged_data["created_at"] = original.created_at
        merged_data["manually_edited"] = (
            original.manually_edited or incoming.manually_edited
        )
        return Channel(**merged_data)

    @staticmethod
    def _matches_filters(channel: Channel, filters: Dict[str, Any]) -> bool:
        for key, expected in filters.items():
            if expected is None:
                continue
            if key == "group" and channel.group != expected:
                return False
            if key == "is_online" and channel.is_online != expected:
                return False
            if key == "validation_status" and channel.validation_status != expected:
                return False
            if key == "manually_edited" and channel.manually_edited != expected:
                return False
        return True
