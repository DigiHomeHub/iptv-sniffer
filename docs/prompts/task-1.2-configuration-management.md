# Task 1.2: Configuration Management

## Task Overview

**Phase**: 1 - Core Infrastructure  
**Duration**: 2-3 hours  
**Complexity**: Low

**Goal**: Implement hierarchical configuration system using Pydantic with environment variable support, providing validated settings for network scanning, FFmpeg, storage, and web server.

**Success Criteria**:

- [ ] All tests pass (pytest)
- [ ] Type checking passes (mypy --strict)
- [ ] Code style compliant (ruff check)
- [ ] Test coverage ≥ 85%
- [ ] Module size < 500 lines

---

## Design Context

### Architectural Decisions (from Design.md)

**Configuration Hierarchy** (Design.md Section 10, lines 822-872):

- **Priority Order**: CLI args > Environment vars > Config file > Defaults
- **Environment Prefix**: All env vars use `IPTV_SNIFFER_` prefix
- **Validation**: Pydantic validates all config values with clear error messages

**Network Scanning Safety** (Design.md Section 4, lines 369-426):

- Max concurrency: 10 default, 50 maximum (prevent network abuse)
- Timeout: 10 seconds default, 60 seconds maximum
- Retry attempts: 3 maximum with exponential backoff

**FFmpeg Integration** (Design.md Section 5, lines 428-520):

- Hardware acceleration options: vaapi (Intel), cuda (NVIDIA), or none
- Custom FFmpeg arguments support for advanced users
- Timeout enforcement critical for non-responsive streams

### Key Constraints

- **Type Safety**: Use Literal types for constrained string values
- **Secret Protection**: Use SecretStr for API keys (masked in logs)
- **Range Validation**: Use Pydantic Field(ge=..., le=...) for numeric bounds
- **Path Handling**: Use pathlib.Path, not strings, for directory paths

---

## Prerequisites

### Required Completed Tasks

- [x] Task 1.1: Channel Data Model (validates Pydantic setup)

### Required Dependencies

```bash
# Pydantic already installed from Task 1.1
# Verify installation
python -c "from pydantic import BaseModel, Field, SecretStr, HttpUrl; print('OK')"
```

---

## TDD Implementation Guide

### Phase 1: Red - Write Failing Tests

**Test File**: `tests/unit/utils/test_config.py`

#### Test Strategy

Cover these dimensions:

1. **Default Values**: Verify sensible defaults without configuration
2. **Range Validation**: Test numeric boundaries (concurrency, timeout, ports)
3. **Environment Loading**: Confirm env vars override defaults
4. **Type Validation**: Ensure invalid types raise ValidationError
5. **Secret Handling**: Verify SecretStr masks sensitive values

#### Core Test Cases

```python
def test_config_loads_defaults():
    """
    Design Intent: Zero-configuration startup with safe defaults
    Validates: All defaults match documented values in Design.md
    """

def test_config_validates_concurrency_limits():
    """
    Design Intent: Prevent network abuse via bounded concurrency
    Validates: Concurrency must be 1-50 (Design.md Section 4)
    """

def test_config_loads_from_env_vars(monkeypatch):
    """
    Design Intent: 12-factor app configuration via environment
    Validates: IPTV_SNIFFER_* env vars override defaults
    """

def test_config_validates_timeout_range():
    """
    Design Intent: Prevent infinite hangs and unreasonably short timeouts
    Validates: Timeout must be 1-60 seconds
    """

def test_config_secret_str_masks_api_key():
    """
    Design Intent: Prevent API key leakage in logs/errors
    Validates: str(config.ai_api_key) returns masked '**********'
    """

def test_config_rejects_invalid_log_level():
    """
    Design Intent: Type-safe log level configuration
    Validates: Only DEBUG/INFO/WARNING/ERROR accepted (Literal type)
    """
```

#### Expected Failure Points

- `AppConfig` class doesn't exist
- Field validation constraints not implemented
- Environment variable loading not configured

Run tests to confirm red state:

```bash
uv run pytest tests/unit/utils/test_config.py -v
# Expected: ImportError
```

### Phase 2: Green - Minimal Implementation

**Implementation File**: `iptv_sniffer/utils/config.py`

#### Implementation Strategy

1. Create `AppConfig` Pydantic BaseModel
2. Group fields by functional area (Network, FFmpeg, Storage, Web, AI, Logging)
3. Use `Field()` with constraints: `ge` (>=), `le` (<=), default values
4. Configure Pydantic `Config` class for env var loading

#### Type Signatures (Required)

```python
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
        env_prefix: str
        env_file: str
```

#### Implementation Checklist

