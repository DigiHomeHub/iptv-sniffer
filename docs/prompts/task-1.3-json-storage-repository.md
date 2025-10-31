# Task 1.3: JSON Storage Repository

## Task Overview

**Phase**: 1 - Core Infrastructure  
**Duration**: 3-4 hours  
**Complexity**: Medium

**Goal**: Implement file-based JSON storage for channels with CRUD operations and basic filtering, using repository pattern to enable future SQLite migration.

**Success Criteria**:

- [ ] All tests pass (pytest with async support)
- [ ] Type checking passes (mypy --strict)
- [ ] Code style compliant (ruff check)
- [ ] Test coverage ≥ 85%
- [ ] Module size < 500 lines

---

## Design Context

### Architectural Decisions (from Design.md)

**Storage Backend Choice** (Design.md Section 2, lines 267-337):

- **v1.0**: JSON file storage for simplicity (zero config, human-readable)
- **Future**: SQLite migration path via repository pattern abstraction
- **Capacity**: Sufficient for <1000 channels
- **Trade-off**: No concurrent writes or transactions, but Docker-friendly

**Repository Pattern** (Design.md Section 2, lines 296-320):

- Abstract interface enables swapping storage backends without changing callers
- Methods: `add()`, `get_by_id()`, `find_all()`, `delete()`
- All methods async to match future SQLite implementation

**Deduplication by URL** (Design.md Section 7, lines 603-654):

- URL is the primary key (normalized)
- `add()` operation: Update existing channel if URL matches, else insert new
- Preserves user edits via `manually_edited` flag

### Key Constraints

- **Async Interface**: All methods must be `async` (future-proofing for SQLite)
- **UTF-8 Encoding**: JSON files use UTF-8 with `ensure_ascii=False`
- **Pretty Printing**: JSON indent=2 for human readability
- **Atomic Writes**: Write to temp file + rename pattern (minimize corruption risk)

---

## Prerequisites

### Required Completed Tasks

- [x] Task 1.1: Channel Data Model (provides Channel Pydantic model)
- [x] Task 1.2: Configuration Management (provides data_dir configuration)

### Required Dependencies

```bash
# Standard library only (json, pathlib, asyncio)
# Verify Channel model available
python -c "from iptv_sniffer.channel.models import Channel; print('OK')"
```

### Dependency Verification

```bash
# Test imports
python -c "
from iptv_sniffer.channel.models import Channel
from iptv_sniffer.utils.config import AppConfig
config = AppConfig()
print(f'Data directory: {config.data_dir}')
"
```

---

## TDD Implementation Guide

### Phase 1: Red - Write Failing Tests

**Test File**: `tests/unit/storage/test_json_repository.py`

#### Test Strategy

Cover these dimensions:

1. **CRUD Operations**: Create, Read, Update, Delete channels
2. **Deduplication**: Adding duplicate URL updates existing record
3. **Filtering**: Filter by group, online status, validation status
4. **Persistence**: Data survives repository recreation
5. **Error Handling**: Non-existent IDs, corrupted JSON files

#### Core Test Cases

```python
@pytest.fixture
def temp_storage_file(tmp_path):
    """Provide temporary JSON file for isolated testing"""

@pytest.mark.asyncio
async def test_add_channel_creates_new_record(temp_storage_file):
    """
    Design Intent: Channels can be persisted to JSON file
    Validates: Basic create operation with file I/O
    """

@pytest.mark.asyncio
async def test_add_channel_updates_existing_by_url(temp_storage_file):
    """
    Design Intent: URL-based deduplication (Design.md Section 7)
    Validates: Second add() with same URL updates first record
    """

@pytest.mark.asyncio
async def test_find_all_with_group_filter(temp_storage_file):
    """
    Design Intent: Enable filtering channels by metadata
    Validates: Query interface for group-based filtering
    """

@pytest.mark.asyncio
async def test_delete_channel_removes_from_storage(temp_storage_file):
    """
    Design Intent: Support channel removal workflow
    Validates: Delete operation persists to disk
    """

@pytest.mark.asyncio
async def test_get_by_id_returns_none_for_missing(temp_storage_file):
    """
    Design Intent: Graceful handling of non-existent channels
    Validates: Return None instead of raising exception
    """

@pytest.mark.asyncio
async def test_repository_survives_recreation(temp_storage_file):
    """
    Design Intent: Data persists across repository instances
    Validates: File-based storage durability
    """
```

#### Expected Failure Points

- `JSONChannelRepository` class doesn't exist
- Async methods not implemented
- Filter logic not present

Run tests to confirm red state:

```bash
uv run pytest tests/unit/storage/test_json_repository.py -v
# Expected: ImportError or test failures
```

### Phase 2: Green - Minimal Implementation

**Implementation File**: `iptv_sniffer/storage/json_repository.py`

#### Implementation Strategy

1. Define `JSONChannelRepository` class with file path attribute
2. Implement private helper methods: `_read_data()`, `_write_data()`
3. Implement async public methods using `asyncio.to_thread()` for file I/O
4. Add filtering logic in `find_all()` method

#### Type Signatures (Required)

```python
class JSONChannelRepository:
    """File-based JSON storage for channels"""

    def __init__(self, file_path: Path) -> None:
        """Initialize repository with JSON file path"""
        ...

    def _read_data(self) -> List[Dict[str, Any]]:
        """Read raw JSON data from file (synchronous)"""
        ...

    def _write_data(self, data: List[Dict[str, Any]]) -> None:
        """Write raw JSON data to file (synchronous)"""
        ...

    async def add(self, channel: Channel) -> Channel:
        """Add new channel or update if URL exists"""
        ...

    async def get_by_id(self, channel_id: str) -> Optional[Channel]:
        """Get channel by ID, return None if not found"""
        ...

    async def get_by_url(self, url: str) -> Optional[Channel]:
        """Get channel by URL for deduplication checks"""
        ...

    async def find_all(
        self, filters: Optional[Dict[str, Any]] = None
    ) -> List[Channel]:
        """Find channels with optional filtering"""
        ...

    async def delete(self, channel_id: str) -> bool:
        """Delete channel by ID, return True if deleted"""
        ...
```

