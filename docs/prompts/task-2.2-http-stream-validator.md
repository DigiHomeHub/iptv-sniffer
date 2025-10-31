# Task 2.2: HTTP Stream Validator

## Task Overview

**Phase**: 2 - FFmpeg Integration  
**Duration**: 4-5 hours  
**Complexity**: Medium

**Goal**: Implement protocol-aware stream validation using ffmpeg-python library, supporting HTTP/HTTPS/RTP/RTSP/UDP protocols with timeout enforcement and structured error handling.

**Success Criteria**:

- [ ] All tests pass (pytest with asyncio)
- [ ] Type checking passes (mypy --strict)
- [ ] Code style compliant (ruff check)
- [ ] Test coverage ≥ 80%
- [ ] Module size < 500 lines

---

## Design Context

### Architectural Decisions (from Design.md)

**ffmpeg-python Integration** (Design.md Section 5, lines 428-520):

- Use ffmpeg-python library (type-safe, prevents command injection)
- Integrate with async architecture via `asyncio.run_in_executor()` + `ThreadPoolExecutor`
- Timeout enforcement critical (default 10s, configurable up to 60s)
- Capture stderr for diagnostic error messages

**Multi-Protocol Support** (Design.md Section 12, lines 982-1080):

- HTTP/HTTPS: Standard timeout (10s)
- RTP (multicast): Extended timeout (20s), special buffer options
- RTSP: TCP transport mode for reliability
- UDP: Standard handling similar to RTP
- Protocol-specific error categorization

**Hybrid Async-Thread Model** (Design.md Section 4, lines 369-426):

- AsyncIO for network-facing API (non-blocking)
- ThreadPoolExecutor for blocking FFmpeg calls
- ThreadPoolExecutor size: 10 workers default (matches max_concurrency)

### Key Constraints

- **No subprocess strings**: Use ffmpeg-python, never `subprocess.run(shell=True)`
- **Mandatory timeouts**: All FFmpeg operations must have timeout
- **Error categorization**: Parse stderr to categorize failure reasons
- **Async interface**: All public methods async (even if wrapping sync FFmpeg)

---

## Prerequisites

### Required Completed Tasks

- [x] Task 1.1: Channel Data Model (provides ValidationStatus enum)
- [x] Task 2.1: FFmpeg Availability Check (ensures FFmpeg installed)

### Required Dependencies

```bash
# Add ffmpeg-python library
uv add ffmpeg-python

# Verify installation
python -c "import ffmpeg; print(ffmpeg.__version__)"
```

### Dependency Verification

```bash
# Ensure FFmpeg installed
ffmpeg -version

# Ensure previous tasks completed
python -c "
from iptv_sniffer.channel.models import ValidationStatus
from iptv_sniffer.utils.ffmpeg import check_ffmpeg_installed
assert check_ffmpeg_installed()
print('Prerequisites: OK')
"
```

---

## TDD Implementation Guide

### Phase 1: Red - Write Failing Tests

**Test File**: `tests/unit/scanner/test_validator.py`

#### Test Strategy

Cover these dimensions:

1. **HTTP Success**: Valid HTTP stream returns metadata
2. **Protocol Detection**: Correct validator selected by URL scheme
3. **Timeout Handling**: Long-running probes timeout gracefully
4. **No Video Stream**: Audio-only streams rejected
5. **Network Errors**: Connection failures categorized correctly
6. **FFmpeg Errors**: Parse stderr for specific error types

#### Core Test Cases

```python
@pytest.mark.asyncio
async def test_validate_http_stream_success():
    """
    Design Intent: HTTP streams validated via FFmpeg probe
    Validates: Extract resolution, codec, return StreamValidationResult
    """

@pytest.mark.asyncio
async def test_validate_stream_timeout():
    """
    Design Intent: Non-responsive streams don't block forever
    Validates: Timeout error categorized as ErrorCategory.TIMEOUT
    """

@pytest.mark.asyncio
async def test_validate_stream_no_video():
    """
    Design Intent: Reject audio-only streams (IPTV requires video)
    Validates: ErrorCategory.NO_VIDEO_STREAM returned
    """

@pytest.mark.asyncio
async def test_validate_rtp_stream_uses_extended_timeout():
    """
    Design Intent: Multicast needs longer timeout for IGMP join
    Validates: RTP validator uses ≥20 second timeout
    """

@pytest.mark.asyncio
async def test_validate_unsupported_protocol():
    """
    Design Intent: Graceful handling of unknown protocols
    Validates: Return is_valid=False, ErrorCategory.UNSUPPORTED_PROTOCOL
    """

@pytest.mark.asyncio
async def test_validate_parses_ffmpeg_stderr():
    """
    Design Intent: Actionable error messages from FFmpeg output
    Validates: Parse stderr for specific error patterns
    """
```