- [ ] Create `iptv_sniffer/utils/` directory
- [ ] Import required types: `Literal`, `Optional`, `List`, `Path`, `SecretStr`, `HttpUrl`
- [ ] Define all fields with `Field()` including validation constraints
- [ ] Use `default_factory=list` for mutable defaults (not `default=[]`)
- [ ] Add `Config` inner class with `env_prefix = "IPTV_SNIFFER_"`
- [ ] Add `env_file = ".env"` to Config for dotenv support
- [ ] Export `AppConfig` in `iptv_sniffer/utils/__init__.py`

#### Common Pitfalls

❌ **Don't**: Use mutable defaults directly (`default=[]`)

- Why: Shared across all instances (Python gotcha)
- Fix: Use `default_factory=list`

❌ **Don't**: Forget `ge`/`le` constraints on numeric fields

- Why: Invalid values bypass validation
- Fix: Always add constraints per Design.md specs

❌ **Don't**: Use plain `str` for API keys

- Why: Leaked in logs and error messages
- Fix: Use `SecretStr` type

✅ **Do**: Group related fields with comments
✅ **Do**: Match default values to Design.md documentation
✅ **Do**: Use `Literal` types for enums without creating Enum class

### Phase 3: Refactor - Code Quality

#### Refactoring Checklist

- [ ] **Add Docstring**: Document configuration purpose

  ```python
  class AppConfig(BaseModel):
      """
      Application configuration with hierarchical loading.

      Priority: CLI args > Env vars > Config file > Defaults
      All numeric fields have validated ranges to prevent abuse.
      """
  ```

- [ ] **Group Imports**: Separate stdlib, third-party, local

  ```python
  # Standard library
  from pathlib import Path
  from typing import List, Literal, Optional

  # Third-party
  from pydantic import BaseModel, Field, SecretStr, HttpUrl
  ```

- [ ] **Add Field Descriptions**: Document non-obvious constraints

  ```python
  max_concurrency: int = Field(
      default=10,
      ge=1,
      le=50,
      description="Max concurrent network requests (prevents network abuse)"
  )
  ```

- [ ] **Extract Constants**: Define magic numbers at module level

  ```python
  DEFAULT_PORT = 8000
  MIN_PORT = 1
  MAX_PORT = 65535
  ```

#### Code Quality Checks

```bash
# Tests pass
uv run pytest tests/unit/utils/test_config.py -v

# Type checking (strict mode)
mypy --strict iptv_sniffer/utils/config.py

# Linting
ruff check iptv_sniffer/utils/

# Coverage
pytest --cov=iptv_sniffer.utils.config --cov-report=term-missing tests/unit/utils/test_config.py
```

---

## Verification & Commit

### Local Verification Workflow

```bash
# Run all config tests
uv run pytest tests/unit/utils/test_config.py -v

# Test environment variable loading
IPTV_SNIFFER_MAX_CONCURRENCY=20 python -c "
from iptv_sniffer.utils.config import AppConfig
config = AppConfig()
assert config.max_concurrency == 20
print('Environment loading: OK')
"

# Test validation boundaries
python -c "
from iptv_sniffer.utils.config import AppConfig
try:
    AppConfig(max_concurrency=100)
    assert False, 'Should reject concurrency > 50'
except ValueError:
    print('Validation boundaries: OK')
"

# Verify mypy strict compliance
mypy --strict iptv_sniffer/utils/config.py
```

### Commit Message Template

```bash
git add tests/unit/utils/test_config.py iptv_sniffer/utils/config.py iptv_sniffer/utils/__init__.py
git commit -m "feat(config): implement hierarchical configuration with Pydantic validation

- Add AppConfig with 6 functional groups (Network, FFmpeg, Storage, Web, AI, Logging)
- Implement environment variable loading with IPTV_SNIFFER_ prefix
- Add range validation for network safety (concurrency: 1-50, timeout: 1-60)
- Use SecretStr for API key protection
- Include 6 unit tests with 88% coverage

Implements configuration hierarchy from Design.md Section 10

Closes #<issue-number>"
```

---

## Reference Materials

### Development Plan

See `docs/development-plan.md` lines 130-215:

- Complete test implementation
- Environment variable handling examples
- Validation boundary tests

### Design Document

See `docs/Design.md`:

- Section 10 (lines 822-872): Configuration Management
- Section 4 (lines 369-426): Concurrency Control and Rate Limiting
- Cross-Cutting Concerns (lines 1507-1540): Security constraints

### Project Guidelines

See `AGENTS.md`:

- Configuration section: "Use Pydantic for all configuration"
- Security section: "Use SecretStr for sensitive values"

---

## Next Steps

After completing this task:

1. Configuration will be used by all subsequent components
2. Task 1.3 (JSON Repository) will use `data_dir` from config
3. Task 2.1 (FFmpeg Check) will use `ffmpeg_timeout` from config
4. Task 6.1 (FastAPI Setup) will use `host` and `port` from config
