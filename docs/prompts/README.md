# IPTV Sniffer Development Prompts

This directory contains task-specific prompts for Test-Driven Development (TDD) of the iptv-sniffer project.

## Overview

Each prompt file guides the implementation of a specific task from the [Development Plan](../development-plan.md), following strict TDD principles (Red-Green-Refactor).

## File Naming Convention

```text
task-<phase>.<number>-<description-in-kebab-case>.md
```

**Examples**:

- `task-1.1-channel-data-model.md`
- `task-2.2-http-stream-validator.md`
- `task-5.2-smart-port-scanner.md`

## Prompt Structure

Each prompt follows a standardized structure:

1. **Task Overview**: Goal, complexity, success criteria
2. **Design Context**: Relevant architectural decisions from Design.md
3. **Prerequisites**: Required completed tasks and dependencies
4. **TDD Implementation Guide**:
   - **Red Phase**: Write failing tests
   - **Green Phase**: Minimal implementation
   - **Refactor Phase**: Code quality improvements
5. **Verification & Commit**: Testing commands and git commit format

## Usage Workflow

### Step 1: Select Task

Choose the next task from the development plan based on:

- Completed prerequisites
- Phase progression
- Team capacity

### Step 2: Review Prompt

Read the entire prompt file to understand:

- Design context and architectural decisions
- Testing strategy and coverage requirements
- Implementation constraints and patterns

### Step 3: Execute TDD Cycle

Follow the three-phase TDD workflow:

```bash
# Red: Write failing tests
vim tests/unit/<module>/test_<name>.py
uv run pytest tests/unit/<module>/test_<name>.py  # Should fail

# Green: Implement minimal code
vim iptv_sniffer/<module>/<file>.py
uv run pytest tests/unit/<module>/test_<name>.py  # Should pass

# Refactor: Improve code quality
# Run quality gates
uv run pyrefly iptv_sniffer/<module>/<file>.py
uv run ruff check iptv_sniffer/<module>/
uv run pytest --cov=iptv_sniffer/<module>/<file> --cov-report=term-missing
```

### Step 4: Verify Quality Gates

All tasks must pass these quality gates before commit:

- [ ] All tests pass: `pytest`
- [ ] Type checking: `pyrefly check` reports no errors
- [ ] Linting: `ruff check` passes
- [ ] Test coverage: ≥ target percentage (specified in prompt)
- [ ] Module size: < 500 lines (excluding comments/blanks)

### Step 5: Commit Changes

Use conventional commit format:

```bash
git add tests/ iptv_sniffer/
git commit -m "feat(<module>): <description>

- Add <count> unit tests with <X>% coverage
- Implement <key functionality>
- <Additional notes>

Closes #<issue-number>"
```

## Development Phases

### Phase 1: Core Infrastructure (Weeks 1-2)

- [Task 1.1](task-1.1-channel-data-model.md): Channel Data Model
- [Task 1.2](task-1.2-configuration-management.md): Configuration Management
- [Task 1.3](task-1.3-json-storage-repository.md): JSON Storage Repository
- [Task 1.4](task-1.4-cli-structure-with-typer.md): CLI Structure with Typer

### Phase 2: FFmpeg Integration (Weeks 3-4)

- [Task 2.1](task-2.1-ffmpeg-availability-check.md): FFmpeg Availability Check
- [Task 2.2](task-2.2-http-stream-validator.md): HTTP Stream Validator
- [Task 2.3](task-2.3-screenshot-capture.md): Screenshot Capture

### Phase 3: Network Scanning (Weeks 5-7)

- [Task 3.1](task-3.1-strategy-pattern-base.md): Strategy Pattern Base
- [Task 3.2](task-3.2-template-scan-strategy.md): Template Scan Strategy
- [Task 3.3](task-3.3-rate-limiter.md): Rate Limiter
- [Task 3.4](task-3.4-scan-orchestrator.md): Scan Orchestrator

### Phase 4: M3U Support (Week 8)

- [Task 4.1](task-4.1-m3u-parser.md): M3U Parser
- [Task 4.2](task-4.2-character-encoding-detection.md): Character Encoding Detection
- [Task 4.3](task-4.3-m3u-generator.md): M3U Generator

### Phase 5: Multicast Support (Weeks 9-10)

- [Task 5.1](task-5.1-multicast-scan-strategy.md): Multicast Scan Strategy
- [Task 5.2](task-5.2-smart-port-scanner.md): Smart Port Scanner
- [Task 5.3](task-5.3-scan-preset-system.md): Scan Preset System

### Phase 6: Web API (Weeks 11-12)

- [Task 6.1](task-6.1-fastapi-setup.md): FastAPI Setup
- [Task 6.2](task-6.2-scan-endpoints.md): Scan Endpoints

### Phase 7: Web Interface (Weeks 13-17)

- [Task 7.0](task-7.0-vue-vite-frontend-setup.md): Vue 3 + Vite Frontend Setup
- [Task 7.1](task-7.1-vue-router-tab-navigation.md): Vue Router + Tab Navigation
- [Task 7.2](task-7.2-vue-stream-test-page.md): Stream Test Page with Vue
- [Task 7.3](task-7.3-vue-screenshot-display.md): Screenshot Display with Vue
- [Task 7.4](task-7.4-vue-channel-management.md): Channel Management Page with Vue
- [Task 7.5](task-7.5-vue-m3u-import-export.md): M3U Import/Export with Vue
- [Task 7.6](task-7.6-vue-group-management.md): TV Groups Management with Vue

### Phase 8: Docker & Deployment (Week 15)

- [Task 8.1](task-8.1-docker-multi-stage-build.md): Docker Multi-Stage Build

## Quality Standards

All implementations must adhere to:

- **Type Safety**: Full type hints with `pyrefly`
- **Code Style**: `ruff` configured with ANN401 rule (no `Any` in public APIs)
- **Testing**: `pytest` + `pytest-asyncio` for async code
- **Coverage**: Minimum 80% overall, 90% for critical paths
- **Module Size**: Maximum 500 lines per file (excluding comments/blanks)
- **Documentation**: Docstrings for all public APIs

## References

- **Development Plan**: [../development-plan.md](../development-plan.md)
- **System Design**: [../Design.md](../Design.md)
- **Project Guidelines**: [../../AGENTS.md](../../AGENTS.md)

## Support

For questions or issues with prompts:

1. Review the Design.md for architectural context
2. Check development-plan.md for implementation examples
3. Consult AGENTS.md for project conventions