#### Implementation Checklist

- [ ] Create `iptv_sniffer/storage/` directory
- [ ] Initialize file on first instantiation if not exists
- [ ] Use `ensure_ascii=False` in `json.dump()` for international names
- [ ] Use `indent=2` for human-readable JSON
- [ ] Implement URL-based deduplication in `add()`
- [ ] Convert dict to Channel using `Channel(**ch)` in read methods
- [ ] Convert Channel to dict using `channel.dict()` in write methods
- [ ] Implement filter logic for `group`, `is_online`, `validation_status`
- [ ] Use `asyncio.to_thread()` for blocking file I/O (not async file I/O)

#### Common Pitfalls

❌ **Don't**: Use `async with open()` without aiofiles library

- Why: Built-in `open()` is blocking, not async
- Fix: Use `asyncio.to_thread(self._read_data)` pattern

❌ **Don't**: Forget to create parent directory

- Why: `FileNotFoundError` if data_dir doesn't exist
- Fix: Use `file_path.parent.mkdir(parents=True, exist_ok=True)`

❌ **Don't**: Use `ensure_ascii=True` (default)

- Why: Encodes international characters as \uXXXX escapes
- Fix: Always set `ensure_ascii=False`

❌ **Don't**: Modify mutable filter dict parameter

- Why: Side effects on caller's dict
- Fix: Copy dict before modifying

✅ **Do**: Initialize empty JSON array `[]` if file doesn't exist
✅ **Do**: Use Path.read_text() / Path.write_text() for simple operations
✅ **Do**: Wrap all file I/O in `asyncio.to_thread()` for async interface

### Phase 3: Refactor - Code Quality

#### Refactoring Checklist

- [ ] **Extract Filter Logic**: Move to separate method if >20 lines

  ```python
  def _apply_filters(
      self, channels: List[Channel], filters: Dict[str, Any]
  ) -> List[Channel]:
      """Apply filters to channel list"""
  ```

- [ ] **Add Docstrings**: Document public API and edge cases

  ```python
  async def add(self, channel: Channel) -> Channel:
      """
      Add new channel or update existing by URL.

      If a channel with the same URL exists, updates its fields
      while preserving manually_edited status per Design.md Section 7.

      Args:
          channel: Channel to add or update

      Returns:
          The saved channel (with any updates applied)
      """
  ```

- [ ] **Error Handling**: Add try-except for JSON decode errors

  ```python
  try:
      return json.loads(content)
  except json.JSONDecodeError as e:
      logger.error(f"Corrupted JSON file: {e}")
      return []  # Return empty list, don't crash
  ```

- [ ] **Logging**: Add structured logging for operations

  ```python
  logger.info(
      "Channel added",
      extra={"channel_id": channel.id, "url": str(channel.url)}
  )
  ```

#### Code Quality Checks

```bash
# Tests pass
uv run pytest tests/unit/storage/test_json_repository.py -v

# Type checking
mypy --strict iptv_sniffer/storage/json_repository.py

# Linting
ruff check iptv_sniffer/storage/

# Coverage
pytest --cov=iptv_sniffer.storage.json_repository --cov-report=term-missing tests/unit/storage/
```

---

## Verification & Commit

### Local Verification Workflow

```bash
# Test repository operations
python -c "
import asyncio
from pathlib import Path
from iptv_sniffer.channel.models import Channel
from iptv_sniffer.storage.json_repository import JSONChannelRepository

async def test():
    repo = JSONChannelRepository(Path('/tmp/test_channels.json'))
    channel = Channel(name='Test', url='http://test.com')

    # Add
    saved = await repo.add(channel)
    assert saved.id == channel.id

    # Get by ID
    found = await repo.get_by_id(channel.id)
    assert found is not None

    # Delete
    deleted = await repo.delete(channel.id)
    assert deleted is True

    print('All operations: OK')

asyncio.run(test())
"

# Run full test suite
uv run pytest tests/unit/storage/ -v

# Verify mypy compliance
mypy --strict iptv_sniffer/storage/
```

### Commit Message Template

```bash
git add tests/unit/storage/ iptv_sniffer/storage/
git commit -m "feat(storage): implement JSON-based channel repository

- Add JSONChannelRepository with async CRUD operations
- Implement URL-based deduplication (Design.md Section 7)
- Support filtering by group, is_online, validation_status
- Use asyncio.to_thread for file I/O compatibility
- Include 8 unit tests with 87% coverage

Repository pattern enables future SQLite migration (Design.md Section 2)

Closes #<issue-number>"
```

---

## Reference Materials

### Development Plan

See `docs/development-plan.md` lines 218-380:

- Complete test suite with fixtures
- Full implementation including filtering
- Async/await usage patterns

### Design Document

See `docs/Design.md`:

- Section 2 (lines 267-337): Storage Architecture
- Section 7 (lines 603-654): Channel Deduplication Strategy

### Project Guidelines

See `AGENTS.md`:

- Storage section: "JSON storage sufficient for <1000 channels"
- Async patterns: "Use asyncio for I/O operations"

---

## Next Steps

After completing this task:

1. Task 1.4 (CLI) will use this repository for channel management
2. Task 3.4 (Scan Orchestrator) will save discovered channels here
3. Task 4.1 (M3U Parser) will import channels into this repository
4. Future Task: Implement SQLiteChannelRepository with same interface
