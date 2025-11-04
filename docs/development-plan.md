# iptv-sniffer Development Plan (TDD Mode)

## Overview

This document breaks down the iptv-sniffer project into TDD-driven development tasks following the **Red-Green-Refactor** cycle:

1. **Red:** Write a failing test that defines expected behavior
2. **Green:** Write minimal code to make the test pass
3. **Refactor:** Improve code quality while keeping tests green

Each phase follows strict TDD principles with test coverage >80% and all modules under 500 lines.

---

## Project Timeline

**Total Duration:** 17 weeks  
**Methodology:** Test-Driven Development (TDD)  
**Test Framework:** unittest + pytest-testmon  
**Quality Gates:** pyrefly check, ruff check, 80%+ coverage

---

## Phase 1: Core Infrastructure (Weeks 1-2)

**Goal:** Establish foundational data models and storage layer with comprehensive test coverage.

### Task 1.1: Channel Data Model

**Test First (Red):**

```python
# tests/unit/channel/test_models.py

def test_channel_creation_with_minimal_fields():
    """Channel should be created with only required fields"""
    channel = Channel(name="CCTV-1", url="http://192.168.1.100:8000")
    assert channel.name == "CCTV-1"
    assert str(channel.url) == "http://192.168.1.100:8000"
    assert channel.is_online is False
    assert channel.id is not None  # Auto-generated UUID

def test_channel_url_validation_rejects_invalid_scheme():
    """Channel URL must use supported protocol schemes"""
    with pytest.raises(ValidationError):
        Channel(name="Test", url="ftp://invalid.com")

def test_channel_url_supports_multiple_protocols():
    """Channel should accept HTTP, RTP, RTSP, UDP protocols"""
    protocols = ["http://", "https://", "rtp://", "rtsp://", "udp://"]
    for proto in protocols:
        channel = Channel(name="Test", url=f"{proto}192.168.1.1:8000")
        assert channel.url.startswith(proto)

def test_channel_validation_status_defaults_to_unknown():
    """Newly created channels should have UNKNOWN validation status"""
    channel = Channel(name="Test", url="http://test.com")
    assert channel.validation_status == ValidationStatus.UNKNOWN

def test_channel_timestamps_auto_generated():
    """created_at and updated_at should be automatically set"""
    channel = Channel(name="Test", url="http://test.com")
    assert channel.created_at is not None
    assert channel.updated_at is not None
```

**Implement (Green):**

```python
# iptv_sniffer/channel/models.py

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4
from pydantic import BaseModel, Field, validator
from urllib.parse import urlparse


class ValidationStatus(str, Enum):
    UNKNOWN = "unknown"
    VALIDATING = "validating"
    ONLINE = "online"
    OFFLINE = "offline"
    ERROR = "error"


class Channel(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    url: str  # Support all protocols, not just HTTP
    tvg_id: Optional[str] = None
    tvg_logo: Optional[str] = None
    group: Optional[str] = None
    resolution: Optional[str] = None
    is_online: bool = False
    validation_status: ValidationStatus = ValidationStatus.UNKNOWN
    last_validated: Optional[datetime] = None
    screenshot_path: Optional[str] = None
    manually_edited: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @validator("url")
    def validate_stream_url(cls, v: str) -> str:
        """Validate URL supports IPTV protocols"""
        valid_schemes = {"http", "https", "rtp", "rtsp", "udp", "mms"}
        parsed = urlparse(v)
        if parsed.scheme not in valid_schemes:
            raise ValueError(f"Unsupported protocol: {parsed.scheme}")
        return v

    class Config:
        use_enum_values = True
```

**Refactor:** Extract URL validation logic to utils if >3 validators share logic.

**Definition of Done:**

- [ ] All tests pass with pytest
- [ ] mypy --strict reports no errors
- [ ] Test coverage >90% for models.py
- [ ] Module <500 lines

---

### Task 1.2: Configuration Management

**Test First (Red):**

```python
# tests/unit/utils/test_config.py

def test_config_loads_defaults():
    """Config should have sensible defaults without env vars"""
    config = AppConfig()
    assert config.max_concurrency == 10
    assert config.timeout == 10
    assert config.ffmpeg_timeout == 10
    assert config.log_level == "INFO"

def test_config_validates_concurrency_limits():
    """Concurrency must be between 1 and 50"""
    with pytest.raises(ValidationError):
        AppConfig(max_concurrency=0)
    with pytest.raises(ValidationError):
        AppConfig(max_concurrency=51)

def test_config_loads_from_env_vars(monkeypatch):
    """Config should override defaults with env vars"""
    monkeypatch.setenv("IPTV_SNIFFER_MAX_CONCURRENCY", "20")
    monkeypatch.setenv("IPTV_SNIFFER_TIMEOUT", "15")
    config = AppConfig()
    assert config.max_concurrency == 20
    assert config.timeout == 15

def test_config_validates_private_network_enforcement():
    """Should validate IP ranges are in RFC1918 private networks"""
    # Test will be used when scanning features are added
    pass
```

**Implement (Green):**

```python
# iptv_sniffer/utils/config.py

from pathlib import Path
from typing import List, Literal, Optional
from pydantic import BaseModel, Field, SecretStr, HttpUrl


class AppConfig(BaseModel):
    # Network Scanning
    max_concurrency: int = Field(default=10, ge=1, le=50)
    timeout: int = Field(default=10, ge=1, le=60)
    retry_attempts: int = Field(default=3, ge=0, le=5)
    retry_backoff: float = Field(default=1.5, ge=1.0, le=3.0)

    # FFmpeg
    ffmpeg_timeout: int = Field(default=10, ge=1, le=60)
    ffmpeg_hwaccel: Optional[Literal["vaapi", "cuda"]] = None
    ffmpeg_custom_args: List[str] = Field(default_factory=list)

    # Storage
    data_dir: Path = Field(default=Path("./data"))
    screenshot_dir: Path = Field(default=Path("./screenshots"))

    # Web Server
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000, ge=1, le=65535)

    # AI Integration
    ai_enabled: bool = Field(default=False)
    ai_api_url: Optional[HttpUrl] = None
    ai_api_key: Optional[SecretStr] = None

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_format: Literal["json", "text"] = "json"

    class Config:
        env_prefix = "IPTV_SNIFFER_"
        env_file = ".env"
```

**Definition of Done:**

- [ ] All config tests pass
- [ ] Environment variable loading works correctly
- [ ] Validation errors are clear and actionable
- [ ] Test coverage >85%

---

### Task 1.3: JSON Storage Repository

**Test First (Red):**

```python
# tests/unit/storage/test_json_repository.py

@pytest.fixture
def temp_storage_file(tmp_path):
    """Provide temporary JSON file for testing"""
    return tmp_path / "channels.json"

@pytest.mark.asyncio
async def test_add_channel_creates_new_record(temp_storage_file):
    """Adding channel should persist to JSON file"""
    repo = JSONChannelRepository(temp_storage_file)
    channel = Channel(name="CCTV-1", url="http://test.com")

    saved = await repo.add(channel)
    assert saved.id == channel.id

    # Verify persistence
    loaded = await repo.get_by_id(channel.id)
    assert loaded.name == "CCTV-1"

@pytest.mark.asyncio
async def test_add_channel_updates_existing_by_url(temp_storage_file):
    """Adding duplicate URL should update existing channel"""
    repo = JSONChannelRepository(temp_storage_file)

    channel1 = Channel(name="CCTV-1", url="http://test.com", is_online=False)
    await repo.add(channel1)

    channel2 = Channel(name="CCTV-1 Updated", url="http://test.com", is_online=True)
    updated = await repo.add(channel2)

    # Should update, not create new
    all_channels = await repo.find_all()
    assert len(all_channels) == 1
    assert all_channels[0].is_online is True

@pytest.mark.asyncio
async def test_find_all_with_filters(temp_storage_file):
    """Repository should support filtering by group and status"""
    repo = JSONChannelRepository(temp_storage_file)

    await repo.add(Channel(name="CCTV-1", url="http://1.com", group="央视", is_online=True))
    await repo.add(Channel(name="CCTV-2", url="http://2.com", group="央视", is_online=False))
    await repo.add(Channel(name="Phoenix", url="http://3.com", group="凤凰", is_online=True))

    # Filter by group
    cctv_channels = await repo.find_all(filters={"group": "央视"})
    assert len(cctv_channels) == 2

    # Filter by online status
    online_channels = await repo.find_all(filters={"is_online": True})
    assert len(online_channels) == 2

@pytest.mark.asyncio
async def test_delete_channel(temp_storage_file):
    """Deleting channel should remove from storage"""
    repo = JSONChannelRepository(temp_storage_file)
    channel = await repo.add(Channel(name="Test", url="http://test.com"))

    result = await repo.delete(channel.id)
    assert result is True

    deleted = await repo.get_by_id(channel.id)
    assert deleted is None
```

**Implement (Green):**

```python
# iptv_sniffer/storage/json_repository.py

import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from iptv_sniffer.channel.models import Channel


class JSONChannelRepository:
    """File-based JSON storage for channels"""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            self._write_data([])

    def _read_data(self) -> List[Dict[str, Any]]:
        """Read raw JSON data"""
        with open(self.file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write_data(self, data: List[Dict[str, Any]]) -> None:
        """Write raw JSON data"""
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    async def add(self, channel: Channel) -> Channel:
        """Add or update channel (by URL)"""
        channels = self._read_data()

        # Check for existing URL
        for idx, ch in enumerate(channels):
            if ch["url"] == str(channel.url):
                # Update existing
                channels[idx] = channel.dict()
                self._write_data(channels)
                return channel

        # Add new
        channels.append(channel.dict())
        self._write_data(channels)
        return channel

    async def get_by_id(self, channel_id: str) -> Optional[Channel]:
        """Get channel by ID"""
        channels = self._read_data()
        for ch in channels:
            if ch["id"] == channel_id:
                return Channel(**ch)
        return None

    async def find_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Channel]:
        """Find channels with optional filters"""
        channels = [Channel(**ch) for ch in self._read_data()]

        if not filters:
            return channels

        # Apply filters
        filtered = channels
        if "group" in filters:
            filtered = [ch for ch in filtered if ch.group == filters["group"]]
        if "is_online" in filters:
            filtered = [ch for ch in filtered if ch.is_online == filters["is_online"]]

        return filtered

    async def delete(self, channel_id: str) -> bool:
        """Delete channel by ID"""
        channels = self._read_data()
        original_len = len(channels)

        channels = [ch for ch in channels if ch["id"] != channel_id]

        if len(channels) < original_len:
            self._write_data(channels)
            return True
        return False
```

