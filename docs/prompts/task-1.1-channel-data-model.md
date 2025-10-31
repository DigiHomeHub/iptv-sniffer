# Task 1.1: Channel Data Model

## Task Overview

**Phase**: 1 - Core Infrastructure  
**Duration**: 2-3 hours  
**Complexity**: Low

**Goal**: Define the foundational Channel data model with Pydantic validation, supporting multiple IPTV protocols and validation status tracking.

**Success Criteria**:

- [ ] All tests pass (pytest)
- [ ] Type checking passes (mypy --strict)
- [ ] Code style compliant (ruff check)
- [ ] Test coverage ≥ 90%
- [ ] Module size < 500 lines

---

## Design Context

### Architectural Decisions (from Design.md)

**Multi-Protocol Support** (Design.md Section 12):

- Channel URLs must support HTTP, HTTPS, RTP, RTSP, UDP, and MMS protocols
- URL validation should reject unsupported protocols with clear error messages
- Changed from `HttpUrl` type to string with custom validator

**Validation Status Tracking** (Design.md Section 14):

- Channels track validation lifecycle: UNKNOWN → VALIDATING → ONLINE/OFFLINE/ERROR
- `validation_status` field enables batch validation workflows
- Status persists across scans to show historical data

**Deduplication Strategy** (Design.md Section 7):

- URL serves as primary deduplication key (normalized)
- `manually_edited` flag preserves user customizations during auto-updates
- Timestamps track creation and last update for auditing

### Key Constraints

- **Data Integrity**: All fields must use Pydantic validation (never plain dataclasses)
- **Protocol Flexibility**: URL field must accept all IPTV-relevant protocols
- **Type Safety**: Full type hints required for mypy --strict compliance
- **Immutable IDs**: Channel IDs auto-generated as UUIDs, never user-editable

---

## Prerequisites

### Required Completed Tasks

None - this is the foundational task for Phase 1.

### Required Dependencies

```bash
# Install dependencies (already in pyproject.toml)
uv add pydantic
```

### Verification Commands

```bash
# Verify Pydantic available
python -c "import pydantic; print(pydantic.__version__)"
```

---

## TDD Implementation Guide

### Phase 1: Red - Write Failing Tests

**Test File**: `tests/unit/channel/test_models.py`

#### Test Strategy

Cover these dimensions:

1. **Minimal Construction**: Verify creation with only required fields
2. **Protocol Validation**: Ensure URL validation accepts/rejects correct protocols
3. **Default Values**: Confirm auto-generation of id, timestamps, status
4. **Validation Errors**: Test Pydantic raises ValidationError for invalid data
5. **Enum Values**: Validate ValidationStatus enum completeness

#### Core Test Cases

```python
def test_channel_creation_with_minimal_fields():
    """
    Design Intent: Channel should be creatable with minimal data (name + url)
    Validates: Principle of least required information
    """

def test_channel_url_validation_rejects_invalid_scheme():
    """
    Design Intent: Prevent channels with unsupported protocols (e.g., ftp://)
    Validates: Security constraint - only IPTV-relevant protocols allowed
    """

def test_channel_url_supports_multiple_protocols():
    """
    Design Intent: Multi-protocol support per Design.md Section 12
    Validates: HTTP, HTTPS, RTP, RTSP, UDP, MMS protocols all accepted
    """

def test_channel_validation_status_defaults_to_unknown():
    """
    Design Intent: Newly created channels have unknown status until validated
    Validates: Validation lifecycle (UNKNOWN → VALIDATING → ONLINE/OFFLINE)
    """

def test_channel_timestamps_auto_generated():
    """
    Design Intent: Audit trail via automatic timestamp management
    Validates: created_at and updated_at auto-set to current UTC time
    """
```

#### Expected Failure Points

Tests will fail because:

1. `Channel` class doesn't exist yet
2. `ValidationStatus` enum not defined
3. URL validator not implemented

Run tests to confirm red state:

```bash
uv run pytest tests/unit/channel/test_models.py -v
# Expected: ImportError or ModuleNotFoundError
```

### Phase 2: Green - Minimal Implementation

**Implementation File**: `iptv_sniffer/channel/models.py`

#### Implementation Strategy

1. Define `ValidationStatus` enum with 5 states
2. Create `Channel` Pydantic BaseModel with all required fields
3. Implement `@validator` for URL protocol checking
4. Use `Field(default_factory=...)` for auto-generated values

#### Type Signatures (Required)

```python
class ValidationStatus(str, Enum):
    UNKNOWN: str
    VALIDATING: str
    ONLINE: str
    OFFLINE: str
    ERROR: str

class Channel(BaseModel):
    id: str
    name: str
    url: str  # Not HttpUrl - custom validation needed
    tvg_id: Optional[str]
    tvg_logo: Optional[str]
    group: Optional[str]
    resolution: Optional[str]
    is_online: bool
    validation_status: ValidationStatus
    last_validated: Optional[datetime]
    screenshot_path: Optional[str]
    manually_edited: bool
    created_at: datetime
    updated_at: datetime

    @validator("url")
    def validate_stream_url(cls, v: str) -> str:
        # Validate protocol scheme
        ...
```

