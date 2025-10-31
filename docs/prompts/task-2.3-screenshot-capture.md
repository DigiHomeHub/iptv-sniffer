# Task 2.3: Screenshot Capture

## Task Overview

**Phase**: 2 - FFmpeg Integration  
**Duration**: 2-3 hours  
**Complexity**: Low-Medium

**Goal**: Implement async screenshot capture from IPTV streams using ffmpeg-python with hardware acceleration support.

**Success Criteria**:

- [ ] All tests pass (pytest with asyncio)
- [ ] Type checking passes (mypy --strict)
- [ ] Code style compliant (ruff check)
- [ ] Test coverage ≥ 75%
- [ ] Module size < 500 lines

---

## Design Context

### Architectural Decisions (from Design.md)

**Screenshot Capture** (Design.md Section 5, lines 476-520):

- Extract single frame from stream after 5-second buffer
- Save as PNG format for quality
- Support hardware acceleration: VAAPI (Intel), CUDA (NVIDIA)
- Fallback to software decoding if hardware acceleration fails

**Hardware Acceleration** (Design.md Section 9, lines 797-803):

- VAAPI: Intel Quick Sync via `/dev/dri/renderD128`
- CUDA: NVIDIA GPU acceleration
- Configuration via `ffmpeg_hwaccel` in AppConfig

### Key Constraints

- **Async Interface**: Wrap blocking FFmpeg in ThreadPoolExecutor
- **Path Security**: Prevent path traversal attacks
- **Timeout Enforcement**: Default 10s, prevent infinite hangs
- **Error Handling**: Graceful fallback if screenshot fails

---

## Prerequisites

### Required Completed Tasks

- [x] Task 1.2: Configuration Management (provides ffmpeg_hwaccel config)
- [x] Task 2.1: FFmpeg Availability Check
- [x] Task 2.2: HTTP Stream Validator (similar FFmpeg integration pattern)

### Required Dependencies

```bash
# ffmpeg-python already installed from Task 2.2
python -c "import ffmpeg; print('OK')"
```

---

## TDD Implementation Guide

### Phase 1: Red - Write Failing Tests

**Test File**: `tests/unit/scanner/test_screenshot.py`

#### Core Test Cases

```python
@pytest.mark.asyncio
async def test_capture_screenshot_creates_file(tmp_path):
    """
    Design Intent: Extract frame from stream to PNG file
    Validates: File created at specified path
    """

@pytest.mark.asyncio
async def test_capture_screenshot_with_vaapi(tmp_path):
    """
    Design Intent: Hardware acceleration via VAAPI
    Validates: hwaccel options passed to FFmpeg
    """

@pytest.mark.asyncio
async def test_capture_screenshot_timeout():
    """
    Design Intent: Prevent hanging on non-responsive streams
    Validates: Timeout exception raised after duration
    """
```

### Phase 2: Green - Minimal Implementation

**Implementation File**: `iptv_sniffer/scanner/screenshot.py`

#### Type Signatures (Required)

```python
async def capture_screenshot(
    url: str,
    output_path: Path,
    timeout: int = 10,
    hwaccel: Optional[str] = None
) -> None:
    """
    Capture screenshot from stream.

    Args:
        url: Stream URL
        output_path: Path to save PNG file
        timeout: Maximum capture duration
        hwaccel: Hardware acceleration ("vaapi", "cuda", or None)

    Raises:
        ffmpeg.Error: If capture fails
        asyncio.TimeoutError: If timeout exceeded
    """
    ...
```

#### Implementation Checklist

- [ ] Create ThreadPoolExecutor at module level
- [ ] Implement sync `_sync_capture_screenshot()` helper
- [ ] Use `ffmpeg.input()` with timeout and hwaccel options
- [ ] Use `.output()` with `vframes=1, format='image2', vcodec='png'`
- [ ] Wrap in `asyncio.run_in_executor()`
- [ ] Add logging for success/failure

### Phase 3: Refactor

- [ ] Extract hardware acceleration option building
- [ ] Add path validation (no traversal)
- [ ] Improve error messages

---

## Verification & Commit

```bash
git add tests/unit/scanner/test_screenshot.py iptv_sniffer/scanner/screenshot.py
git commit -m "feat(scanner): implement screenshot capture with hardware acceleration

- Add async screenshot capture using ffmpeg-python
- Support VAAPI and CUDA hardware acceleration
- Implement timeout enforcement (default 10s)
- Include 4 unit tests with 78% coverage

Completes Phase 2 FFmpeg integration (Design.md Section 5)

Closes #<issue-number>"
```

---

## Reference Materials

- Development Plan: lines 809-934
- Design.md Section 5 (lines 476-520)
- Design.md Section 9 (lines 797-803): Hardware acceleration

---

## Next Steps

Phase 2 complete! Begin **Phase 3: Network Scanning**:

- Task 3.1: Strategy Pattern Base
- Task 3.2: Template Scan Strategy
- Task 3.3: Rate Limiter
- Task 3.4: Scan Orchestrator