**Refactor:** Extract filter logic to separate method if >5 filter types.

**Definition of Done:**

- [ ] All repository tests pass
- [ ] Concurrent access handled gracefully (document limitation)
- [ ] Test coverage >85%
- [ ] Module <500 lines

---

### Task 1.4: CLI Structure with Typer

**Test First (Red):**

```python
# tests/unit/cli/test_app.py

from typer.testing import CliRunner
from iptv_sniffer.cli.app import app

runner = CliRunner()

def test_cli_version_command():
    """CLI should display version information"""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "iptv-sniffer" in result.stdout

def test_cli_help_command():
    """CLI should display help message"""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "scan" in result.stdout
    assert "validate" in result.stdout
    assert "export" in result.stdout

def test_cli_scan_command_exists():
    """Scan command should be available"""
    result = runner.invoke(app, ["scan", "--help"])
    assert result.exit_code == 0
    assert "Start network scan" in result.stdout
```

**Implement (Green):**

```python
# iptv_sniffer/cli/app.py

import typer
from typing import Optional

app = typer.Typer(
    name="iptv-sniffer",
    help="Discover and validate IPTV channels on local networks"
)

def version_callback(value: bool):
    if value:
        typer.echo("iptv-sniffer version 0.1.0")
        raise typer.Exit()

@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None, "--version", callback=version_callback, is_eager=True
    )
):
    """iptv-sniffer CLI"""
    pass

# Placeholder commands (will be implemented in later phases)
@app.command()
def scan():
    """Start network scan for IPTV channels"""
    typer.echo("Scan command not yet implemented")

@app.command()
def validate():
    """Validate existing channels"""
    typer.echo("Validate command not yet implemented")

@app.command()
def export():
    """Export channels as M3U playlist"""
    typer.echo("Export command not yet implemented")
```

**Definition of Done:**

- [ ] Basic CLI structure works
- [ ] All commands appear in help
- [ ] Version command displays correctly
- [ ] Test coverage >80%

---

## Phase 2: FFmpeg Integration (Weeks 3-4)

**Goal:** Implement FFmpeg-based stream validation with protocol-aware handling.

### Task 2.1: FFmpeg Availability Check

**Test First (Red):**

```python
# tests/unit/utils/test_ffmpeg.py

def test_ffmpeg_installed_returns_true_when_available():
    """Should detect FFmpeg installation"""
    assert check_ffmpeg_installed() is True

def test_ffmpeg_version_detection():
    """Should detect FFmpeg version string"""
    version = get_ffmpeg_version()
    assert version is not None
    assert "ffmpeg" in version.lower()

@patch("shutil.which", return_value=None)
def test_ffmpeg_not_installed_raises_error(mock_which):
    """Should raise clear error when FFmpeg missing"""
    with pytest.raises(FFmpegNotFoundError, match="FFmpeg not found"):
        check_ffmpeg_installed(raise_on_missing=True)
```

**Implement (Green):**

```python
# iptv_sniffer/utils/ffmpeg.py

import shutil
import subprocess
from typing import Optional


class FFmpegNotFoundError(Exception):
    """Raised when FFmpeg is not installed"""
    pass


def check_ffmpeg_installed(raise_on_missing: bool = False) -> bool:
    """Check if FFmpeg is available on system"""
    ffmpeg_path = shutil.which("ffmpeg")

    if ffmpeg_path is None:
        if raise_on_missing:
            raise FFmpegNotFoundError(
                "FFmpeg not found. Install: apt-get install ffmpeg"
            )
        return False

    return True


def get_ffmpeg_version() -> Optional[str]:
    """Get FFmpeg version string"""
    if not check_ffmpeg_installed():
        return None

    result = subprocess.run(
        ["ffmpeg", "-version"],
        capture_output=True,
        text=True
    )

    return result.stdout.split("\n")[0] if result.returncode == 0 else None
```

**Definition of Done:**

- [ ] FFmpeg detection works across platforms
- [ ] Clear error messages when FFmpeg missing
- [ ] Test coverage >85%

---

### Task 2.2: HTTP Stream Validator

**Test First (Red):**

```python
# tests/unit/scanner/test_validator.py

@pytest.mark.asyncio
async def test_validate_http_stream_success():
    """Should validate accessible HTTP stream"""
    validator = StreamValidator(max_workers=2)

    # Use real test stream or mock ffmpeg.probe
    with patch("ffmpeg.probe") as mock_probe:
        mock_probe.return_value = {
            "streams": [
                {
                    "codec_type": "video",
                    "codec_name": "h264",
                    "width": 1920,
                    "height": 1080
                }
            ]
        }

        result = await validator.validate("http://192.168.1.100:8000")

        assert result.is_valid is True
        assert result.protocol == "http"
        assert result.resolution == "1920x1080"
        assert result.codec_video == "h264"

@pytest.mark.asyncio
async def test_validate_stream_timeout():
    """Should handle timeout gracefully"""
    validator = StreamValidator(max_workers=2)

    with patch("ffmpeg.probe", side_effect=ffmpeg.Error("timeout", None, b"timeout")):
        result = await validator.validate("http://slow-server.com", timeout=1)

        assert result.is_valid is False
        assert result.error_category == ErrorCategory.TIMEOUT

@pytest.mark.asyncio
async def test_validate_stream_no_video():
    """Should reject streams without video"""
    validator = StreamValidator(max_workers=2)

    with patch("ffmpeg.probe") as mock_probe:
        mock_probe.return_value = {
            "streams": [
                {"codec_type": "audio", "codec_name": "aac"}
            ]
        }

        result = await validator.validate("http://audio-only.com")

        assert result.is_valid is False
        assert result.error_category == ErrorCategory.NO_VIDEO_STREAM
```

**Implement (Green):**

```python
# iptv_sniffer/scanner/validator.py

import asyncio
import ffmpeg
import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class ErrorCategory(str, Enum):
    NETWORK_UNREACHABLE = "network_unreachable"
    TIMEOUT = "timeout"
    NO_VIDEO_STREAM = "no_video_stream"
    UNSUPPORTED_CODEC = "unsupported_codec"
    UNSUPPORTED_PROTOCOL = "unsupported_protocol"
    MULTICAST_NOT_SUPPORTED = "multicast_not_supported"


@dataclass
class StreamValidationResult:
    url: str
    is_valid: bool
    protocol: str
    resolution: Optional[str] = None
    codec_video: Optional[str] = None
    codec_audio: Optional[str] = None
    error_category: Optional[ErrorCategory] = None
    error_message: Optional[str] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class StreamValidator:
    """Protocol-aware stream validator using ffmpeg-python"""

    def __init__(self, max_workers: int = 10):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.validators = {
            "http": self._validate_http,
            "https": self._validate_http,
            "rtp": self._validate_rtp,
            "rtsp": self._validate_rtsp,
            "udp": self._validate_udp,
        }

    async def validate(self, url: str, timeout: int = 10) -> StreamValidationResult:
        """Validate stream with protocol-specific handler"""
        protocol = self._detect_protocol(url)
        validator = self.validators.get(protocol)

        if not validator:
            return StreamValidationResult(
                url=url,
                is_valid=False,
                protocol=protocol,
                error_category=ErrorCategory.UNSUPPORTED_PROTOCOL,
                error_message=f"Protocol {protocol} not supported"
            )

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            self.executor,
            validator,
            url,
            timeout
        )

    def _detect_protocol(self, url: str) -> str:
        """Extract protocol from URL"""
        return urlparse(url).scheme.lower()

    def _validate_http(self, url: str, timeout: int) -> StreamValidationResult:
        """Validate HTTP/HTTPS stream"""
        try:
            probe = ffmpeg.probe(url, timeout=timeout)
            return self._parse_probe_result(url, "http", probe)

        except ffmpeg.Error as e:
            return self._handle_ffmpeg_error(url, "http", e)

    def _validate_rtp(self, url: str, timeout: int) -> StreamValidationResult:
        """Validate RTP multicast stream (longer timeout, special options)"""
        timeout = max(timeout, 20)  # RTP needs longer timeout

        try:
            probe = ffmpeg.probe(
                url,
                timeout=timeout,
                rtbufsize="100M",
                analyzeduration="10M",
                probesize="10M"
            )
            return self._parse_probe_result(url, "rtp", probe)

        except ffmpeg.Error as e:
            return self._handle_ffmpeg_error(url, "rtp", e)

    def _validate_rtsp(self, url: str, timeout: int) -> StreamValidationResult:
        """Validate RTSP stream"""
        try:
            probe = ffmpeg.probe(url, timeout=timeout, rtsp_transport="tcp")
            return self._parse_probe_result(url, "rtsp", probe)

        except ffmpeg.Error as e:
            return self._handle_ffmpeg_error(url, "rtsp", e)

    def _validate_udp(self, url: str, timeout: int) -> StreamValidationResult:
        """Validate UDP stream"""
        try:
            probe = ffmpeg.probe(url, timeout=timeout)
            return self._parse_probe_result(url, "udp", probe)

        except ffmpeg.Error as e:
            return self._handle_ffmpeg_error(url, "udp", e)

    def _parse_probe_result(
        self, url: str, protocol: str, probe: dict
    ) -> StreamValidationResult:
        """Extract stream info from FFmpeg probe result"""
        video_stream = next(
            (s for s in probe.get("streams", []) if s["codec_type"] == "video"),
            None
        )

        if not video_stream:
            return StreamValidationResult(
                url=url,
                is_valid=False,
                protocol=protocol,
                error_category=ErrorCategory.NO_VIDEO_STREAM,
                error_message="No video stream found"
            )

        audio_stream = next(
            (s for s in probe.get("streams", []) if s["codec_type"] == "audio"),
            None
        )

        return StreamValidationResult(
            url=url,
            is_valid=True,
            protocol=protocol,
            resolution=f"{video_stream['width']}x{video_stream['height']}",
            codec_video=video_stream["codec_name"],
            codec_audio=audio_stream["codec_name"] if audio_stream else None
        )

    def _handle_ffmpeg_error(
        self, url: str, protocol: str, error: ffmpeg.Error
    ) -> StreamValidationResult:
        """Parse FFmpeg error into structured result"""
        stderr = error.stderr.decode() if error.stderr else ""

        if "timeout" in stderr.lower() or "timed out" in stderr.lower():
            category = ErrorCategory.TIMEOUT
            message = "Stream validation timed out"
        elif "no route to host" in stderr.lower():
            category = ErrorCategory.MULTICAST_NOT_SUPPORTED
            message = "Multicast not supported on this network"
        else:
            category = ErrorCategory.NETWORK_UNREACHABLE
            message = f"FFmpeg error: {stderr[:200]}"

        logger.warning(
            "Stream validation failed",
            extra={"url": url, "protocol": protocol, "error": stderr}
        )

        return StreamValidationResult(
            url=url,
            is_valid=False,
            protocol=protocol,
            error_category=category,
            error_message=message
        )
```

