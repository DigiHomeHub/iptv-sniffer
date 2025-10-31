from __future__ import annotations

import unittest
from typing import Any, Dict
from unittest.mock import patch

from iptv_sniffer.scanner.validator import ErrorCategory, StreamValidator


class DummyFFmpegError(Exception):
    """Replacement for ffmpeg.Error when mocking."""

    def __init__(self, stderr: bytes):
        super().__init__("ffmpeg error")
        self.stderr = stderr


def _make_probe_streams(video: bool = True, audio: bool = True) -> Dict[str, Any]:
    streams = []
    if video:
        streams.append(
            {
                "codec_type": "video",
                "codec_name": "h264",
                "width": 1920,
                "height": 1080,
            }
        )
    if audio:
        streams.append(
            {
                "codec_type": "audio",
                "codec_name": "aac",
            }
        )
    return {"streams": streams}


class StreamValidatorTestCase(unittest.IsolatedAsyncioTestCase):
    """Unittest suite covering StreamValidator behaviour."""

    def setUp(self) -> None:
        patcher = patch(
            "iptv_sniffer.scanner.validator.check_ffmpeg_installed", return_value=True
        )
        self.addCleanup(patcher.stop)
        self.mock_ffmpeg_check = patcher.start()
        self.validator = StreamValidator(max_workers=2)

    async def test_validate_http_stream_success(self) -> None:
        probe_result = _make_probe_streams()
        with patch(
            "iptv_sniffer.scanner.validator.ffmpeg.probe", return_value=probe_result
        ):
            result = await self.validator.validate(
                "http://example.com/stream", timeout=5
            )

        self.assertTrue(result.is_valid)
        self.assertEqual(result.protocol, "http")
        self.assertEqual(result.resolution, "1920x1080")
        self.assertEqual(result.codec_video, "h264")
        self.assertEqual(result.codec_audio, "aac")
        self.assertIsNone(result.error_category)

    async def test_validate_stream_timeout(self) -> None:
        stderr = b"Connection timed out after 10000 ms"
        with patch(
            "iptv_sniffer.scanner.validator.ffmpeg.probe",
            side_effect=DummyFFmpegError(stderr=stderr),
        ):
            result = await self.validator.validate("http://slow.example.com", timeout=5)

        self.assertFalse(result.is_valid)
        self.assertEqual(result.error_category, ErrorCategory.TIMEOUT)
        self.assertIn("timed out", (result.error_message or "").lower())

    async def test_validate_stream_no_video(self) -> None:
        probe_result = _make_probe_streams(video=False, audio=True)
        with patch(
            "iptv_sniffer.scanner.validator.ffmpeg.probe", return_value=probe_result
        ):
            result = await self.validator.validate(
                "http://audio-only.example.com", timeout=5
            )

        self.assertFalse(result.is_valid)
        self.assertEqual(result.error_category, ErrorCategory.NO_VIDEO_STREAM)

    async def test_validate_rtp_stream_uses_extended_timeout(self) -> None:
        probe_result = _make_probe_streams()
        with patch(
            "iptv_sniffer.scanner.validator.ffmpeg.probe", return_value=probe_result
        ) as mock_probe:
            await self.validator.validate("rtp://239.0.0.1:1234", timeout=5)

        kwargs = mock_probe.call_args.kwargs
        timeout_value = kwargs.get("timeout")
        self.assertIsNotNone(timeout_value)
        assert timeout_value is not None  # Type narrowing for pyrefly
        self.assertGreaterEqual(timeout_value, 20)

    async def test_validate_unsupported_protocol(self) -> None:
        result = await self.validator.validate("ftp://example.com/stream", timeout=5)

        self.assertFalse(result.is_valid)
        self.assertEqual(result.error_category, ErrorCategory.UNSUPPORTED_PROTOCOL)

    async def test_validate_parses_ffmpeg_stderr_for_network_error(self) -> None:
        stderr = b"Connection refused"
        with patch(
            "iptv_sniffer.scanner.validator.ffmpeg.probe",
            side_effect=DummyFFmpegError(stderr=stderr),
        ):
            result = await self.validator.validate(
                "http://offline.example.com", timeout=5
            )

        self.assertFalse(result.is_valid)
        self.assertEqual(result.error_category, ErrorCategory.NETWORK_UNREACHABLE)
        self.assertIn("connection refused", (result.error_message or "").lower())

    async def test_validate_returns_error_when_ffmpeg_missing(self) -> None:
        with patch(
            "iptv_sniffer.scanner.validator.check_ffmpeg_installed", return_value=False
        ):
            result = await self.validator.validate("http://example.com/stream")

        self.assertFalse(result.is_valid)
        self.assertEqual(result.error_category, ErrorCategory.UNSUPPORTED_PROTOCOL)
        self.assertIn("ffmpeg is not installed", (result.error_message or "").lower())

    async def test_validate_rtsp_uses_tcp_transport(self) -> None:
        probe_result = _make_probe_streams()
        with patch(
            "iptv_sniffer.scanner.validator.ffmpeg.probe", return_value=probe_result
        ) as mock_probe:
            await self.validator.validate("rtsp://example.com/live", timeout=5)

        self.assertEqual(mock_probe.call_args.kwargs.get("rtsp_transport"), "tcp")

    async def test_validate_udp_passes_probe_options(self) -> None:
        probe_result = _make_probe_streams()
        with patch(
            "iptv_sniffer.scanner.validator.ffmpeg.probe", return_value=probe_result
        ) as mock_probe:
            await self.validator.validate("udp://239.0.0.1:1234", timeout=5)

        kwargs = mock_probe.call_args.kwargs
        self.assertEqual(kwargs.get("analyzeduration"), "5M")
        self.assertEqual(kwargs.get("probesize"), "5M")

    async def test_validate_multicast_error_category(self) -> None:
        stderr = b"Multicast join failed"
        with patch(
            "iptv_sniffer.scanner.validator.ffmpeg.probe",
            side_effect=DummyFFmpegError(stderr=stderr),
        ):
            result = await self.validator.validate("rtp://239.0.0.1:1234", timeout=5)

        self.assertEqual(result.error_category, ErrorCategory.MULTICAST_NOT_SUPPORTED)

    async def test_validate_handles_exception_without_stderr(self) -> None:
        class CustomError(Exception):
            pass

        with patch(
            "iptv_sniffer.scanner.validator.ffmpeg.probe",
            side_effect=CustomError("probe failed"),
        ):
            result = await self.validator.validate("http://broken.example.com")

        self.assertFalse(result.is_valid)
        self.assertIn("probe failed", (result.error_message or ""))

    async def test_validate_handles_unsupported_codec(self) -> None:
        stderr = b"unsupported codec"
        with patch(
            "iptv_sniffer.scanner.validator.ffmpeg.probe",
            side_effect=DummyFFmpegError(stderr=stderr),
        ):
            result = await self.validator.validate("http://codec.example.com")

        self.assertEqual(result.error_category, ErrorCategory.UNSUPPORTED_CODEC)


if __name__ == "__main__":
    unittest.main()
