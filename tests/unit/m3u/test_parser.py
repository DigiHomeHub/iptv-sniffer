import unittest

from iptv_sniffer.m3u.parser import M3UParser


class TestM3UParser(unittest.TestCase):
    def setUp(self) -> None:
        self.parser = M3UParser()

    def test_parse_extended_attributes(self) -> None:
        content = (
            "#EXTM3U\n"
            '#EXTINF:-1 tvg-id="123" tvg-name="News HD" tvg-logo="http://logo.png" '
            'group-title="News",News Channel HD\n'
            "http://example.com/stream1\n"
            '#EXTINF:-1 tvg-id="456" group-title="Sports",Sports Live\n'
            "http://example.com/stream2\n"
        )

        playlist = self.parser.parse(content)

        self.assertEqual(len(playlist.channels), 2)

        first = playlist.channels[0]
        self.assertEqual(first.name, "News Channel HD")
        self.assertEqual(first.url, "http://example.com/stream1")
        self.assertEqual(first.tvg_id, "123")
        self.assertEqual(first.tvg_name, "News HD")
        self.assertEqual(first.tvg_logo, "http://logo.png")
        self.assertEqual(first.group_title, "News")

        second = playlist.channels[1]
        self.assertEqual(second.name, "Sports Live")
        self.assertEqual(second.group_title, "Sports")
        self.assertIsNone(second.tvg_name)

    def test_parse_extgrp_fallback(self) -> None:
        content = (
            "#EXTM3U\n"
            '#EXTINF:-1 tvg-id="789",Variety Show\n'
            "#EXTGRP:Variety\n"
            "http://example.com/variety\n"
        )

        playlist = self.parser.parse(content)

        self.assertEqual(len(playlist.channels), 1)
        channel = playlist.channels[0]
        self.assertEqual(channel.group_title, "Variety")

    def test_parse_skips_malformed_entries(self) -> None:
        content = (
            "#EXTM3U\n"
            "#EXTINF:-1,Valid Channel\n"
            "http://example.com/valid\n"
            '#EXTINF:-1 tvg-id="bad",Missing URL\n'
            "#EXTINF:-1,Whitespace URL\n"
            "   \n"
        )

        playlist = self.parser.parse(content)

        self.assertEqual(len(playlist.channels), 1)
        self.assertEqual(playlist.channels[0].name, "Valid Channel")
        self.assertEqual(playlist.channels[0].url, "http://example.com/valid")


if __name__ == "__main__":
    unittest.main()