**Definition of Done:**

- [ ] All validator tests pass
- [ ] HTTP/HTTPS validation works
- [ ] Timeout handling works correctly
- [ ] Error messages are actionable
- [ ] Test coverage >80%
- [ ] Module <500 lines

---

### Task 2.3: Screenshot Capture

**Test First (Red):**

```python
# tests/unit/scanner/test_screenshot.py

@pytest.mark.asyncio
async def test_capture_screenshot_creates_file(tmp_path):
    """Should capture screenshot to specified path"""
    output_path = tmp_path / "screenshot.png"

    with patch("ffmpeg.input") as mock_input:
        mock_stream = MagicMock()
        mock_input.return_value = mock_stream
        mock_stream.output.return_value.overwrite_output.return_value.run.return_value = None

        await capture_screenshot("http://test.com", output_path, timeout=5)

        mock_input.assert_called_once()
        assert "http://test.com" in str(mock_input.call_args)

@pytest.mark.asyncio
async def test_capture_screenshot_with_hwaccel(tmp_path):
    """Should use hardware acceleration when specified"""
    output_path = tmp_path / "screenshot.png"

    with patch("ffmpeg.input") as mock_input:
        mock_stream = MagicMock()
        mock_input.return_value = mock_stream
        mock_stream.output.return_value.overwrite_output.return_value.run.return_value = None

        await capture_screenshot("http://test.com", output_path, hwaccel="vaapi")

        # Check VAAPI options were passed
        call_kwargs = mock_input.call_args[1]
        assert call_kwargs.get("hwaccel") == "vaapi"
```

**Implement (Green):**

```python
# iptv_sniffer/scanner/screenshot.py

import asyncio
import ffmpeg
import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=5)


async def capture_screenshot(
    url: str,
    output_path: Path,
    timeout: int = 10,
    hwaccel: Optional[str] = None
) -> None:
    """Capture screenshot from stream"""
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(
        _executor,
        _sync_capture_screenshot,
        url,
        output_path,
        timeout,
        hwaccel
    )


def _sync_capture_screenshot(
    url: str,
    output_path: Path,
    timeout: int,
    hwaccel: Optional[str]
) -> None:
    """Synchronous screenshot capture (runs in thread pool)"""
    input_opts = {"t": 5, "timeout": timeout}

    if hwaccel == "vaapi":
        input_opts.update({
            "hwaccel": "vaapi",
            "hwaccel_device": "/dev/dri/renderD128",
            "hwaccel_output_format": "vaapi"
        })
    elif hwaccel == "cuda":
        input_opts.update({
            "hwaccel": "cuda",
            "hwaccel_output_format": "cuda"
        })

    try:
        (
            ffmpeg
            .input(url, **input_opts)
            .output(
                str(output_path),
                vframes=1,
                format="image2",
                vcodec="png"
            )
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )

        logger.info(f"Screenshot captured: {output_path}")

    except ffmpeg.Error as e:
        logger.error(
            f"Screenshot capture failed: {e.stderr.decode() if e.stderr else 'Unknown error'}"
        )
        raise
```

**Definition of Done:**

- [ ] Screenshot capture works for valid streams
- [ ] Hardware acceleration options tested
- [ ] Timeout enforcement works
- [ ] Test coverage >75%

---

## Phase 3: Network Scanning (Weeks 5-7)

**Goal:** Implement strategy pattern for flexible scanning with rate limiting.

### Task 3.1: Strategy Pattern Base

**Test First (Red):**

```python
# tests/unit/scanner/test_strategy.py

@pytest.mark.asyncio
async def test_scan_strategy_interface():
    """All strategies must implement required interface"""

    class TestStrategy(ScanStrategy):
        async def generate_targets(self):
            yield "http://test.com"

        def estimate_target_count(self) -> int:
            return 1

    strategy = TestStrategy()
    targets = [t async for t in strategy.generate_targets()]
    assert len(targets) == 1
    assert strategy.estimate_target_count() == 1

def test_scan_mode_enum_values():
    """ScanMode should have all expected modes"""
    assert ScanMode.TEMPLATE == "template"
    assert ScanMode.MULTICAST == "multicast"
    assert ScanMode.M3U_BATCH == "m3u_batch"
```

**Implement (Green):**

```python
# iptv_sniffer/scanner/strategy.py

from abc import ABC, abstractmethod
from enum import Enum
from typing import AsyncIterator


class ScanMode(str, Enum):
    TEMPLATE = "template"
    MULTICAST = "multicast"
    M3U_BATCH = "m3u_batch"


class ScanStrategy(ABC):
    """Abstract base class for scanning strategies"""

    @abstractmethod
    async def generate_targets(self) -> AsyncIterator[str]:
        """Generate stream URLs to validate"""
        pass

    @abstractmethod
    def estimate_target_count(self) -> int:
        """Estimate total targets for progress tracking"""
        pass
```

**Definition of Done:**

- [ ] ABC interface defined
- [ ] Type hints complete
- [ ] Test coverage 100% for abstract class

---

### Task 3.2: Template Scan Strategy

**Test First (Red):**

```python
# tests/unit/scanner/test_template_strategy.py

@pytest.mark.asyncio
async def test_template_strategy_generates_urls():
    """Should generate URLs by replacing {ip} placeholder"""
    strategy = TemplateScanStrategy(
        base_url="http://192.168.2.2:7788/rtp/{ip}:8000",
        start_ip="192.168.1.1",
        end_ip="192.168.1.3"
    )

    urls = [url async for url in strategy.generate_targets()]

    assert len(urls) == 3
    assert urls[0] == "http://192.168.2.2:7788/rtp/192.168.1.1:8000"
    assert urls[1] == "http://192.168.2.2:7788/rtp/192.168.1.2:8000"
    assert urls[2] == "http://192.168.2.2:7788/rtp/192.168.1.3:8000"

def test_template_strategy_validates_private_ips():
    """Should reject public IP ranges"""
    with pytest.raises(SecurityError, match="Only private IP ranges allowed"):
        TemplateScanStrategy(
            base_url="http://server.com/{ip}",
            start_ip="8.8.8.8",  # Public IP
            end_ip="8.8.8.10"
        )

def test_template_strategy_validates_ip_range_size():
    """Should reject ranges larger than 1024 IPs"""
    with pytest.raises(ValueError, match="IP range too large"):
        TemplateScanStrategy(
            base_url="http://server.com/{ip}",
            start_ip="192.168.1.1",
            end_ip="192.168.5.1"  # >1024 IPs
        )

def test_template_strategy_estimate_count():
    """Should accurately estimate target count"""
    strategy = TemplateScanStrategy(
        base_url="http://test.com/{ip}",
        start_ip="192.168.1.1",
        end_ip="192.168.1.100"
    )
    assert strategy.estimate_target_count() == 100
```

**Implement (Green):**

```python
# iptv_sniffer/scanner/template_strategy.py

import ipaddress
import logging
from typing import AsyncIterator
from iptv_sniffer.scanner.strategy import ScanStrategy

logger = logging.getLogger(__name__)


class SecurityError(Exception):
    """Raised for security violations in scanning"""
    pass


class TemplateScanStrategy(ScanStrategy):
    """Scan strategy using URL template with IP range"""

    def __init__(self, base_url: str, start_ip: str, end_ip: str):
        self.base_url = base_url
        self.start_ip = start_ip
        self.end_ip = end_ip

        # Validate private network
        self._validate_private_network()

        # Validate range size
        count = self._calculate_ip_count()
        if count > 1024:
            raise ValueError(
                f"IP range too large ({count} IPs). Maximum: 1024"
            )

    def _validate_private_network(self) -> None:
        """Ensure IP range is within RFC1918 private networks"""
        private_ranges = [
            ipaddress.ip_network("10.0.0.0/8"),
            ipaddress.ip_network("172.16.0.0/12"),
            ipaddress.ip_network("192.168.0.0/16"),
        ]

        start = ipaddress.ip_address(self.start_ip)
        end = ipaddress.ip_address(self.end_ip)

        for network in private_ranges:
            if start in network and end in network:
                return

        raise SecurityError("Only private IP ranges allowed (RFC1918)")

    def _calculate_ip_count(self) -> int:
        """Calculate number of IPs in range"""
        start = int(ipaddress.ip_address(self.start_ip))
        end = int(ipaddress.ip_address(self.end_ip))
        return end - start + 1

    async def generate_targets(self) -> AsyncIterator[str]:
        """Generate URLs by substituting IP addresses"""
        start = ipaddress.ip_address(self.start_ip)
        end = ipaddress.ip_address(self.end_ip)

        current = start
        while current <= end:
            url = self.base_url.replace("{ip}", str(current))
            yield url
            current += 1

    def estimate_target_count(self) -> int:
        """Estimate total number of URLs to generate"""
        return self._calculate_ip_count()
```

