# Task 4.2: Character Encoding Detection

## Task Overview

**Phase**: 4 - M3U Support  
**Duration**: 2 hours  
**Complexity**: Low

**Goal**: Detect and handle non-UTF-8 M3U files using chardet library.

**Success Criteria**:

- [ ] All tests pass
- [ ] Type checking passes (pyrefly check)
- [ ] Test coverage ≥ 80%

---

## Design Context

**Encoding Support** (Design.md Section 6, lines 577-594):

- Try UTF-8 first (most common)
- Use chardet for automatic detection
- Support international channel names (GB2312, etc.)

---

## Prerequisites

- [x] Task 4.1: M3U Parser

### Dependencies

```bash
uv add chardet
```

---

## Implementation

**File**: `iptv_sniffer/m3u/encoding.py`

```python
def read_m3u_file(path: Path) -> str:
    """Read M3U file with automatic encoding detection"""
    try:
        return path.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        raw = path.read_bytes()
        detected = chardet.detect(raw)
        encoding = detected['encoding']
        logger.info(f"Detected encoding: {encoding}")
        return raw.decode(encoding)
```

---

## Commit

```bash
git commit -m "feat(m3u): add character encoding detection with chardet

- Implement read_m3u_file() with UTF-8 first, chardet fallback
- Support international channel names (GB2312, Big5, etc.)
- Log detected encoding with confidence level
- Include 3 unit tests with 85% coverage

Enables international M3U file support per Design.md Section 6

Closes #<issue-number>"
```
