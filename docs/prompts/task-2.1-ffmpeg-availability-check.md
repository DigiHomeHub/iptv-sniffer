# Task 2.1: FFmpeg Availability Check

## Task Overview

**Phase**: 2 - FFmpeg Integration  
**Duration**: 1-2 hours  
**Complexity**: Low

**Goal**: Implement FFmpeg installation detection and version reporting with clear error messages for missing installations.

**Success Criteria**:

- [ ] All tests pass (pytest)
- [ ] Type checking passes (mypy --strict)
- [ ] Code style compliant (ruff check)
- [ ] Test coverage ≥ 85%
- [ ] Module size < 500 lines

---

## Design Context

### Architectural Decisions (from Design.md)

**FFmpeg Integration Requirements** (Design.md Section 5, lines 428-520):

- FFmpeg is **mandatory dependency** - application cannot function without it
- Must detect availability on startup before attempting stream validation
- Provide actionable installation instructions in error messages
- Version detection for debugging and compatibility checks

**Docker Deployment** (Design.md Section 9, lines 737-820):

- Docker image bundles FFmpeg via `apt-get install ffmpeg libavcodec-extra`
- Local development requires user installation
- Health check endpoint must verify FFmpeg availability

### Key Constraints

- **Cross-Platform**: Must work on Linux, macOS, Windows
- **Clear Errors**: Error messages include installation commands
- **Non-Blocking**: Check should be fast (<1 second)
- **Version Parsing**: Extract version string for diagnostics

---

## Prerequisites

### Required Completed Tasks

None - this is the first task in Phase 2.

### Required Dependencies

```bash
# Standard library only (shutil, subprocess)
# FFmpeg itself must be installed by user/Docker

# Verify FFmpeg installed (manual check)
ffmpeg -version
```

---

## TDD Implementation Guide

### Phase 1: Red - Write Failing Tests

**Test File**: `tests/unit/utils/test_ffmpeg.py`

#### Test Strategy

Cover these dimensions:

1. **Detection Success**: FFmpeg installed and detected
2. **Detection Failure**: FFmpeg not found, graceful handling
3. **Version Extraction**: Parse version string from output
4. **Error Raising**: Optional exception on missing FFmpeg
5. **Cross-Platform**: Test with mocked platform-specific paths

#### Core Test Cases

```python
def test_ffmpeg_installed_returns_true_when_available():
    """
    Design Intent: Detect FFmpeg availability on system PATH
    Validates: shutil.which() finds ffmpeg executable
    """

def test_ffmpeg_version_detection():
    """
    Design Intent: Extract version for debugging/compatibility
    Validates: Parse version string from ffmpeg -version output
    """

@patch("shutil.which", return_value=None)
def test_ffmpeg_not_installed_returns_false(mock_which):
    """
    Design Intent: Graceful detection when FFmpeg missing
    Validates: Return False, don't raise exception
    """

@patch("shutil.which", return_value=None)
def test_ffmpeg_not_installed_raises_error_when_requested(mock_which):
    """
    Design Intent: Startup validation can fail fast
    Validates: raise_on_missing=True raises FFmpegNotFoundError
    """

def test_ffmpeg_error_message_includes_install_instructions():
    """
    Design Intent: Actionable error messages for users
    Validates: Exception message includes platform-specific install command
    """
```

#### Expected Failure Points

- `check_ffmpeg_installed()` function doesn't exist
- `get_ffmpeg_version()` function doesn't exist
- `FFmpegNotFoundError` exception class doesn't exist

Run tests:

```bash
uv run pytest tests/unit/utils/test_ffmpeg.py -v
```

### Phase 2: Green - Minimal Implementation

**Implementation File**: `iptv_sniffer/utils/ffmpeg.py`

#### Implementation Strategy

1. Define custom `FFmpegNotFoundError` exception
2. Implement `check_ffmpeg_installed()` using `shutil.which()`
3. Implement `get_ffmpeg_version()` using `subprocess.run()`
4. Add platform-specific installation instructions

#### Type Signatures (Required)

```python
class FFmpegNotFoundError(Exception):
    """Raised when FFmpeg is not installed"""
    pass

def check_ffmpeg_installed(raise_on_missing: bool = False) -> bool:
    """
    Check if FFmpeg is available on system.

    Args:
        raise_on_missing: If True, raise exception when not found

    Returns:
        True if FFmpeg found, False otherwise

    Raises:
        FFmpegNotFoundError: If raise_on_missing=True and FFmpeg not found
    """
    ...

def get_ffmpeg_version() -> Optional[str]:
    """
    Get FFmpeg version string.

    Returns:
        Version string (e.g., "ffmpeg version 4.4.2") or None if not installed
    """
    ...

def get_install_instructions() -> str:
    """
    Get platform-specific FFmpeg installation instructions.

    Returns:
        Installation command for current platform
    """
    ...
```

#### Implementation Checklist