**Definition of Done:**

- [ ] URL generation works correctly
- [ ] Private network validation enforced
- [ ] Range size validation enforced
- [ ] Test coverage >90%
- [ ] Module <500 lines

---

### Task 3.3: Rate Limiter

**Test First (Red):**

```python
# tests/unit/scanner/test_rate_limiter.py

@pytest.mark.asyncio
async def test_rate_limiter_enforces_concurrency():
    """Should limit concurrent operations to max_concurrency"""
    limiter = RateLimiter(max_concurrency=2, timeout=10)

    execution_times = []

    async def slow_task(task_id: int):
        async with limiter:
            start = time.time()
            await asyncio.sleep(0.1)
            execution_times.append((task_id, start, time.time()))

    # Start 4 tasks with concurrency=2
    await asyncio.gather(*[slow_task(i) for i in range(4)])

    # Check that only 2 tasks ran concurrently
    # (Tasks 0,1 should complete before 2,3 start)
    assert len(execution_times) == 4

@pytest.mark.asyncio
async def test_rate_limiter_timeout():
    """Should enforce timeout on operations"""
    limiter = RateLimiter(max_concurrency=10, timeout=0.1)

    async def slow_task():
        async with limiter:
            await asyncio.sleep(1)  # Longer than timeout

    with pytest.raises(asyncio.TimeoutError):
        await slow_task()
```

**Implement (Green):**

```python
# iptv_sniffer/scanner/rate_limiter.py

import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter using asyncio.Semaphore"""

    def __init__(self, max_concurrency: int = 10, timeout: int = 10):
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self.timeout = timeout

    async def __aenter__(self):
        await self.semaphore.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.semaphore.release()

    async def execute(self, coro: Any):
        """Execute coroutine with rate limiting and timeout"""
        async with self:
            try:
                return await asyncio.wait_for(coro, timeout=self.timeout)
            except asyncio.TimeoutError:
                logger.warning(f"Operation timed out after {self.timeout}s")
                raise
```

**Definition of Done:**

- [ ] Concurrency limiting works
- [ ] Timeout enforcement works
- [ ] Test coverage >85%

---

### Task 3.4: Scan Orchestrator

**Test First (Red):**

```python
# tests/unit/scanner/test_orchestrator.py

@pytest.mark.asyncio
async def test_orchestrator_executes_scan_with_strategy():
    """Should execute scan using provided strategy"""
    strategy = TemplateScanStrategy(
        base_url="http://test.com/{ip}",
        start_ip="192.168.1.1",
        end_ip="192.168.1.3"
    )

    validator = StreamValidator(max_workers=2)
    orchestrator = ScanOrchestrator(validator, max_concurrency=2)

    results = []
    async for result in orchestrator.execute_scan(strategy):
        results.append(result)

    assert len(results) == 3
    assert all(isinstance(r, StreamValidationResult) for r in results)

@pytest.mark.asyncio
async def test_orchestrator_tracks_progress():
    """Should track scan progress"""
    strategy = TemplateScanStrategy(
        base_url="http://test.com/{ip}",
        start_ip="192.168.1.1",
        end_ip="192.168.1.10"
    )

    validator = StreamValidator(max_workers=2)
    orchestrator = ScanOrchestrator(validator, max_concurrency=2)

    progress_updates = []

    async def progress_callback(progress: ScanProgress):
        progress_updates.append(progress)

    orchestrator.on_progress(progress_callback)

    async for _ in orchestrator.execute_scan(strategy):
        pass

    assert len(progress_updates) > 0
    assert progress_updates[-1].completed == 10
```

**Implement (Green):**

```python
# iptv_sniffer/scanner/orchestrator.py

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import AsyncIterator, Callable, Optional
from iptv_sniffer.scanner.strategy import ScanStrategy
from iptv_sniffer.scanner.validator import StreamValidator, StreamValidationResult
from iptv_sniffer.scanner.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


@dataclass
class ScanProgress:
    total: int
    completed: int
    valid: int
    invalid: int
    started_at: datetime

    @property
    def percentage(self) -> float:
        return (self.completed / self.total * 100) if self.total > 0 else 0.0


class ScanOrchestrator:
    """Orchestrates scanning with progress tracking"""

    def __init__(self, validator: StreamValidator, max_concurrency: int = 10):
        self.validator = validator
        self.rate_limiter = RateLimiter(max_concurrency=max_concurrency)
        self.progress_callbacks = []

    def on_progress(self, callback: Callable[[ScanProgress], None]):
        """Register progress callback"""
        self.progress_callbacks.append(callback)

    async def execute_scan(
        self, strategy: ScanStrategy
    ) -> AsyncIterator[StreamValidationResult]:
        """Execute scan using strategy"""
        total = strategy.estimate_target_count()
        progress = ScanProgress(
            total=total,
            completed=0,
            valid=0,
            invalid=0,
            started_at=datetime.utcnow()
        )

        logger.info(f"Starting scan: {total} targets")

        async for url in strategy.generate_targets():
            result = await self.rate_limiter.execute(
                self.validator.validate(url)
            )

            progress.completed += 1
            if result.is_valid:
                progress.valid += 1
            else:
                progress.invalid += 1

            # Notify progress callbacks
            for callback in self.progress_callbacks:
                await callback(progress)

            yield result

        logger.info(
            f"Scan completed: {progress.valid} valid, {progress.invalid} invalid"
        )
```

**Definition of Done:**

- [ ] Scan execution works with any strategy
- [ ] Progress tracking accurate
- [ ] Rate limiting applied
- [ ] Test coverage >80%
- [ ] Module <500 lines

---

## Phase 4: M3U Support (Week 8)

**Goal:** Implement M3U parsing and generation with encoding detection.

### Task 4.1: M3U Parser

**Test First (Red):**

```python
# tests/unit/m3u/test_parser.py

def test_parse_simple_m3u():
    """Should parse basic M3U format"""
    content = """#EXTM3U
#EXTINF:-1,CCTV-1
http://192.168.1.100:8000
#EXTINF:-1,CCTV-2
http://192.168.1.101:8000
"""

    parser = M3UParser()
    playlist = parser.parse(content)

    assert len(playlist.channels) == 2
    assert playlist.channels[0].name == "CCTV-1"
    assert playlist.channels[0].url == "http://192.168.1.100:8000"

def test_parse_extended_m3u_attributes():
    """Should parse extended M3U attributes"""
    content = """#EXTM3U
#EXTINF:-1 tvg-id="cctv1" tvg-name="CCTV-1" tvg-logo="http://logo.com/cctv1.png" group-title="央视",CCTV-1
http://192.168.1.100:8000
"""

    parser = M3UParser()
    playlist = parser.parse(content)

    channel = playlist.channels[0]
    assert channel.tvg_id == "cctv1"
    assert channel.tvg_name == "CCTV-1"
    assert channel.tvg_logo == "http://logo.com/cctv1.png"
    assert channel.group_title == "央视"

def test_parse_m3u_handles_malformed_entries():
    """Should skip malformed entries with warning"""
    content = """#EXTM3U
#EXTINF:-1,Valid Channel
http://valid.com
#EXTINF:-1,Missing URL

#EXTINF:-1,Another Valid
http://valid2.com
"""

    parser = M3UParser()
    playlist = parser.parse(content)

    # Should have 2 valid channels (skipped malformed)
    assert len(playlist.channels) == 2
```

**Implement (Green):**

```python
# iptv_sniffer/m3u/parser.py

import logging
import re
from typing import List
from iptv_sniffer.m3u.models import M3UPlaylist, M3UChannel

logger = logging.getLogger(__name__)


class M3UParser:
    """Parser for M3U/M3U8 playlists with extended attributes"""

    def parse(self, content: str) -> M3UPlaylist:
        """Parse M3U content into playlist"""
        lines = content.splitlines()
        channels = []

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            if line.startswith("#EXTINF"):
                attrs = self._parse_extinf(line)
                i += 1

                # Next non-empty line should be URL
                while i < len(lines) and not lines[i].strip():
                    i += 1

                if i < len(lines):
                    url = lines[i].strip()
                    if url and not url.startswith("#"):
                        try:
                            channel = M3UChannel(
                                name=attrs["name"],
                                url=url,
                                tvg_id=attrs.get("tvg-id"),
                                tvg_name=attrs.get("tvg-name"),
                                tvg_logo=attrs.get("tvg-logo"),
                                group_title=attrs.get("group-title")
                            )
                            channels.append(channel)
                        except Exception as e:
                            logger.warning(f"Failed to parse channel: {e}")

            i += 1

        return M3UPlaylist(channels=channels)

    def _parse_extinf(self, line: str) -> dict:
        """Parse EXTINF line attributes"""
        # Extract attributes using regex
        pattern = r'([a-z-]+)="([^"]*)"'
        attrs = dict(re.findall(pattern, line))

        # Extract channel name (after last comma)
        if "," in line:
            name = line.split(",", 1)[1].strip()
            attrs["name"] = name
        else:
            attrs["name"] = "Unknown"

        return attrs
```