#### Expected Failure Points

- `StreamValidator` class doesn't exist
- `StreamValidationResult` dataclass not defined
- `ErrorCategory` enum not defined
- Protocol-specific validators not implemented

Run tests:

```bash
uv run pytest tests/unit/scanner/test_validator.py -v
```

### Phase 2: Green - Minimal Implementation

**Implementation Files**:

- `iptv_sniffer/scanner/validator.py` (main implementation)

#### Implementation Strategy

1. Define `ErrorCategory` enum with error types
2. Define `StreamValidationResult` dataclass
3. Create `StreamValidator` class with ThreadPoolExecutor
4. Implement protocol dispatch via `_detect_protocol()`
5. Implement protocol-specific validators: `_validate_http()`, `_validate_rtp()`, etc.
6. Parse FFmpeg probe results to extract metadata
7. Handle FFmpeg errors with categorization

#### Type Signatures (Required)

```python
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
    timestamp: datetime = field(default_factory=datetime.utcnow)

class StreamValidator:
    def __init__(self, max_workers: int = 10):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.validators: Dict[str, Callable] = {...}

    async def validate(self, url: str, timeout: int = 10) -> StreamValidationResult:
        """Validate stream with protocol-specific handler"""
        ...

    def _detect_protocol(self, url: str) -> str:
        """Extract protocol from URL"""
        ...

    def _validate_http(self, url: str, timeout: int) -> StreamValidationResult:
        """Validate HTTP/HTTPS stream (synchronous, runs in thread pool)"""
        ...

    def _validate_rtp(self, url: str, timeout: int) -> StreamValidationResult:
        """Validate RTP multicast stream"""
        ...

    def _parse_probe_result(self, url: str, protocol: str, probe: dict) -> StreamValidationResult:
        """Extract stream info from FFmpeg probe"""
        ...

    def _handle_ffmpeg_error(self, url: str, protocol: str, error: ffmpeg.Error) -> StreamValidationResult:
        """Parse FFmpeg error into structured result"""
        ...
```

#### Implementation Checklist

- [ ] Create `iptv_sniffer/scanner/` directory
- [ ] Import `ffmpeg`, `asyncio`, `logging`, `concurrent.futures`
- [ ] Define `ErrorCategory` and `StreamValidationResult`
- [ ] Create `StreamValidator` with ThreadPoolExecutor
- [ ] Use `urlparse()` in `_detect_protocol()`
- [ ] Call `ffmpeg.probe()` with timeout parameter
- [ ] Use `asyncio.run_in_executor()` to wrap sync validators
- [ ] Parse probe dict to find video/audio streams
- [ ] Extract width/height for resolution, codec_name for codecs
- [ ] Catch `ffmpeg.Error` and parse stderr with `.decode()`
- [ ] Match error patterns: "timeout", "no route to host", etc.
- [ ] Return structured `StreamValidationResult` in all cases

#### Common Pitfalls

❌ **Don't**: Make validator methods async

- Why: ffmpeg-python is blocking, can't be awaited
- Fix: Keep validators sync, wrap in `run_in_executor()`

❌ **Don't**: Use `shell=True` or command strings

- Why: Project requirement (AGENTS.md) + security
- Fix: Use ffmpeg-python library methods

❌ **Don't**: Forget timeout on ffmpeg.probe()

- Why: Non-responsive streams hang forever
- Fix: Always pass timeout parameter

❌ **Don't**: Raise exceptions from validators

- Why: Caller expects StreamValidationResult
- Fix: Catch all exceptions, return result with is_valid=False

✅ **Do**: Log stderr output for debugging
✅ **Do**: Use longer timeout for RTP (20s minimum)
✅ **Do**: Return consistent StreamValidationResult structure

### Phase 3: Refactor - Code Quality

#### Refactoring Checklist

- [ ] **Extract Error Pattern Matching**: Separate function

  ```python
  def _categorize_ffmpeg_error(stderr: str) -> ErrorCategory:
      """Categorize error from FFmpeg stderr output"""
      stderr_lower = stderr.lower()
      if "timeout" in stderr_lower:
          return ErrorCategory.TIMEOUT
      if "no route" in stderr_lower:
          return ErrorCategory.MULTICAST_NOT_SUPPORTED
      return ErrorCategory.NETWORK_UNREACHABLE
  ```