- [ ] Create `iptv_sniffer/utils/ffmpeg.py`
- [ ] Define `FFmpegNotFoundError` exception class
- [ ] Use `shutil.which("ffmpeg")` to detect installation
- [ ] Use `subprocess.run(["ffmpeg", "-version"])` to get version
- [ ] Parse first line of output for version string
- [ ] Add platform detection via `sys.platform`
- [ ] Provide install commands for Linux (apt/yum), macOS (brew), Windows (choco)
- [ ] Handle subprocess errors gracefully (return None, don't crash)

#### Common Pitfalls

❌ **Don't**: Use `shell=True` in subprocess

- Why: Security risk (command injection)
- Fix: Pass command as list `["ffmpeg", "-version"]`

❌ **Don't**: Assume ffmpeg is in specific path

- Why: Path varies by platform and installation method
- Fix: Use `shutil.which()` to search PATH

❌ **Don't**: Cache detection results at module level

- Why: FFmpeg could be installed during runtime
- Fix: Check on each call (fast operation anyway)

✅ **Do**: Set timeout on subprocess.run() (e.g., 5 seconds)
✅ **Do**: Capture stdout and stderr
✅ **Do**: Return None instead of raising on version check failure

### Phase 3: Refactor - Code Quality

#### Refactoring Checklist

- [ ] **Extract Platform Detection**: Separate function

  ```python
  def _get_platform() -> str:
      """Detect current platform (linux/darwin/windows)"""
      return sys.platform
  ```

- [ ] **Add Logging**: Log FFmpeg detection results

  ```python
  import logging
  logger = logging.getLogger(__name__)

  logger.info(f"FFmpeg detected: {ffmpeg_path}")
  logger.warning("FFmpeg not found on system PATH")
  ```

- [ ] **Improve Error Message**: Include version in error

  ```python
  raise FFmpegNotFoundError(
      "FFmpeg not found. Install with:\n"
      f"  {get_install_instructions()}\n"
      "Required for stream validation."
  )
  ```

- [ ] **Add Docstrings**: Document all public functions

  ```python
  def check_ffmpeg_installed(raise_on_missing: bool = False) -> bool:
      """
      Check if FFmpeg is available on system PATH.

      This function uses shutil.which() to locate the ffmpeg executable.
      Fast operation (<100ms typically).

      Args:
          raise_on_missing: If True, raise exception when FFmpeg not found.
                          Useful for startup validation.

      Returns:
          True if FFmpeg executable found, False otherwise.

      Raises:
          FFmpegNotFoundError: When raise_on_missing=True and FFmpeg not found.

      Example:
          >>> if check_ffmpeg_installed():
          ...     print("FFmpeg available")
          >>> check_ffmpeg_installed(raise_on_missing=True)  # Raises if missing
      """
  ```

#### Code Quality Checks

```bash
# Tests pass
uv run pytest tests/unit/utils/test_ffmpeg.py -v

# Type checking
uv run pyrefly check iptv_sniffer/utils/ffmpeg.py

# Linting
uv run ruff check iptv_sniffer/utils/

# Coverage
uv run pytest --cov=iptv_sniffer.utils.ffmpeg --cov-report=term-missing tests/unit/utils/test_ffmpeg.py
```

---

## Verification & Commit

### Local Verification Workflow

```bash
# Manual test - FFmpeg installed
python -c "
from iptv_sniffer.utils.ffmpeg import check_ffmpeg_installed, get_ffmpeg_version
print(f'FFmpeg installed: {check_ffmpeg_installed()}')
print(f'Version: {get_ffmpeg_version()}')
"

# Manual test - Error handling
python -c "
from unittest.mock import patch
from iptv_sniffer.utils.ffmpeg import check_ffmpeg_installed, FFmpegNotFoundError

with patch('shutil.which', return_value=None):
    try:
        check_ffmpeg_installed(raise_on_missing=True)
    except FFmpegNotFoundError as e:
        print(f'Error caught: {e}')
"

# Run test suite
uv run pytest tests/unit/utils/test_ffmpeg.py -v

# Type check
mypy --strict iptv_sniffer/utils/ffmpeg.py
```

### Integration with Health Check

```python
# Future use in web/app.py health check
@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "checks": {
            "ffmpeg": check_ffmpeg_installed(),
            "ffmpeg_version": get_ffmpeg_version()
        }
    }
```

### Commit Message Template

```bash
git add tests/unit/utils/test_ffmpeg.py iptv_sniffer/utils/ffmpeg.py
git commit -m "feat(ffmpeg): implement FFmpeg availability detection

- Add check_ffmpeg_installed() with optional exception raising
- Implement get_ffmpeg_version() for debugging/compatibility
- Define FFmpegNotFoundError with actionable error messages
- Add platform-specific installation instructions
- Include 5 unit tests with 90% coverage

Critical for startup validation and health checks (Design.md Section 5)

Closes #<issue-number>"
```

---

## Reference Materials

### Development Plan

See `docs/development-plan.md` lines 469-544:

- Complete test implementation with mocking
- FFmpeg detection and version parsing
- Error handling patterns

### Design Document

See `docs/Design.md`:

- Section 5 (lines 428-520): FFmpeg Integration Strategy
- Section 9 (lines 737-820): Docker Deployment with FFmpeg

### Project Guidelines

See `AGENTS.md`:

- FFmpeg Integration: "Use ffmpeg-python library, never subprocess strings"
- Note: This task uses subprocess only for detection, not stream operations

---

## Next Steps

After completing this task:

1. **Task 2.2**: HTTP Stream Validator (uses check_ffmpeg_installed())
2. **Task 2.3**: Screenshot Capture (uses FFmpeg for image extraction)
3. **Task 6.1**: FastAPI Setup (health check uses this module)

**FFmpeg Installation Guide for Development**:

```bash
# Linux (Ubuntu/Debian)
sudo apt-get update && sudo apt-get install -y ffmpeg libavcodec-extra

# macOS
brew install ffmpeg

# Windows (with Chocolatey)
choco install ffmpeg
```