**Implement M3U Models:**

```python
# iptv_sniffer/m3u/models.py

from typing import List, Optional
from pydantic import BaseModel


class M3UChannel(BaseModel):
    """M3U channel entry"""
    name: str
    url: str
    tvg_id: Optional[str] = None
    tvg_name: Optional[str] = None
    tvg_logo: Optional[str] = None
    group_title: Optional[str] = None


class M3UPlaylist(BaseModel):
    """M3U playlist containing multiple channels"""
    channels: List[M3UChannel]
```

**Definition of Done:**

- [ ] Basic M3U parsing works
- [ ] Extended attributes parsed correctly
- [ ] Malformed entries handled gracefully
- [ ] Test coverage >85%
- [ ] Module <500 lines

---

### Task 4.2: Character Encoding Detection

**Test First (Red):**

```python
# tests/unit/m3u/test_encoding.py

def test_read_m3u_utf8(tmp_path):
    """Should read UTF-8 encoded M3U files"""
    m3u_file = tmp_path / "playlist.m3u"
    m3u_file.write_text("#EXTM3U\n#EXTINF:-1,测试频道\nhttp://test.com", encoding="utf-8")

    content = read_m3u_file(m3u_file)
    assert "测试频道" in content

def test_read_m3u_gb2312(tmp_path):
    """Should detect and read GB2312 encoded files"""
    m3u_file = tmp_path / "playlist.m3u"
    m3u_file.write_bytes("#EXTM3U\n#EXTINF:-1,测试频道\nhttp://test.com".encode("gb2312"))

    content = read_m3u_file(m3u_file)
    assert "测试频道" in content
```

**Implement (Green):**

```python
# iptv_sniffer/m3u/encoding.py

import chardet
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def read_m3u_file(path: Path) -> str:
    """Read M3U file with automatic encoding detection"""
    # Try UTF-8 first (most common)
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        # Detect encoding
        raw = path.read_bytes()
        detected = chardet.detect(raw)
        encoding = detected["encoding"]
        confidence = detected["confidence"]

        logger.info(
            f"Detected encoding: {encoding} (confidence: {confidence:.2%})"
        )

        if confidence < 0.7:
            logger.warning(f"Low confidence in encoding detection")

        return raw.decode(encoding)
```

**Add Dependency:**

```bash
uv add chardet
```

**Definition of Done:**

- [ ] UTF-8 files read correctly
- [ ] Non-UTF-8 files detected and decoded
- [ ] Test coverage >80%

---

### Task 4.3: M3U Generator

**Test First (Red):**

```python
# tests/unit/m3u/test_generator.py

def test_generate_m3u_from_channels():
    """Should generate valid M3U from channel list"""
    channels = [
        Channel(name="CCTV-1", url="http://test1.com", group="央视"),
        Channel(name="CCTV-2", url="http://test2.com", group="央视"),
    ]

    generator = M3UGenerator()
    m3u_content = generator.generate(channels)

    assert m3u_content.startswith("#EXTM3U")
    assert "CCTV-1" in m3u_content
    assert "http://test1.com" in m3u_content
    assert 'group-title="央视"' in m3u_content

def test_generate_m3u_with_extended_attributes():
    """Should include extended attributes in output"""
    channels = [
        Channel(
            name="CCTV-1",
            url="http://test.com",
            tvg_id="cctv1",
            tvg_logo="http://logo.com/cctv1.png",
            group="央视"
        )
    ]

    generator = M3UGenerator()
    m3u_content = generator.generate(channels)

    assert 'tvg-id="cctv1"' in m3u_content
    assert 'tvg-logo="http://logo.com/cctv1.png"' in m3u_content
```

**Implement (Green):**

```python
# iptv_sniffer/m3u/generator.py

from typing import List
from iptv_sniffer.channel.models import Channel


class M3UGenerator:
    """Generate M3U playlists from channels"""

    def generate(self, channels: List[Channel]) -> str:
        """Generate M3U content from channel list"""
        lines = ["#EXTM3U"]

        for channel in channels:
            # Build EXTINF line
            extinf_parts = ["#EXTINF:-1"]

            if channel.tvg_id:
                extinf_parts.append(f'tvg-id="{channel.tvg_id}"')
            if channel.name:
                extinf_parts.append(f'tvg-name="{channel.name}"')
            if channel.tvg_logo:
                extinf_parts.append(f'tvg-logo="{channel.tvg_logo}"')
            if channel.group:
                extinf_parts.append(f'group-title="{channel.group}"')

            extinf_parts.append(channel.name)

            lines.append(" ".join(extinf_parts))
            lines.append(str(channel.url))

        return "\n".join(lines)
```

**Definition of Done:**

- [ ] M3U generation works correctly
- [ ] Extended attributes included
- [ ] Output compatible with VLC/Kodi
- [ ] Test coverage >85%

---

## Phase 5: Multicast Support (Weeks 9-10)

**Goal:** Implement multicast scanning with smart port detection and presets.

### Task 5.1: Multicast Scan Strategy

**Test First (Red):**

```python
# tests/unit/scanner/test_multicast_strategy.py

@pytest.mark.asyncio
async def test_multicast_strategy_generates_combinations():
    """Should generate all IP × port combinations"""
    strategy = MulticastScanStrategy(
        protocol="rtp",
        ip_ranges=["239.3.1.1-239.3.1.3"],
        ports=[8000, 8004]
    )

    urls = [url async for url in strategy.generate_targets()]

    assert len(urls) == 6  # 3 IPs × 2 ports
    assert "rtp://239.3.1.1:8000" in urls
    assert "rtp://239.3.1.3:8004" in urls

def test_multicast_strategy_estimate_count():
    """Should accurately estimate target count"""
    strategy = MulticastScanStrategy(
        protocol="rtp",
        ip_ranges=["239.3.1.1-239.3.1.10", "239.3.2.1-239.3.2.5"],
        ports=[8000, 8004, 8008]
    )

    # (10 + 5) IPs × 3 ports = 45
    assert strategy.estimate_target_count() == 45
```

**Implement (Green):**

```python
# iptv_sniffer/scanner/multicast_strategy.py

import ipaddress
import logging
from typing import AsyncIterator, List
from iptv_sniffer.scanner.strategy import ScanStrategy

logger = logging.getLogger(__name__)


class MulticastScanStrategy(ScanStrategy):
    """Scan strategy for multicast IP ranges with port lists"""

    def __init__(
        self,
        protocol: str,
        ip_ranges: List[str],
        ports: List[int]
    ):
        self.protocol = protocol
        self.ip_ranges = ip_ranges
        self.ports = ports

    async def generate_targets(self) -> AsyncIterator[str]:
        """Generate all IP × port combinations"""
        for ip_range in self.ip_ranges:
            for ip in self._parse_ip_range(ip_range):
                for port in self.ports:
                    yield f"{self.protocol}://{ip}:{port}"

    def estimate_target_count(self) -> int:
        """Estimate total number of targets"""
        total_ips = sum(
            self._count_ips_in_range(r) for r in self.ip_ranges
        )
        return total_ips * len(self.ports)

    def _parse_ip_range(self, ip_range: str) -> List[str]:
        """Parse IP range string (e.g., '239.3.1.1-239.3.1.10')"""
        if "-" in ip_range:
            start_str, end_str = ip_range.split("-")
            start = ipaddress.ip_address(start_str.strip())
            end = ipaddress.ip_address(end_str.strip())

            ips = []
            current = start
            while current <= end:
                ips.append(str(current))
                current += 1

            return ips
        else:
            return [ip_range.strip()]

    def _count_ips_in_range(self, ip_range: str) -> int:
        """Count IPs in range"""
        if "-" in ip_range:
            start_str, end_str = ip_range.split("-")
            start = int(ipaddress.ip_address(start_str.strip()))
            end = int(ipaddress.ip_address(end_str.strip()))
            return end - start + 1
        return 1
```

**Definition of Done:**

- [ ] Multicast URL generation works
- [ ] IP range parsing correct
- [ ] Target count estimation accurate
- [ ] Test coverage >85%

---

### Task 5.2: Smart Port Scanner

**Test First (Red):**

```python
# tests/unit/scanner/test_smart_port_scanner.py

@pytest.mark.asyncio
async def test_smart_port_scanner_discovers_pattern():
    """Should discover port pattern from first IP"""
    strategy = MulticastScanStrategy(
        protocol="rtp",
        ip_ranges=["239.3.1.1-239.3.1.5"],
        ports=[8000, 8004, 8008, 8012, 8016, 8020]
    )

    # Mock validator to return valid only for ports 8000, 8008
    validator = MagicMock()

    async def mock_validate(url, timeout=10):
        port = int(url.split(":")[-1])
        return StreamValidationResult(
            url=url,
            is_valid=(port in [8000, 8008]),
            protocol="rtp"
        )

    validator.validate.side_effect = mock_validate

    scanner = SmartPortScanner(strategy, validator)
    results = []

    async for result in scanner.scan():
        results.append(result)

    # Should have scanned:
    # - First IP with all 6 ports
    # - Remaining 4 IPs with only 2 discovered ports (8000, 8008)
    # Total: 6 + (4 × 2) = 14 URLs
    assert len(results) <= 14
```

**Implement (Green):**

