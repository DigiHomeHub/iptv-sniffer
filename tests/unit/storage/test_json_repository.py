from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List

from iptv_sniffer.channel.models import Channel, ValidationStatus
from iptv_sniffer.storage.json_repository import JSONChannelRepository


def _channel(name: str, url: str, **kwargs) -> Channel:
    return Channel(name=name, url=url, **kwargs)


class TestJSONChannelRepository(unittest.IsolatedAsyncioTestCase):
    """Unit tests for the JSON-backed channel repository."""

    def setUp(self) -> None:
        self._temp_dir = TemporaryDirectory()
        self.storage_path = Path(self._temp_dir.name) / "channels.json"
        self.repository = JSONChannelRepository(self.storage_path)

    def tearDown(self) -> None:
        self._temp_dir.cleanup()

    async def test_add_channel_creates_new_record(self) -> None:
        channel = _channel("Test Channel", "http://example.com/stream")

        saved = await self.repository.add(channel)

        self.assertEqual(saved.id, channel.id)
        stored = await self.repository.find_all()
        self.assertEqual(len(stored), 1)
        self.assertEqual(stored[0].url, channel.url)

    async def test_add_channel_updates_existing_by_url(self) -> None:
        original = _channel("Original", "http://example.com/live", manually_edited=True)
        updated = original.model_copy(
            update={
                "name": "Updated Name",
                "group": "News",
                "manually_edited": False,
            }
        )

        await self.repository.add(original)
        merged = await self.repository.add(updated)

        self.assertEqual(merged.id, original.id)
        self.assertEqual(merged.name, "Updated Name")
        self.assertTrue(merged.manually_edited)  # should preserve manual edits
        self.assertEqual(merged.created_at, original.created_at)

        stored = await self.repository.find_all()
        self.assertEqual(len(stored), 1)
        self.assertEqual(stored[0].group, "News")

    async def test_find_all_with_filters(self) -> None:
        channels: List[Channel] = [
            _channel("News", "http://example.com/news", group="News"),
            _channel(
                "Sports",
                "http://example.com/sports",
                group="Sports",
                is_online=True,
                validation_status=ValidationStatus.ONLINE,
            ),
            _channel(
                "Movies",
                "http://example.com/movies",
                group="Entertainment",
                validation_status=ValidationStatus.OFFLINE,
            ),
        ]

        for ch in channels:
            await self.repository.add(ch)

        by_group = await self.repository.find_all({"group": "Sports"})
        self.assertEqual(len(by_group), 1)
        self.assertEqual(by_group[0].name, "Sports")

        by_online = await self.repository.find_all({"is_online": True})
        self.assertEqual(len(by_online), 1)
        self.assertEqual(by_online[0].name, "Sports")

        by_status = await self.repository.find_all(
            {"validation_status": ValidationStatus.OFFLINE}
        )
        self.assertEqual(len(by_status), 1)
        self.assertEqual(by_status[0].name, "Movies")

    async def test_delete_channel_removes_from_storage(self) -> None:
        channel = _channel("Delete Me", "http://example.com/delete")
        await self.repository.add(channel)

        deleted = await self.repository.delete(channel.id)
        self.assertTrue(deleted)

        stored = await self.repository.find_all()
        self.assertEqual(stored, [])

        deleted_again = await self.repository.delete(channel.id)
        self.assertFalse(deleted_again)

    async def test_get_by_id_returns_none_for_missing(self) -> None:
        result = await self.repository.get_by_id("missing-id")
        self.assertIsNone(result)

    async def test_get_by_url_returns_channel(self) -> None:
        channel = _channel("Lookup", "http://example.com/lookup")
        await self.repository.add(channel)

        found = await self.repository.get_by_url("HTTP://example.com/lookup")

        self.assertIsNotNone(found)
        assert found is not None  # for mypy
        self.assertEqual(found.id, channel.id)

    async def test_repository_survives_recreation(self) -> None:
        channel = _channel("Persisted", "http://example.com/persist")
        await self.repository.add(channel)

        repo_again = JSONChannelRepository(self.storage_path)
        found = await repo_again.get_by_id(channel.id)

        self.assertIsNotNone(found)
        assert found is not None
        self.assertEqual(found.id, channel.id)

    async def test_missing_file_returns_empty_list(self) -> None:
        self.storage_path.unlink(missing_ok=True)
        channels = await self.repository.find_all()
        self.assertEqual(channels, [])

    async def test_corrupted_file_returns_empty_list(self) -> None:
        self.storage_path.write_text("not json", encoding="utf-8")
        channels = await self.repository.find_all()
        self.assertEqual(channels, [])

    async def test_non_list_payload_and_invalid_entries(self) -> None:
        self.storage_path.write_text("{}", encoding="utf-8")
        self.assertEqual(await self.repository.find_all(), [])

        malformed_payload = json.dumps(
            [
                123,
                {"name": "No URL"},
                {
                    "id": "custom-id",
                    "name": "Valid",
                    "url": "http://example.com/ok",
                },
            ],
            ensure_ascii=False,
        )
        self.storage_path.write_text(malformed_payload, encoding="utf-8")

        channels = await self.repository.find_all({"manually_edited": False})

        self.assertEqual(len(channels), 1)
        self.assertEqual(channels[0].id, "custom-id")


if __name__ == "__main__":
    unittest.main()
