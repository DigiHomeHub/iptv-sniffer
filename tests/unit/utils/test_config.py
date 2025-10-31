from __future__ import annotations

import os
import unittest
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Iterable, Iterator, Optional

from pydantic import ValidationError

from iptv_sniffer.utils.config import AppConfig

ENV_KEYS = (
    "IPTV_SNIFFER_MAX_CONCURRENCY",
    "IPTV_SNIFFER_TIMEOUT",
    "IPTV_SNIFFER_LOG_LEVEL",
    "IPTV_SNIFFER_DATA_DIR",
    "IPTV_SNIFFER_FFMPEG_CUSTOM_ARGS",
    "IPTV_SNIFFER_AI_API_KEY",
)


@contextmanager
def scrub_environment(keys: Iterable[str]) -> Iterator[None]:
    """Temporarily remove specific environment variables."""
    original: Dict[str, Optional[str]] = {}

    for key in keys:
        original[key] = os.environ.pop(key, None)

    try:
        yield
    finally:
        for key, value in original.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


@contextmanager
def override_environment(values: Dict[str, str]) -> Iterator[None]:
    """Override selected environment variables for the duration of the context."""
    with scrub_environment(values.keys()):
        os.environ.update(values)
        try:
            yield
        finally:
            for key in values:
                os.environ.pop(key, None)


class TestAppConfig(unittest.TestCase):
    """Unit tests for the AppConfig settings model."""

    def test_config_loads_defaults(self) -> None:
        """AppConfig should provide safe defaults when no overrides supplied."""
        with scrub_environment(ENV_KEYS):
            config = AppConfig()

        self.assertEqual(config.max_concurrency, 10)
        self.assertEqual(config.timeout, 10)
        self.assertEqual(config.retry_attempts, 3)
        self.assertAlmostEqual(config.retry_backoff, 1.5)
        self.assertEqual(config.ffmpeg_timeout, 10)
        self.assertIsNone(config.ffmpeg_hwaccel)
        self.assertEqual(config.ffmpeg_custom_args, [])
        self.assertEqual(config.data_dir, Path("./data"))
        self.assertEqual(config.screenshot_dir, Path("./screenshots"))
        self.assertEqual(config.host, "0.0.0.0")
        self.assertEqual(config.port, 8000)
        self.assertFalse(config.ai_enabled)
        self.assertIsNone(config.ai_api_url)
        self.assertIsNone(config.ai_api_key)
        self.assertEqual(config.log_level, "INFO")
        self.assertEqual(config.log_format, "json")

    def test_config_validates_concurrency_limits(self) -> None:
        """max_concurrency must stay within documented bounds (1-50)."""
        with self.assertRaises(ValidationError):
            AppConfig(max_concurrency=0)

        with self.assertRaises(ValidationError):
            AppConfig(max_concurrency=51)

        self.assertEqual(AppConfig(max_concurrency=1).max_concurrency, 1)
        self.assertEqual(AppConfig(max_concurrency=50).max_concurrency, 50)

    def test_config_loads_from_env_vars(self) -> None:
        """Environment variables prefixed with IPTV_SNIFFER_ override defaults."""
        overrides = {
            "IPTV_SNIFFER_MAX_CONCURRENCY": "20",
            "IPTV_SNIFFER_TIMEOUT": "25",
            "IPTV_SNIFFER_LOG_LEVEL": "DEBUG",
            "IPTV_SNIFFER_DATA_DIR": "/tmp/iptv",
            "IPTV_SNIFFER_FFMPEG_CUSTOM_ARGS": '["-reconnect", "1"]',
        }
        with override_environment(overrides):
            config = AppConfig()

        self.assertEqual(config.max_concurrency, 20)
        self.assertEqual(config.timeout, 25)
        self.assertEqual(config.log_level, "DEBUG")
        self.assertEqual(config.data_dir, Path("/tmp/iptv"))
        self.assertEqual(config.ffmpeg_custom_args, ["-reconnect", "1"])

    def test_config_validates_timeout_range(self) -> None:
        """Timeout must stay within 1-60 seconds to avoid hangs."""
        with self.assertRaises(ValidationError):
            AppConfig(timeout=0)

        with self.assertRaises(ValidationError):
            AppConfig(timeout=61)

        self.assertEqual(AppConfig(timeout=60).timeout, 60)

    def test_config_secret_str_masks_api_key(self) -> None:
        """SecretStr values should remain masked under str()."""
        with override_environment({"IPTV_SNIFFER_AI_API_KEY": "super-secret"}):
            config = AppConfig()

        self.assertIsNotNone(config.ai_api_key)
        self.assertEqual(str(config.ai_api_key), "**********")
        self.assertEqual(config.ai_api_key.get_secret_value(), "super-secret")

    def test_config_rejects_invalid_log_level(self) -> None:
        """Only supported log levels are accepted."""
        with self.assertRaises(ValidationError):
            AppConfig(log_level="TRACE")  # type: ignore[arg-type]

    def test_config_parses_ffmpeg_custom_args_variants(self) -> None:
        """Custom FFmpeg args should accept comma strings and sequences."""
        config_from_string = AppConfig(ffmpeg_custom_args="-an, -sn , ")
        config_from_sequence = AppConfig(
            ffmpeg_custom_args=["-re", "-fflags", "+genpts"]
        )
        config_blank = AppConfig(ffmpeg_custom_args="   ")
        config_scalar_json = AppConfig(ffmpeg_custom_args='"-itsoffset"')

        self.assertEqual(config_from_string.ffmpeg_custom_args, ["-an", "-sn"])
        self.assertEqual(
            config_from_sequence.ffmpeg_custom_args, ["-re", "-fflags", "+genpts"]
        )
        self.assertEqual(config_blank.ffmpeg_custom_args, [])
        self.assertEqual(config_scalar_json.ffmpeg_custom_args, ["-itsoffset"])

    def test_config_rejects_invalid_custom_args_type(self) -> None:
        """Invalid types for custom args should raise validation errors."""
        with self.assertRaises(ValidationError):
            AppConfig(ffmpeg_custom_args=123)  # type: ignore[arg-type]

    def test_config_path_validation_rejects_non_strings(self) -> None:
        """Ensure path validators reject unsupported input types."""
        with self.assertRaises(ValidationError):
            AppConfig(data_dir=5.5)  # type: ignore[arg-type]

    def test_config_retry_backoff_must_be_positive(self) -> None:
        """Retry backoff must be strictly greater than zero."""
        with self.assertRaises(ValidationError):
            AppConfig(retry_backoff=0)


if __name__ == "__main__":
    unittest.main()