```python
# iptv_sniffer/scanner/smart_port_scanner.py

import logging
from typing import AsyncIterator, Set
from iptv_sniffer.scanner.multicast_strategy import MulticastScanStrategy
from iptv_sniffer.scanner.validator import StreamValidator, StreamValidationResult

logger = logging.getLogger(__name__)


class SmartPortScanner:
    """
    Smart port scanner with pattern detection.
    Scans first IP with all ports, then applies discovered pattern.
    """

    def __init__(
        self,
        strategy: MulticastScanStrategy,
        validator: StreamValidator,
        enable_smart_scan: bool = True
    ):
        self.strategy = strategy
        self.validator = validator
        self.enable_smart_scan = enable_smart_scan

    async def scan(self) -> AsyncIterator[StreamValidationResult]:
        """Execute scan with smart port detection"""
        if not self.enable_smart_scan:
            # Fall back to full scan
            async for url in self.strategy.generate_targets():
                yield await self.validator.validate(url)
            return

        # Phase 1: Scan first IP with all ports
        discovered_ports = await self._discover_ports_on_first_ip()

        if not discovered_ports:
            logger.warning("No valid ports discovered on first IP")
            return

        logger.info(f"Discovered {len(discovered_ports)} valid ports: {discovered_ports}")

        # Phase 2: Scan remaining IPs with discovered ports only
        async for result in self._scan_remaining_ips(discovered_ports):
            yield result

    async def _discover_ports_on_first_ip(self) -> Set[int]:
        """Scan first IP with all ports to discover pattern"""
        discovered = set()

        first_ip = self._get_first_ip()
        logger.info(f"Discovering port pattern on {first_ip}")

        for port in self.strategy.ports:
            url = f"{self.strategy.protocol}://{first_ip}:{port}"
            result = await self.validator.validate(url, timeout=20)

            if result.is_valid:
                discovered.add(port)

        return discovered

    async def _scan_remaining_ips(
        self, ports: Set[int]
    ) -> AsyncIterator[StreamValidationResult]:
        """Scan remaining IPs with discovered ports"""
        first_ip = self._get_first_ip()

        for ip_range in self.strategy.ip_ranges:
            for ip in self.strategy._parse_ip_range(ip_range):
                if ip == first_ip:
                    continue  # Skip first IP (already scanned)

                for port in ports:
                    url = f"{self.strategy.protocol}://{ip}:{port}"
                    yield await self.validator.validate(url, timeout=20)

    def _get_first_ip(self) -> str:
        """Get first IP from ranges"""
        first_range = self.strategy.ip_ranges[0]
        return self.strategy._parse_ip_range(first_range)[0]
```

**Definition of Done:**

- [ ] Smart scanning reduces URL count by ~80%
- [ ] Pattern discovery works correctly
- [ ] Fallback to full scan available
- [ ] Test coverage >75%
- [ ] Module <500 lines

---

### Task 5.3: Scan Preset System

**Test First (Red):**

```python
# tests/unit/scanner/test_presets.py

def test_load_presets_from_json(tmp_path):
    """Should load multicast presets from JSON"""
    preset_file = tmp_path / "presets.json"
    preset_file.write_text('''
    {
      "presets": [
        {
          "id": "beijing-unicom",
          "name": "北京联通 IPTV",
          "protocol": "rtp",
          "ip_ranges": ["239.3.1.1-239.3.1.10"],
          "ports": [8000, 8004, 8008]
        }
      ]
    }
    ''')

    loader = PresetLoader(preset_file)
    presets = loader.load_all()

    assert len(presets) == 1
    assert presets[0].id == "beijing-unicom"
    assert presets[0].protocol == "rtp"

def test_get_preset_by_id(tmp_path):
    """Should retrieve specific preset by ID"""
    preset_file = tmp_path / "presets.json"
    preset_file.write_text('''
    {
      "presets": [
        {"id": "preset-1", "name": "Test 1", "protocol": "rtp", "ip_ranges": [], "ports": []},
        {"id": "preset-2", "name": "Test 2", "protocol": "rtp", "ip_ranges": [], "ports": []}
      ]
    }
    ''')

    loader = PresetLoader(preset_file)
    preset = loader.get_by_id("preset-2")

    assert preset.id == "preset-2"
    assert preset.name == "Test 2"

def test_create_strategy_from_preset():
    """Should create MulticastScanStrategy from preset"""
    preset = ScanPreset(
        id="test",
        name="Test Preset",
        protocol="rtp",
        ip_ranges=["239.3.1.1-239.3.1.5"],
        ports=[8000, 8004]
    )

    strategy = preset.to_strategy()

    assert isinstance(strategy, MulticastScanStrategy)
    assert strategy.protocol == "rtp"
    assert strategy.estimate_target_count() == 10  # 5 IPs × 2 ports
```

**Implement (Green):**

```python
# iptv_sniffer/scanner/presets.py

import json
import logging
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel
from iptv_sniffer.scanner.multicast_strategy import MulticastScanStrategy

logger = logging.getLogger(__name__)


class ScanPreset(BaseModel):
    """Multicast scan preset configuration"""
    id: str
    name: str
    description: Optional[str] = None
    protocol: str
    ip_ranges: List[str]
    ports: List[int]
    estimated_targets: Optional[int] = None
    estimated_duration: Optional[str] = None
    reference: Optional[str] = None

    def to_strategy(self) -> MulticastScanStrategy:
        """Convert preset to scan strategy"""
        return MulticastScanStrategy(
            protocol=self.protocol,
            ip_ranges=self.ip_ranges,
            ports=self.ports
        )


class PresetLoader:
    """Load scan presets from JSON configuration"""

    def __init__(self, preset_file: Path):
        self.preset_file = preset_file

    def load_all(self) -> List[ScanPreset]:
        """Load all presets from file"""
        if not self.preset_file.exists():
            logger.warning(f"Preset file not found: {self.preset_file}")
            return []

        with open(self.preset_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        presets = [ScanPreset(**p) for p in data.get("presets", [])]
        logger.info(f"Loaded {len(presets)} presets")

        return presets

    def get_by_id(self, preset_id: str) -> Optional[ScanPreset]:
        """Get specific preset by ID"""
        presets = self.load_all()
        return next((p for p in presets if p.id == preset_id), None)
```

**Create Default Presets:**

```json
// config/multicast_presets.json

{
  "presets": [
    {
      "id": "beijing-unicom",
      "name": "北京联通 IPTV",
      "description": "Beijing Unicom multicast IPTV (239.3.1.x)",
      "protocol": "rtp",
      "ip_ranges": ["239.3.1.1-239.3.1.255"],
      "ports": [
        8000, 8004, 8008, 8012, 8016, 8020, 8024, 8028, 8032, 8036, 8040, 8044,
        8048, 8052, 8056, 8060, 8064, 8068, 8072, 8076, 8080, 8084, 8088, 8092,
        8096, 8100, 8104, 8108, 8112, 8116, 8120
      ],
      "estimated_targets": 7905,
      "estimated_duration": "3-4 hours (with smart scanning)",
      "reference": "https://github.com/qwerttvv/Beijing-IPTV"
    },
    {
      "id": "shanghai-telecom",
      "name": "上海电信 IPTV",
      "protocol": "rtp",
      "ip_ranges": ["239.45.0.1-239.45.3.255"],
      "ports": [9000, 9004, 9008, 9012, 9016],
      "estimated_targets": 5120
    }
  ]
}
```

**Definition of Done:**

- [ ] Preset loading works
- [ ] Strategy creation from preset works
- [ ] Default presets file created
- [ ] Test coverage >80%

---

## Phase 6: Web API (Weeks 11-12)

**Goal:** Build FastAPI REST endpoints with WebSocket progress updates.

### Task 6.1: FastAPI Setup

**Test First (Red):**

```python
# tests/integration/web/test_app.py

from fastapi.testclient import TestClient
from iptv_sniffer.web.app import app

client = TestClient(app)

def test_health_endpoint():
    """Health check should return 200 OK"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_openapi_docs_available():
    """OpenAPI documentation should be accessible"""
    response = client.get("/docs")
    assert response.status_code == 200

def test_cors_headers():
    """CORS headers should be present"""
    response = client.get("/health", headers={"Origin": "http://localhost:3000"})
    assert "access-control-allow-origin" in response.headers
```

**Implement (Green):**

```python
# iptv_sniffer/web/app.py

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from iptv_sniffer import __version__
from iptv_sniffer.utils.config import AppConfig
from iptv_sniffer.utils.ffmpeg import check_ffmpeg_installed

logger = logging.getLogger(__name__)

app = FastAPI(
    title="iptv-sniffer",
    description="Discover and validate IPTV channels on local networks",
    version=__version__
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info(f"Starting iptv-sniffer v{__version__}")

    # Verify FFmpeg available
    if not check_ffmpeg_installed():
        logger.error("FFmpeg not found. Install: apt-get install ffmpeg")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "version": __version__,
        "checks": {
            "ffmpeg": check_ffmpeg_installed()
        }
    }
```

**Definition of Done:**

- [ ] FastAPI app starts successfully
- [ ] Health endpoint works
- [ ] OpenAPI docs accessible
- [ ] CORS configured

---

### Task 6.2: Scan Endpoints

**Test First (Red):**

```python
# tests/integration/web/test_scan_endpoints.py

from fastapi.testclient import TestClient
from iptv_sniffer.web.app import app

client = TestClient(app)

def test_start_template_scan():
    """Should start template scan and return scan ID"""
    response = client.post("/api/scan/start", json={
        "mode": "template",
        "base_url": "http://192.168.2.2:7788/rtp/{ip}:8000",
        "start_ip": "192.168.1.1",
        "end_ip": "192.168.1.10"
    })

    assert response.status_code == 200
    data = response.json()
    assert "scan_id" in data
    assert data["status"] == "pending"

def test_get_scan_status():
    """Should retrieve scan status"""
    # Start scan
    start_response = client.post("/api/scan/start", json={
        "mode": "template",
        "base_url": "http://test.com/{ip}",
        "start_ip": "192.168.1.1",
        "end_ip": "192.168.1.3"
    })
    scan_id = start_response.json()["scan_id"]

    # Get status
    status_response = client.get(f"/api/scan/{scan_id}")
    assert status_response.status_code == 200

    data = status_response.json()
    assert data["scan_id"] == scan_id
    assert "progress" in data
    assert "total" in data

def test_cancel_scan():
    """Should cancel running scan"""
    # Start scan
    start_response = client.post("/api/scan/start", json={
        "mode": "template",
        "base_url": "http://test.com/{ip}",
        "start_ip": "192.168.1.1",
        "end_ip": "192.168.1.100"
    })
    scan_id = start_response.json()["scan_id"]

    # Cancel scan
    cancel_response = client.delete(f"/api/scan/{scan_id}")
    assert cancel_response.status_code == 200
    assert cancel_response.json()["cancelled"] is True
```