- [ ] **Add Structured Logging**:

  ```python
  logger.info(
      "Stream validation started",
      extra={"url": url, "protocol": protocol, "timeout": timeout}
  )
  ```

- [ ] **Extract Protocol Options**: Define constants

  ```python
  RTP_PROBE_OPTIONS = {
      "rtbufsize": "100M",
      "analyzeduration": "10M",
      "probesize": "10M"
  }
  ```

- [ ] **Improve Docstrings**: Document return structures

  ```python
  async def validate(self, url: str, timeout: int = 10) -> StreamValidationResult:
      """
      Validate IPTV stream via FFmpeg probe.

      Automatically detects protocol and applies protocol-specific validation.
      Runs in thread pool to avoid blocking async event loop.

      Args:
          url: Stream URL (http://, rtp://, rtsp://, udp://)
          timeout: Maximum probe duration in seconds

      Returns:
          StreamValidationResult with is_valid, metadata, or error info

      Example:
          >>> validator = StreamValidator()
          >>> result = await validator.validate("http://stream.example.com")
          >>> if result.is_valid:
          ...     print(f"Resolution: {result.resolution}")
      """
  ```

#### Code Quality Checks

```bash
# Tests pass
uv run pytest tests/unit/scanner/test_validator.py -v

# Type checking
uv run pyrefly iptv_sniffer/scanner/validator.py

# Linting
uv run ruff check iptv_sniffer/scanner/

# Coverage
uv run pytest --cov=iptv_sniffer.scanner.validator --cov-report=term-missing tests/unit/scanner/test_validator.py
```

---

## Verification & Commit

### Local Verification Workflow

```bash
# Manual test with real stream (if available)
python -c "
import asyncio
from iptv_sniffer.scanner.validator import StreamValidator

async def test():
    validator = StreamValidator(max_workers=2)
    result = await validator.validate('http://test-stream-url.com', timeout=5)
    print(f'Valid: {result.is_valid}')
    print(f'Resolution: {result.resolution}')
    print(f'Codec: {result.codec_video}')

asyncio.run(test())
"

# Run full test suite
uv run pytest tests/unit/scanner/ -v

# Type check
uv run pyrefly check iptv_sniffer/scanner/
```

### Commit Message Template

```bash
git add tests/unit/scanner/test_validator.py iptv_sniffer/scanner/validator.py
git commit -m "feat(scanner): implement multi-protocol stream validator

- Add StreamValidator with HTTP/HTTPS/RTP/RTSP/UDP support
- Implement ffmpeg-python integration via ThreadPoolExecutor
- Define StreamValidationResult and ErrorCategory enums
- Add protocol-specific timeout and option handling
- Parse FFmpeg stderr for categorized error messages
- Include 8 unit tests with 82% coverage

Implements Design.md Section 5 (FFmpeg Integration) and Section 12 (Multi-Protocol)

Closes #<issue-number>"
```

---

## Reference Materials

### Development Plan

See `docs/development-plan.md` lines 547-806:

- Complete validator implementation with protocol dispatch
- FFmpeg error handling patterns
- Async/thread integration

### Design Document

See `docs/Design.md`:

- Section 5 (lines 428-520): FFmpeg Integration Strategy
- Section 12 (lines 982-1080): Multi-Protocol Stream Validation
- Section 4 (lines 369-426): Hybrid Async-Thread Concurrency Model

### FFmpeg-Python Documentation

- [ffmpeg-python GitHub](https://github.com/kkroening/ffmpeg-python)
- [ffmpeg.probe() API](https://github.com/kkroening/ffmpeg-python/blob/master/ffmpeg/_probe.py)

---

## Next Steps

After completing this task:

1. **Task 2.3**: Screenshot Capture (uses similar FFmpeg integration pattern)
2. **Task 3.1**: Strategy Pattern Base (will use StreamValidator)
3. **Task 3.4**: Scan Orchestrator (orchestrates validation across IPs)

**FFmpeg-Python Usage Tips**:

- Always set timeout to avoid hangs
- Use `capture_stdout=True, capture_stderr=True` for error diagnostics
- RTP streams need larger buffers: `rtbufsize`, `analyzeduration`, `probesize`
- Parse stderr to provide actionable error messages to users
