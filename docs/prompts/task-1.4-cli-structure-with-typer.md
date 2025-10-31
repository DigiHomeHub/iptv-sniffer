# Task 1.4: CLI Structure with Typer

## Task Overview

**Phase**: 1 - Core Infrastructure  
**Duration**: 2 hours  
**Complexity**: Low

**Goal**: Establish command-line interface structure using Typer with placeholder commands for scan, validate, and export operations.

**Success Criteria**:

- [ ] All tests pass (pytest with CliRunner)
- [ ] Type checking passes (mypy --strict)
- [ ] Code style compliant (ruff check)
- [ ] Test coverage ≥ 80%
- [ ] Module size < 500 lines

---

## Design Context

### Architectural Decisions

**CLI Framework Choice**:

- **Typer**: Modern Python CLI library built on Click
- **Benefits**: Automatic help generation from type hints, subcommands support
- **Integration**: Will be entry point in pyproject.toml scripts

**Command Structure**:

- `iptv-sniffer scan`: Network scanning (Phase 3 implementation)
- `iptv-sniffer validate`: Batch validation (Phase 4 implementation)
- `iptv-sniffer export`: M3U export (Phase 4 implementation)
- `iptv-sniffer --version`: Version information

### Key Constraints

- **Placeholder Commands**: Commands implemented but raise "Not implemented" for now
- **Help Text**: All commands must have descriptive help text
- **Version Display**: --version flag shows package version
- **Exit Codes**: Use proper exit codes (0=success, 1=error)

---

## Prerequisites

### Required Completed Tasks

- [x] Task 1.1: Channel Data Model
- [x] Task 1.2: Configuration Management
- [x] Task 1.3: JSON Storage Repository

### Required Dependencies

```bash
# Add Typer dependency
uv add typer

# Verify installation
python -c "import typer; print(typer.__version__)"
```

---

## TDD Implementation Guide

### Phase 1: Red - Write Failing Tests

**Test File**: `tests/unit/cli/test_app.py`

#### Test Strategy

Cover these dimensions:

1. **Command Existence**: Verify all commands registered
2. **Help Text**: Ensure help displays correctly
3. **Version Display**: --version flag works
4. **Exit Codes**: Commands return proper codes

#### Core Test Cases

```python
from typer.testing import CliRunner
from iptv_sniffer.cli.app import app

runner = CliRunner()

def test_cli_version_command():
    """
    Design Intent: Users can check installed version
    Validates: --version flag displays package version
    """

def test_cli_help_command():
    """
    Design Intent: Self-documenting CLI via help text
    Validates: Main help lists all subcommands
    """

def test_cli_scan_command_exists():
    """
    Design Intent: Scan command registered and shows help
    Validates: iptv-sniffer scan --help works
    """

def test_cli_validate_command_exists():
    """
    Design Intent: Validate command registered
    Validates: Command appears in help and is callable
    """

def test_cli_export_command_exists():
    """
    Design Intent: Export command registered
    Validates: Command appears in help and is callable
    """

def test_cli_placeholder_commands_notify_not_implemented():
    """
    Design Intent: Commands exist but defer implementation
    Validates: Clear "not yet implemented" message shown
    """
```

#### Expected Failure Points

- `app` Typer instance doesn't exist
- Commands not registered
- Version callback not implemented

Run tests:

```bash
uv run pytest tests/unit/cli/test_app.py -v
```

### Phase 2: Green - Minimal Implementation

**Implementation File**: `iptv_sniffer/cli/app.py`

#### Implementation Strategy

1. Create Typer app instance with name and help text
2. Define version callback function
3. Register @app.callback() for global options
4. Add @app.command() decorators for scan, validate, export
5. Implement placeholder message for each command

#### Type Signatures (Required)

```python
app: typer.Typer

def version_callback(value: bool) -> None:
    """Display version and exit if --version flag provided"""
    ...

@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        callback=version_callback,
        is_eager=True
    )
) -> None:
    """iptv-sniffer CLI - Discover and validate IPTV channels"""
    ...

@app.command()
def scan(
    # Future: Add scan parameters
) -> None:
    """Start network scan for IPTV channels"""
    ...

@app.command()
def validate(
    # Future: Add validation parameters
) -> None:
    """Validate existing channels"""
    ...

@app.command()
def export(
    # Future: Add export parameters
) -> None:
    """Export channels as M3U playlist"""
    ...
```

#### Implementation Checklist