**Implement (Green):**

```python
# iptv_sniffer/web/api/scan.py

import asyncio
import logging
from datetime import datetime
from enum import Enum
from typing import Dict, Optional, List
from uuid import uuid4
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field
from iptv_sniffer.scanner.strategy import ScanMode
from iptv_sniffer.scanner.template_strategy import TemplateScanStrategy
from iptv_sniffer.scanner.multicast_strategy import MulticastScanStrategy
from iptv_sniffer.scanner.validator import StreamValidator
from iptv_sniffer.scanner.orchestrator import ScanOrchestrator

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/scan", tags=["scan"])

# Global scan registry
active_scans: Dict[str, dict] = {}


class ScanStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class ScanStartRequest(BaseModel):
    mode: ScanMode

    # Template mode fields
    base_url: Optional[str] = None
    start_ip: Optional[str] = None
    end_ip: Optional[str] = None

    # Multicast mode fields
    protocol: Optional[str] = None
    ip_ranges: Optional[List[str]] = None
    ports: Optional[List[int]] = None
    preset: Optional[str] = None

    timeout: int = Field(default=10, ge=1, le=60)


class ScanStatusResponse(BaseModel):
    scan_id: str
    status: ScanStatus
    progress: int
    total: int
    valid: int
    invalid: int
    started_at: datetime
    completed_at: Optional[datetime] = None


@router.post("/start")
async def start_scan(
    request: ScanStartRequest,
    background_tasks: BackgroundTasks
):
    """Start a new scan"""
    scan_id = str(uuid4())

    # Create strategy based on mode
    if request.mode == ScanMode.TEMPLATE:
        if not all([request.base_url, request.start_ip, request.end_ip]):
            raise HTTPException(400, "Missing required template mode fields")

        strategy = TemplateScanStrategy(
            base_url=request.base_url,
            start_ip=request.start_ip,
            end_ip=request.end_ip
        )

    elif request.mode == ScanMode.MULTICAST:
        if not all([request.protocol, request.ip_ranges, request.ports]):
            raise HTTPException(400, "Missing required multicast mode fields")

        strategy = MulticastScanStrategy(
            protocol=request.protocol,
            ip_ranges=request.ip_ranges,
            ports=request.ports
        )

    else:
        raise HTTPException(400, f"Unsupported scan mode: {request.mode}")

    # Register scan
    active_scans[scan_id] = {
        "status": ScanStatus.PENDING,
        "progress": 0,
        "total": strategy.estimate_target_count(),
        "valid": 0,
        "invalid": 0,
        "started_at": datetime.utcnow(),
        "completed_at": None
    }

    # Start scan in background
    background_tasks.add_task(execute_scan, scan_id, strategy)

    return {
        "scan_id": scan_id,
        "status": ScanStatus.PENDING,
        "estimated_targets": strategy.estimate_target_count()
    }


@router.get("/{scan_id}")
async def get_scan_status(scan_id: str) -> ScanStatusResponse:
    """Get scan status"""
    if scan_id not in active_scans:
        raise HTTPException(404, "Scan not found")

    scan_data = active_scans[scan_id]
    return ScanStatusResponse(scan_id=scan_id, **scan_data)


@router.delete("/{scan_id}")
async def cancel_scan(scan_id: str):
    """Cancel running scan"""
    if scan_id not in active_scans:
        raise HTTPException(404, "Scan not found")

    active_scans[scan_id]["status"] = ScanStatus.CANCELLED

    return {"cancelled": True}


async def execute_scan(scan_id: str, strategy):
    """Execute scan in background"""
    try:
        active_scans[scan_id]["status"] = ScanStatus.RUNNING

        validator = StreamValidator(max_workers=10)
        orchestrator = ScanOrchestrator(validator, max_concurrency=10)

        async for result in orchestrator.execute_scan(strategy):
            # Update progress
            scan_data = active_scans[scan_id]
            scan_data["progress"] += 1

            if result.is_valid:
                scan_data["valid"] += 1
            else:
                scan_data["invalid"] += 1

            # Check for cancellation
            if scan_data["status"] == ScanStatus.CANCELLED:
                logger.info(f"Scan {scan_id} cancelled")
                return

        # Mark completed
        active_scans[scan_id]["status"] = ScanStatus.COMPLETED
        active_scans[scan_id]["completed_at"] = datetime.utcnow()

    except Exception as e:
        logger.error(f"Scan {scan_id} failed: {e}")
        active_scans[scan_id]["status"] = ScanStatus.FAILED
```

**Register Router:**

```python
# iptv_sniffer/web/app.py (add to existing file)

from iptv_sniffer.web.api import scan

app.include_router(scan.router)
```

**Definition of Done:**

- [ ] Scan start endpoint works
- [ ] Status retrieval works
- [ ] Cancellation works
- [ ] Background execution works
- [ ] Test coverage >75%

---

## Phase 7: Web Interface & Product Integration (Weeks 13-17)

**Goal:** Build complete web frontend to enable end-user product usage, completing the journey from backend infrastructure to usable product.

**Context:** Phase 1-6 delivered robust backend capabilities (scanning, validation, M3U support, REST API foundation), but the product lacks any user interface. This phase bridges the gap by implementing:

- Web UI for all core workflows (scan, manage, export)
- Frontend-backend integration with Vue 3 + Vite
- Real-time progress updates
- Channel grouping system
- Production-ready polish

**Frontend Technology Stack:**

- **Framework:** Vue 3.4+ (Composition API with `<script setup>`)
- **Build Tool:** Vite 5+
- **Language:** TypeScript 5+ (optional but recommended)
- **UI Framework:** Tailwind CSS 3+ (via PostCSS)
- **Component Library:** Headless UI (@headlessui/vue)
- **HTTP Client:** Axios 1+
- **State Management:** Pinia 2+ (when needed for cross-component state)

**Priority Matrix:**

- **P0 (Critical):** MVP usability - Frontend Setup + Stream Test page (Tasks 7.0-7.2)
- **P1 (High):** Complete feature parity - Channel Management + M3U workflows (Tasks 7.3-7.4)
- **P2 (Medium):** Advanced UX - Grouping + Real-time updates (Tasks 7.5-7.6)
- **P3 (Low):** Optional enhancements - AI recognition + i18n (Tasks 7.7-7.8)

---

### Task 7.0: Vue 3 + Vite Frontend Setup (P0)

**Priority:** P0 - Foundation for all frontend development

**Test First (Red):**

```python
# tests/unit/web/test_frontend_build.py

import subprocess
from pathlib import Path

def test_frontend_build_succeeds():
    """Frontend build should complete without errors"""
    frontend_dir = Path("frontend")
    result = subprocess.run(
        ["npm", "run", "build"],
        cwd=frontend_dir,
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert (frontend_dir / "dist" / "index.html").exists()

def test_vite_config_proxy_configured():
    """Vite should proxy API requests to FastAPI backend"""
    vite_config = Path("frontend/vite.config.ts")
    content = vite_config.read_text()
    assert "proxy" in content
    assert "/api" in content
    assert "http://localhost:8000" in content
```

**Implement (Green):**

#### Step 1: Initialize Vue 3 + Vite Project

```bash
# Create frontend directory
cd ~/workspace/iptv-sniffer
npm create vite@latest frontend -- --template vue-ts

# Install dependencies
cd frontend
npm install

# Install Tailwind CSS and Headless UI
npm install -D tailwindcss postcss autoprefixer
npm install @headlessui/vue
npx tailwindcss init -p

# Install Axios for HTTP client
npm install axios
```

#### Step 2: Configure Vite Proxy

```typescript
// frontend/vite.config.ts

import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import path from "path";

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: "../iptv_sniffer/web/static",
    emptyOutDir: true,
  },
});
```

#### Step 3: Configure Tailwind CSS

```javascript
// frontend/tailwindcss.config.js

/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{vue,js,ts,jsx,tsx}"],
  theme: {
    extend: {},
  },
  plugins: [],
};
```

```css
/* frontend/src/style.css */

@tailwind base;
@tailwind components;
@tailwind utilities;

@layer components {
  .btn {
    @apply px-4 py-2 rounded-lg font-medium transition-colors;
  }

  .btn-primary {
    @apply bg-blue-600 text-white hover:bg-blue-700;
  }

  .btn-secondary {
    @apply bg-gray-200 text-gray-800 hover:bg-gray-300;
  }

  .card {
    @apply bg-white rounded-lg shadow-md p-6;
  }

  .input-field {
    @apply w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500;
  }
}
```

#### Step 4: Create API Client

```typescript
// frontend/src/api/client.ts

import axios, { AxiosInstance, AxiosResponse } from "axios";

const apiClient: AxiosInstance = axios.create({
  baseURL: "/api",
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error) => {
    const message =
      error.response?.data?.detail || error.message || "Request failed";
    console.error("API Error:", message);
    return Promise.reject(new Error(message));
  }
);

export default apiClient;
```

