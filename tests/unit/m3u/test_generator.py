import unittest
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from iptv_sniffer.channel.models import Channel, ValidationStatus
from iptv_sniffer.m3u.generator import M3UGenerator


class TestM3UGenerator(unittest.TestCase):
    def setUp(self) -> None:
        self.generator = M3UGenerator()

    def _base_channel(self, **overrides: Any) -> Channel:
        now = datetime.now(tz=timezone.utc)
        data = {
            "id": str(uuid4()),
            "name": "News HD",
            "url": "http://example.com/news",
            "tvg_id": "NEWS123",
            "tvg_logo": "http://logo.png",
            "group": "News",
            "is_online": True,
            "validation_status": ValidationStatus.ONLINE,
            "manually_edited": False,
            "created_at": now,
            "updated_at": now,
        }
        data.update(overrides)
        return Channel(**data)

    def test_generate_includes_extended_attributes(self) -> None:
        channel = self._base_channel()
        content = self.generator.generate([channel])

        lines = content.splitlines()

        self.assertEqual(lines[0], "#EXTM3U")
        self.assertEqual(
            lines[1],
            '#EXTINF:-1 tvg-id="NEWS123" tvg-name="News HD" tvg-logo="http://logo.png" group-title="News",News HD',
        )
        self.assertEqual(lines[2], "#EXTGRP:News")
        self.assertEqual(lines[3], "http://example.com/news")

    def test_generate_handles_missing_optional_fields(self) -> None:
        channel = self._base_channel(tvg_logo=None, group=None, tvg_id=None)
        content = self.generator.generate([channel])

        lines = content.splitlines()

        self.assertEqual(lines[1], '#EXTINF:-1 tvg-name="News HD",News HD')
        self.assertTrue(all(not line.startswith("#EXTGRP") for line in lines[2:]))

    def test_generate_multiple_channels(self) -> None:
        channels = [
            self._base_channel(name="News HD", url="http://example.com/news"),
            self._base_channel(
                name="Sports Live",
                url="http://example.com/sports",
                tvg_id="SPORTS123",
                group="Sports",
            ),
        ]
        content = self.generator.generate(channels)

        lines = content.splitlines()
        self.assertEqual(content.count("#EXTINF"), 2)
        self.assertIn("#EXTGRP:Sports", lines)
        self.assertIn("http://example.com/sports", lines)

    def test_generate_escapes_quotes_in_names(self) -> None:
        channel = self._base_channel(
            name='Movie "Premiere"', tvg_id=None, tvg_logo=None, group=None
        )
        content = self.generator.generate([channel])

        extinf_line = content.splitlines()[1]

        self.assertIn('tvg-name="Movie \\"Premiere\\""', extinf_line)
        self.assertIn(',Movie \\"Premiere\\"', extinf_line)


if __name__ == "__main__":
    unittest.main()