- [ ] Create `iptv_sniffer/cli/` directory
- [ ] Create `iptv_sniffer/__init__.py` with `__version__ = "0.1.0"`
- [ ] Import Typer and create app instance
- [ ] Implement version_callback with `typer.echo()` and `raise typer.Exit()`
- [ ] Add @app.callback() with version option
- [ ] Register three placeholder commands
- [ ] Each command uses `typer.echo("Command not yet implemented")`
- [ ] Add docstrings to all commands

#### Common Pitfalls

❌ **Don't**: Use `print()` instead of `typer.echo()`

- Why: `typer.echo()` handles testing better
- Fix: Always use Typer's output functions

❌ **Don't**: Forget `is_eager=True` on version option

- Why: Version callback runs after command processing
- Fix: Add `is_eager=True` to process before commands

❌ **Don't**: Return values from command functions

- Why: Typer uses exit codes, not return values
- Fix: Use `raise typer.Exit(code=1)` for errors

✅ **Do**: Use type hints on all parameters
✅ **Do**: Provide help text for all commands
✅ **Do**: Import version from package `__init__.py`

### Phase 3: Refactor - Code Quality

#### Refactoring Checklist

- [ ] **Extract Version String**: Define in `iptv_sniffer/__init__.py`

  ```python
  # iptv_sniffer/__init__.py
  __version__ = "0.1.0"
  ```

- [ ] **Improve Help Text**: Add usage examples

  ```python
  @app.command()
  def scan():
      """
      Start network scan for IPTV channels.

      Example:
          iptv-sniffer scan --start-ip 192.168.1.1 --end-ip 192.168.1.255
      """
  ```

- [ ] **Add Type Hints**: Ensure all parameters typed

  ```python
  def main(
      version: Optional[bool] = typer.Option(None, "--version", ...)
  ) -> None:
  ```

- [ ] **Group Imports**: Organize imports properly

  ```python
  # Standard library
  from typing import Optional

  # Third-party
  import typer

  # Local
  from iptv_sniffer import __version__
  ```

#### Code Quality Checks

```bash
# Tests pass
uv run pytest tests/unit/cli/test_app.py -v

# Type checking
mypy --strict iptv_sniffer/cli/app.py

# Linting
ruff check iptv_sniffer/cli/

# Manual CLI test
python -m iptv_sniffer.cli.app --help
python -m iptv_sniffer.cli.app --version
```

---

## Verification & Commit

### Local Verification Workflow

```bash
# Test CLI via Python module
python -m iptv_sniffer.cli.app --help
# Should display main help with subcommands

python -m iptv_sniffer.cli.app --version
# Should display version

python -m iptv_sniffer.cli.app scan --help
# Should display scan command help

# Run test suite
uv run pytest tests/unit/cli/ -v

# Type check
mypy --strict iptv_sniffer/cli/
```

### Entry Point Configuration

Add to `pyproject.toml`:

```toml
[project.scripts]
iptv-sniffer = "iptv_sniffer.cli.app:app"
```

Then test installed command:

```bash
uv run iptv-sniffer --help
```

### Commit Message Template

```bash
git add tests/unit/cli/ iptv_sniffer/cli/ iptv_sniffer/__init__.py pyproject.toml
git commit -m "feat(cli): implement CLI structure with Typer

- Add Typer-based CLI with scan, validate, export commands
- Implement --version flag displaying package version
- Add placeholder implementations for future development
- Configure entry point in pyproject.toml as 'iptv-sniffer'
- Include 6 unit tests with 85% coverage

Establishes foundation for Phase 3-4 command implementations

Closes #<issue-number>"
```

---

## Reference Materials

### Development Plan

See `docs/development-plan.md` lines 383-466:

- Complete test suite with CliRunner
- Command structure and registration
- Version callback implementation

### Design Document

See `docs/Design.md`:

- Implementation Plan Phase 1 (lines 1679-1688): CLI structure milestone

### Typer Documentation

- [Typer Documentation](https://typer.tiangolo.com/)
- [Testing with CliRunner](https://typer.tiangolo.com/tutorial/testing/)

---

## Next Steps

After completing this task, Phase 1 (Core Infrastructure) is complete!

**Phase 2 begins next**:

1. Task 2.1: FFmpeg Availability Check
2. Task 2.2: HTTP Stream Validator
3. Task 2.3: Screenshot Capture

**Future CLI enhancements** (Phase 3+):

- Task 3.2: Add scan command parameters (base_url, start_ip, end_ip)
- Task 4.1: Add validate command for M3U imports
- Task 4.3: Implement export command functionality