```typescript
// frontend/src/api/scan.ts

import apiClient from "./client";

export interface ScanStartRequest {
  mode: "template" | "multicast" | "m3u_batch";
  base_url?: string;
  start_ip?: string;
  end_ip?: string;
  protocol?: string;
  ip_ranges?: string[];
  ports?: number[];
  timeout?: number;
}

export interface ScanStatusResponse {
  scan_id: string;
  status: "pending" | "running" | "completed" | "cancelled" | "failed";
  progress: number;
  total: number;
  valid: number;
  invalid: number;
  started_at: string;
  completed_at?: string;
}

export const scanAPI = {
  start: (data: ScanStartRequest) =>
    apiClient.post<{ scan_id: string }>("/scan/start", data),

  getStatus: (scanId: string) =>
    apiClient.get<ScanStatusResponse>(`/scan/${scanId}`),

  cancel: (scanId: string) => apiClient.delete(`/scan/${scanId}`),
};
```

#### Step 5: Update FastAPI to Serve Vue Build

```python
# iptv_sniffer/web/app.py (modify existing)

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

app = FastAPI(
    title="iptv-sniffer",
    description="Discover and validate IPTV channels on local networks",
    version=__version__
)

# Mount static files (Vue build output)
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(static_dir / "assets")), name="assets")

# Serve index.html for all non-API routes (Vue Router history mode)
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    """Serve Vue SPA for all non-API routes"""
    if full_path.startswith("api/"):
        # Let FastAPI handle API routes
        return

    index_path = static_dir / "index.html"
    if index_path.exists():
        return FileResponse(index_path)

    # Development mode: proxy to Vite dev server
    return {"message": "Run 'npm run dev' in frontend/ directory"}
```

**Frontend Project Structure:**

```text
frontend/
├── package.json           # NPM dependencies
├── vite.config.ts         # Vite configuration with proxy
├── tailwind.config.js     # Tailwind CSS configuration
├── tsconfig.json          # TypeScript configuration
├── index.html             # HTML entry point
└── src/
    ├── main.ts            # Vue app entry point
    ├── App.vue            # Root component with router-view
    ├── style.css          # Tailwind CSS imports
    ├── api/               # API client layer
    │   ├── client.ts      # Axios instance with interceptors
    │   ├── scan.ts        # Scan API methods
    │   └── channels.ts    # Channel API methods (Task 7.3)
    ├── components/        # Reusable UI components
    │   ├── BaseButton.vue
    │   ├── BaseCard.vue
    │   ├── BaseModal.vue
    │   └── Toast.vue
    ├── views/             # Page-level components
    │   ├── StreamTest.vue # Stream Test page
    │   ├── Channels.vue   # TV Channels page
    │   ├── Groups.vue     # TV Groups page
    │   └── Settings.vue   # Settings page
    ├── router/            # Vue Router configuration
    │   └── index.ts       # Route definitions
    └── types/             # TypeScript type definitions
        └── api.ts         # API response types
```

**Definition of Done:**

- [ ] Vite project initialized with Vue 3 + TypeScript
- [ ] Tailwind CSS configured and working
- [ ] Vite proxy correctly forwards /api requests to FastAPI
- [ ] Frontend build outputs to iptv_sniffer/web/static/
- [ ] FastAPI serves Vue SPA for non-API routes
- [ ] API client with error handling implemented
- [ ] Development server runs on <http://localhost:5173>
- [ ] Production build verified

---

### Task 7.1: Vue Router + Tab Navigation (P0)

**Priority:** P0 - Core navigation structure

**Description:** Implement Vue Router with tab-based navigation for 4 main application pages.

**Key Deliverables:**

- Vue Router configuration with history mode
- App.vue root component with tab navigation using Headless UI
- Route guards for future authentication
- Placeholder view components for all pages

**Implementation Details:** See `docs/prompts/task-7.1-vue-router-tab-navigation.md`

**Definition of Done:**

- [ ] Vue Router 4 configured with 4 routes
- [ ] Tab navigation working with active state indication
- [ ] Keyboard navigation accessible (Tab/Enter/Arrow keys)
- [ ] Responsive layout on mobile/tablet/desktop
- [ ] All route transition tests pass
- [ ] No console errors or warnings

---

### Task 7.2: Stream Test Page with Vue (P0)

**Priority:** P0 - Core user workflow (scan discovery)

**Description:** Implement Stream Test page using Vue 3 Composition API with scan configuration form, real-time progress tracking via HTTP polling, and results display with filtering.

**Key Components:**

- `StreamTest.vue` - Main page component with reactive scan state
- `ScanConfigForm.vue` - Input form for base URL and IP range
- `ScanProgress.vue` - Real-time progress bar with statistics
- `ChannelResultsGrid.vue` - Filterable channel results with screenshots
- `Toast.vue` - Toast notification component for user feedback

**Implementation Details:** See `docs/prompts/task-7.2-vue-stream-test-page.md`

**Definition of Done:**

- [ ] Form validates input (URL pattern, IP format) with Vuelidate
- [ ] Scan starts and returns scan_id
- [ ] Progress bar updates every second via HTTP polling
- [ ] Results display with screenshot thumbnails
- [ ] Filter buttons work correctly (All/Success/Failed/4K/1080p/720p)
- [ ] Cancel button stops scan
- [ ] Mobile responsive layout
- [ ] Unit tests for all components >80% coverage
- [ ] E2E test for scan workflow with Playwright

---

### Task 7.3: Screenshot Display with Vue (P0)

**Priority:** P0 - Critical for visual validation

**Description:** Implement screenshot display components using Vue 3 with lazy loading, lightbox modal, and secure FastAPI endpoint for serving screenshot images.

**Key Components:**

- `ChannelCard.vue` - Channel card with screenshot thumbnail
- `ImageLightbox.vue` - Full-screen image viewer with Headless UI Dialog
- Screenshot API endpoint (`/api/screenshots/{filename}`) with path traversal protection

**Implementation Details:** See `docs/prompts/task-7.3-vue-screenshot-display.md`

**Definition of Done:**

- [ ] Screenshot endpoint serves images correctly with security headers
- [ ] Path traversal attack prevented
- [ ] Lazy loading implemented with `<img loading="lazy">`
- [ ] Lightbox modal with Headless UI Dialog for accessibility
- [ ] Placeholder image for missing screenshots
- [ ] Cache headers configured (`Cache-Control: public, max-age=3600`)
- [ ] Unit tests for screenshot API >80% coverage
- [ ] E2E test for lightbox interaction

---

### Task 7.4: Channel Management Page with Vue (P1)

**Priority:** P1 - Required for channel browsing and CRUD operations

**Description:** Implement TV Channels page with Vue 3, featuring filterable channel list, inline editing, batch operations, and pagination with FastAPI backend support.

**Key Components:**

- `TVChannels.vue` - Main channel management page
- `ChannelTable.vue` - Data table with sorting and filtering
- `ChannelEditModal.vue` - Modal for editing channel metadata
- `BatchActionBar.vue` - Batch delete/validate/export actions
- Channel API (`/api/channels`) - CRUD endpoints with pagination and filtering

**Implementation Details:** See `docs/prompts/task-7.4-vue-channel-management.md`

**Definition of Done:**

- [ ] Channel list displays with pagination (default 50 per page)
- [ ] Filters work: group, resolution, status (online/offline), search
- [ ] Inline editing for channel name, logo, group, TVG metadata
- [ ] Batch operations: delete, validate, export selected channels
- [ ] Virtual scrolling for large channel lists (>1000 channels)
- [ ] Backend API tests pass with >80% coverage
- [ ] Frontend component tests pass with >75% coverage
- [ ] OpenAPI documentation updated

---

### Task 7.5: M3U Import/Export with Vue (P1)

**Priority:** P1 - Core workflow for existing playlists

**Description:** Implement M3U file import/export functionality with Vue 3 drag-and-drop uploader, progress tracking, and character encoding detection. Backend API handles M3U parsing and generation.

**Key Components:**

- `M3UImport.vue` - File upload component with drag-and-drop support
- `ImportProgress.vue` - Import progress tracker with validation status
- `M3UExportModal.vue` - Export configuration modal with filter options
- M3U API (`/api/m3u`) - Import/export endpoints with encoding detection

**Implementation Details:** See `docs/prompts/task-7.5-vue-m3u-import-export.md`

**Definition of Done:**

- [ ] Drag-and-drop M3U file upload works
- [ ] Character encoding detection accurate (UTF-8, GB2312, auto-detect)
- [ ] Import progress displays: total channels, imported, failed with error reasons
- [ ] Export modal with filters: group, resolution, status, custom selection
- [ ] Generated M3U file is VLC playable
- [ ] Large file support (>10,000 channels) with streaming
- [ ] Backend API tests pass with >80% coverage
- [ ] Frontend component tests pass with >75% coverage

---

(Continue with Tasks 7.6-7.9 following same pattern...)

## Summary

This development plan provides a comprehensive TDD-driven roadmap covering:

- **9 Phases** over 17 weeks
- **70+ Test-First Tasks** with explicit Red-Green-Refactor cycles
- **Clear Definition of Done** for each task with measurable criteria
- **Quality Gates:** pyrefly check, ruff check, >80% test coverage, <500 lines per module

**Phase 7 adds:**

- **9 additional tasks** for Web Interface with Vue 3 + Vite (Weeks 13-17)
- **Modern frontend stack:** Vue 3 Composition API + TypeScript + Tailwind CSS + Headless UI
- **Priority-driven approach:** P0 (MVP) → P1 (Core) → P2 (Advanced) → P3 (Optional)
- **Frontend-backend integration** completing the product journey from CLI to full web application
- **Production-ready polish** with Vite optimized builds and Docker deployment support

Each task follows strict TDD discipline:

1. Write failing tests that define expected behavior
2. Implement minimal code to pass tests
3. Refactor for code quality while maintaining green tests
4. Verify all quality gates before moving to next task

This ensures high code quality, comprehensive test coverage, and architectural integrity throughout the development lifecycle.