#### Implementation Checklist

- [ ] Create `iptv_sniffer/channel/` directory
- [ ] Create `__init__.py` with public exports
- [ ] Define `ValidationStatus` enum using `str, Enum` base
- [ ] Define `Channel` with all fields from type signature
- [ ] Use `Field(default_factory=lambda: str(uuid4()))` for id
- [ ] Use `Field(default_factory=datetime.utcnow)` for timestamps
- [ ] Implement URL validator checking `urlparse(v).scheme`
- [ ] Add `Config` class with `use_enum_values = True`

#### Common Pitfalls

❌ **Don't**: Use `dataclass` instead of Pydantic `BaseModel`

- Why: Project requires Pydantic for validation (AGENTS.md rule)

❌ **Don't**: Use `HttpUrl` type for url field

- Why: HttpUrl only accepts HTTP/HTTPS, not RTP/RTSP/UDP

❌ **Don't**: Hardcode datetime values in defaults

- Why: Uses same timestamp for all instances (Python gotcha)

✅ **Do**: Use `default_factory` for mutable/dynamic defaults
✅ **Do**: Validate URL scheme in validator, not regex
✅ **Do**: Import from `urllib.parse` for URL parsing

### Phase 3: Refactor - Code Quality

#### Refactoring Checklist

- [ ] **Extract Magic Values**: Move protocol list to module constant

  ```python
  SUPPORTED_PROTOCOLS = {"http", "https", "rtp", "rtsp", "udp", "mms"}
  ```

- [ ] **Add Docstrings**: Document class purpose and field meanings

  ```python
  class Channel(BaseModel):
      """
      IPTV channel model with multi-protocol support.

      Supports validation lifecycle tracking and deduplication by URL.
      All timestamps in UTC.
      """
  ```

- [ ] **Improve Error Messages**: Make validation errors actionable

  ```python
  raise ValueError(
      f"Unsupported protocol: {parsed.scheme}. "
      f"Supported: {', '.join(SUPPORTED_PROTOCOLS)}"
  )
  ```

- [ ] **Optimize Imports**: Group stdlib, third-party, local imports

  ```python
  # Standard library
  from datetime import datetime
  from enum import Enum
  from typing import Optional
  from urllib.parse import urlparse
  from uuid import uuid4

  # Third-party
  from pydantic import BaseModel, Field, validator
  ```

#### Code Quality Checks

Run all quality gates:

```bash
# 1. Tests still pass after refactoring
uv run pytest tests/unit/channel/test_models.py -v

# 2. Type checking
mypy --strict iptv_sniffer/channel/models.py

# 3. Linting
ruff check iptv_sniffer/channel/

# 4. Coverage (should be >90%)
pytest --cov=iptv_sniffer.channel.models --cov-report=term-missing tests/unit/channel/test_models.py
```

---

## Verification & Commit

### Local Verification Workflow

```bash
# Run full test suite for this module
uv run pytest tests/unit/channel/ -v --tb=short

# Type check with strict mode
mypy --strict iptv_sniffer/channel/

# Check code style
ruff check iptv_sniffer/channel/

# Verify coverage threshold
pytest --cov=iptv_sniffer.channel --cov-report=term-missing \
       --cov-fail-under=90 tests/unit/channel/
```

### Commit Message Template

```bash
git add tests/unit/channel/test_models.py iptv_sniffer/channel/models.py iptv_sniffer/channel/__init__.py
git commit -m "feat(channel): implement Channel data model with multi-protocol support

- Add Channel Pydantic model with UUID auto-generation
- Implement ValidationStatus enum (UNKNOWN/VALIDATING/ONLINE/OFFLINE/ERROR)
- Add URL validator supporting HTTP/HTTPS/RTP/RTSP/UDP/MMS protocols
- Include 5 unit tests with 95% coverage
- Type-safe with mypy --strict compliance

Validates architectural decision for multi-protocol IPTV support (Design.md Section 12)

Closes #<issue-number>"
```

---

## Reference Materials

### Development Plan

See `docs/development-plan.md` lines 28-125 for:

- Complete test suite example
- Full implementation code
- Definition of Done criteria

### Design Document

See `docs/Design.md`:

- Section 12 (lines 982-1080): Multi-Protocol Stream Validation
- Section 7 (lines 603-654): Channel Deduplication Strategy
- Section 2 (lines 267-295): Data Models overview

### Project Guidelines

See `AGENTS.md`:

- Data Models section: "All data must use Pydantic BaseModels (never dataclass)"
- Type Safety section: "Use mypy --strict throughout"
- Module Size Limit: "Each file must remain under 500 lines"

---

## Next Steps

After completing this task:

1. Proceed to **Task 1.2: Configuration Management** (also uses Pydantic)
2. Task 1.3 will use this Channel model in the repository pattern
3. Task 2.2 will extend this with StreamValidationResult integration
