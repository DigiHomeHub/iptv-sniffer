import unittest
from datetime import datetime, timezone
from typing import List
from uuid import UUID

from pydantic import ValidationError

from iptv_sniffer.channel.models import Channel, ValidationStatus


class TestChannelModel(unittest.TestCase):
    """Test suite for Channel Pydantic model."""

    def test_channel_creation_with_minimal_fields(self) -> None:
        """Channel should be instantiable with only name and url."""
        channel = Channel(name="Demo Channel", url="http://example.com/stream")

        # Ensure UUID auto-generation occurs
        UUID(channel.id)

        self.assertEqual(channel.name, "Demo Channel")
        self.assertEqual(channel.url, "http://example.com/stream")
        self.assertEqual(channel.validation_status, ValidationStatus.UNKNOWN)
        self.assertFalse(channel.manually_edited)
        self.assertFalse(channel.is_online)
        self.assertIsNone(channel.last_validated)
        self.assertIsNone(channel.tvg_id)
        self.assertIsNone(channel.tvg_logo)
        self.assertIsNone(channel.group)
        self.assertIsNone(channel.resolution)
        self.assertIsNone(channel.screenshot_path)

    def test_channel_url_validation_rejects_invalid_scheme(self) -> None:
        """Unsupported protocols should raise a validation error."""
        with self.assertRaises(ValidationError) as context:
            Channel(name="Invalid Channel", url="ftp://example.com/stream")

        message = str(context.exception)
        self.assertIn("Unsupported protocol", message)
        self.assertIn("ftp", message)

    def test_channel_url_supports_multiple_protocols(self) -> None:
        """Ensure all IPTV-supported protocols are accepted."""
        urls: List[str] = [
            "http://example.com/stream",
            "https://secure.example.com/stream",
            "rtp://239.0.0.1:5000",
            "rtsp://example.com/stream",
            "udp://239.0.0.1:1234",
            "mms://example.com/channel",
        ]

        for url in urls:
            channel = Channel(name="Protocol Channel", url=url)
            self.assertEqual(channel.url, url)

    def test_channel_validation_status_defaults_to_unknown(self) -> None:
        """New channels start with UNKNOWN validation status."""
        channel = Channel(name="Status Channel", url="http://example.com/live")
        self.assertEqual(channel.validation_status, ValidationStatus.UNKNOWN)

    def test_channel_timestamps_auto_generated(self) -> None:
        """created_at and updated_at should default to current UTC timestamps."""
        before = datetime.now(tz=timezone.utc)
        channel = Channel(name="Timestamp Channel", url="http://example.com/live")
        after = datetime.now(tz=timezone.utc)

        self.assertLessEqual(before, channel.created_at)
        self.assertLessEqual(channel.created_at, after)
        self.assertLessEqual(before, channel.updated_at)
        self.assertLessEqual(channel.updated_at, after)
        self.assertEqual(channel.created_at.tzinfo, timezone.utc)
        self.assertEqual(channel.updated_at.tzinfo, timezone.utc)

    def test_validation_status_enum_members(self) -> None:
        """ValidationStatus enum should expose the full lifecycle."""
        expected = {
            ValidationStatus.UNKNOWN,
            ValidationStatus.VALIDATING,
            ValidationStatus.ONLINE,
            ValidationStatus.OFFLINE,
            ValidationStatus.ERROR,
        }
        self.assertEqual(set(ValidationStatus), expected)


if __name__ == "__main__":
    unittest.main()
