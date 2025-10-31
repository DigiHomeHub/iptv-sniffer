from __future__ import annotations

import asyncio
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from iptv_sniffer.scanner.screenshot import capture_screenshot


class DummyGraph:
    """Simple stand-in for ffmpeg stream graph."""

    def __init__(self, input_kwargs):
        self.input_kwargs = input_kwargs
        self.output_path: str | None = None
        self.output_kwargs: dict | None = None

    def output(self, path: str, **kwargs):
        self.output_path = path
        self.output_kwargs = kwargs
        return self


class ScreenshotCaptureTestCase(unittest.IsolatedAsyncioTestCase):
    """Tests for asynchronous screenshot capture."""

    def setUp(self) -> None:
        patcher = patch(
            "iptv_sniffer.scanner.screenshot.check_ffmpeg_installed", return_value=True
        )
        self.addCleanup(patcher.stop)
        patcher.start()

    async def test_capture_screenshot_creates_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "frame.png"
            graphs: list[DummyGraph] = []

            def input_side_effect(url: str, **kwargs):
                graph = DummyGraph(kwargs)
                graphs.append(graph)
                return graph

            def run_side_effect(graph: DummyGraph, **kwargs):
                assert graph.output_path is not None
                Path(graph.output_path).write_bytes(b"\x89PNG")
                return (b"", b"")

            with (
                patch(
                    "iptv_sniffer.scanner.screenshot.ffmpeg.input",
                    side_effect=input_side_effect,
                ),
                patch(
                    "iptv_sniffer.scanner.screenshot.ffmpeg.run",
                    side_effect=run_side_effect,
                ),
            ):
                await capture_screenshot("http://example.com/live", output_path)

            self.assertTrue(output_path.exists())
            self.assertEqual(graphs[0].input_kwargs.get("ss"), 5)
            output_kwargs = graphs[0].output_kwargs
            assert output_kwargs is not None
            self.assertEqual(output_kwargs.get("vframes"), 1)
            self.assertEqual(output_kwargs.get("vcodec"), "png")

    async def test_capture_screenshot_with_vaapi(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "frame.png"
            graphs: list[DummyGraph] = []

            def input_side_effect(url: str, **kwargs):
                graph = DummyGraph(kwargs)
                graphs.append(graph)
                return graph

            def run_side_effect(graph: DummyGraph, **kwargs):
                assert graph.output_path is not None
                Path(graph.output_path).write_bytes(b"\x89PNG")
                return (b"", b"")

            with (
                patch(
                    "iptv_sniffer.scanner.screenshot.ffmpeg.input",
                    side_effect=input_side_effect,
                ),
                patch(
                    "iptv_sniffer.scanner.screenshot.ffmpeg.run",
                    side_effect=run_side_effect,
                ),
            ):
                await capture_screenshot(
                    "http://example.com/live", output_path, hwaccel="vaapi"
                )

            self.assertTrue(output_path.exists())
            input_kwargs = graphs[0].input_kwargs
            self.assertEqual(input_kwargs.get("hwaccel"), "vaapi")
            self.assertEqual(input_kwargs.get("hwaccel_device"), "/dev/dri/renderD128")

    async def test_capture_screenshot_timeout(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "frame.png"

            def input_side_effect(url: str, **kwargs):
                return DummyGraph(kwargs)

            def run_side_effect(graph: DummyGraph, **kwargs):
                time.sleep(2)

            with (
                patch(
                    "iptv_sniffer.scanner.screenshot.ffmpeg.input",
                    side_effect=input_side_effect,
                ),
                patch(
                    "iptv_sniffer.scanner.screenshot.ffmpeg.run",
                    side_effect=run_side_effect,
                ),
            ):
                with self.assertRaises(asyncio.TimeoutError):
                    await capture_screenshot(
                        "http://example.com/live", output_path, timeout=1
                    )

            self.assertFalse(output_path.exists())

    async def test_capture_screenshot_hwaccel_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "frame.png"
            graphs: list[DummyGraph] = []

            def input_side_effect(url: str, **kwargs):
                graph = DummyGraph(kwargs)
                graphs.append(graph)
                return graph

            call_count = {"value": 0}

            def run_side_effect(graph: DummyGraph, **kwargs):
                call_count["value"] += 1
                if call_count["value"] == 1:
                    raise DummyFFmpegError(stderr=b"hwaccel failure")
                assert graph.output_path is not None
                Path(graph.output_path).write_bytes(b"\x89PNG")
                return (b"", b"")

            with (
                patch(
                    "iptv_sniffer.scanner.screenshot.ffmpeg.input",
                    side_effect=input_side_effect,
                ),
                patch(
                    "iptv_sniffer.scanner.screenshot.ffmpeg.run",
                    side_effect=run_side_effect,
                ),
            ):
                await capture_screenshot(
                    "http://example.com/live", output_path, hwaccel="cuda"
                )

            self.assertTrue(output_path.exists())
            self.assertGreaterEqual(call_count["value"], 2)
            first_kwargs = graphs[0].input_kwargs
            second_kwargs = graphs[1].input_kwargs
            self.assertEqual(first_kwargs.get("hwaccel"), "cuda")
            self.assertNotIn("hwaccel", second_kwargs)


class DummyFFmpegError(Exception):
    def __init__(self, stderr: bytes):
        super().__init__("ffmpeg error")
        self.stderr = stderr


if __name__ == "__main__":
    unittest.main()
