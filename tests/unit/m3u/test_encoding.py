import logging
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from iptv_sniffer.m3u.encoding import read_m3u_file


class TestM3UEncoding(unittest.TestCase):
    def test_read_utf8_file(self) -> None:
        with tempfile.NamedTemporaryFile("w+", encoding="utf-8", delete=False) as tmp:
            tmp.write("#EXTM3U\n#EXTINF:-1,Channel UTF-8\nhttp://example.com\n")
            tmp_path = Path(tmp.name)

        try:
            content = read_m3u_file(tmp_path)
            self.assertIn("Channel UTF-8", content)
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_fallback_to_detected_encoding(self) -> None:
        text = "#EXTM3U\n#EXTINF:-1,国际频道\nhttp://example.com\n"
        encoded = text.encode("gb2312")

        with tempfile.NamedTemporaryFile("wb", delete=False) as tmp:
            tmp.write(encoded)
            tmp_path = Path(tmp.name)

        try:
            with patch(
                "iptv_sniffer.m3u.encoding.chardet.detect",
                return_value={"encoding": "gb2312", "confidence": 0.92},
            ):
                content = read_m3u_file(tmp_path)
            self.assertIn("国际频道", content)
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_logs_detected_encoding(self) -> None:
        text = "#EXTM3U\n#EXTINF:-1,Internación\nhttp://example.com\n"
        encoded = text.encode("iso-8859-1")

        with tempfile.NamedTemporaryFile("wb", delete=False) as tmp:
            tmp.write(encoded)
            tmp_path = Path(tmp.name)

        try:
            with patch(
                "iptv_sniffer.m3u.encoding.chardet.detect",
                return_value={"encoding": "iso-8859-1", "confidence": 0.66},
            ):
                with self.assertLogs(
                    "iptv_sniffer.m3u.encoding", level=logging.INFO
                ) as captured:
                    _ = read_m3u_file(tmp_path)

            self.assertTrue(
                any("Detected encoding" in message for message in captured.output),
                "Expected detected encoding log entry.",
            )
        finally:
            tmp_path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
