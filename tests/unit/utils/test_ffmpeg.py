from __future__ import annotations

import subprocess
import unittest
from unittest.mock import patch

from iptv_sniffer.utils import ffmpeg as ffmpeg_utils


class TestFFmpegUtils(unittest.TestCase):
    """Unit tests for FFmpeg utility helpers."""

    def test_ffmpeg_installed_returns_true_when_available(self) -> None:
        """Detect FFmpeg availability using shutil.which."""
        with patch("shutil.which", return_value="/usr/bin/ffmpeg"):
            self.assertTrue(ffmpeg_utils.check_ffmpeg_installed())

    def test_ffmpeg_installed_returns_false_when_missing(self) -> None:
        """Return False when FFmpeg cannot be located."""
        with patch("shutil.which", return_value=None):
            self.assertFalse(ffmpeg_utils.check_ffmpeg_installed())

    def test_ffmpeg_not_installed_raises_error_when_requested(self) -> None:
        """Raise FFmpegNotFoundError when raise_on_missing=True."""
        with patch("shutil.which", return_value=None):
            with self.assertRaises(ffmpeg_utils.FFmpegNotFoundError):
                ffmpeg_utils.check_ffmpeg_installed(raise_on_missing=True)

    def test_ffmpeg_version_detection(self) -> None:
        """Extract version string from ffmpeg -version output."""
        mock_completed_process = subprocess.CompletedProcess(
            args=["ffmpeg", "-version"],
            returncode=0,
            stdout="ffmpeg version 4.4.2-static\nbuilt with gcc 10.2.1\n",
            stderr="",
        )
        with (
            patch("shutil.which", return_value="/usr/bin/ffmpeg"),
            patch("subprocess.run", return_value=mock_completed_process),
        ):
            version = ffmpeg_utils.get_ffmpeg_version()
            assert version is not None
            self.assertIn("4.4.2", version)

    def test_ffmpeg_version_returns_none_when_ffmpeg_missing(self) -> None:
        """Return None for version when FFmpeg is not installed."""
        with patch("shutil.which", return_value=None):
            version = ffmpeg_utils.get_ffmpeg_version()
            self.assertIsNone(version)

    def test_ffmpeg_version_returns_none_on_subprocess_error(self) -> None:
        """Return None if ffmpeg -version call fails."""
        with (
            patch("shutil.which", return_value="/usr/bin/ffmpeg"),
            patch(
                "subprocess.run",
                side_effect=subprocess.SubprocessError("failure"),
            ),
        ):
            version = ffmpeg_utils.get_ffmpeg_version()
            self.assertIsNone(version)

    def test_ffmpeg_version_returns_none_on_nonzero_exit(self) -> None:
        """Return None when ffmpeg exits with non-zero status."""
        mock_completed_process = subprocess.CompletedProcess(
            args=["ffmpeg", "-version"],
            returncode=1,
            stdout="",
            stderr="command failed",
        )
        with (
            patch("shutil.which", return_value="/usr/bin/ffmpeg"),
            patch("subprocess.run", return_value=mock_completed_process),
        ):
            version = ffmpeg_utils.get_ffmpeg_version()
            self.assertIsNone(version)

    def test_ffmpeg_version_returns_none_when_stdout_empty(self) -> None:
        """Return None when ffmpeg produces no stdout."""
        mock_completed_process = subprocess.CompletedProcess(
            args=["ffmpeg", "-version"],
            returncode=0,
            stdout="",
            stderr="",
        )
        with (
            patch("shutil.which", return_value="/usr/bin/ffmpeg"),
            patch("subprocess.run", return_value=mock_completed_process),
        ):
            version = ffmpeg_utils.get_ffmpeg_version()
            self.assertIsNone(version)

    def test_install_instructions_for_platform(self) -> None:
        """Installation instructions should vary by platform."""
        with patch("sys.platform", "linux"):
            instructions = ffmpeg_utils.get_install_instructions()
            self.assertIn("apt-get", instructions)

        with patch("sys.platform", "darwin"):
            instructions = ffmpeg_utils.get_install_instructions()
            self.assertIn("brew install", instructions)

        with patch("sys.platform", "win32"):
            instructions = ffmpeg_utils.get_install_instructions()
            self.assertIn("choco install", instructions)

        with patch("sys.platform", "freebsd"):
            instructions = ffmpeg_utils.get_install_instructions()
            self.assertIn("ffmpeg.org", instructions)

    def test_check_ffmpeg_installed_logs_instruction_on_missing(self) -> None:
        """Error message should include installation instructions."""
        instructions = "install command"
        with (
            patch("shutil.which", return_value=None),
            patch.object(
                ffmpeg_utils, "get_install_instructions", return_value=instructions
            ),
        ):
            with self.assertRaises(ffmpeg_utils.FFmpegNotFoundError) as excinfo:
                ffmpeg_utils.check_ffmpeg_installed(raise_on_missing=True)
            self.assertIn(instructions, str(excinfo.exception))


if __name__ == "__main__":
    unittest.main()
