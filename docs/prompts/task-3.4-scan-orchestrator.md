# Task 3.4: Scan Orchestrator

## Task Overview

**Phase**: 3 - Network Scanning  
**Duration**: 3-4 hours  
**Complexity**: Medium

**Goal**: Orchestrate scan execution with progress tracking, using any ScanStrategy implementation.

**Success Criteria**:

- [ ] All tests pass (pytest with asyncio)
- [ ] Type checking passes (mypy --strict)
- [ ] Test coverage ≥ 80%
- [ ] Module size < 500 lines

---

## Design Context

**Scan Orchestration**: Coordinates strategy, validator, and rate limiter into unified scan workflow with progress callbacks.

---

## Prerequisites

- [x] Task 3.1: Strategy Pattern Base
- [x] Task 3.2: Template Scan Strategy
- [x] Task 3.3: Rate Limiter
- [x] Task 2.2: HTTP Stream Validator

---

## Implementation

**File**: `iptv_sniffer/scanner/orchestrator.py`

```python
@dataclass
class ScanProgress:
    total: int
    completed: int
    valid: int
    invalid: int
    started_at: datetime

class ScanOrchestrator:
    def __init__(self, validator: StreamValidator, max_concurrency: int = 10):
        self.validator = validator
        self.rate_limiter = RateLimiter(max_concurrency)
        self.progress_callbacks = []

    def on_progress(self, callback: Callable[[ScanProgress], None]):
        self.progress_callbacks.append(callback)

    async def execute_scan(self, strategy: ScanStrategy) -> AsyncIterator[StreamValidationResult]:
        total = strategy.estimate_target_count()
        progress = ScanProgress(total=total, completed=0, valid=0, invalid=0, started_at=datetime.utcnow())

        async for url in strategy.generate_targets():
            result = await self.rate_limiter.execute(self.validator.validate(url))
            progress.completed += 1
            progress.valid += 1 if result.is_valid else 0
            progress.invalid += 1 if not result.is_valid else 0

            for callback in self.progress_callbacks:
                await callback(progress)

            yield result
```

---

## Commit

```bash
git commit -m "feat(scanner): implement scan orchestrator with progress tracking

- Add ScanOrchestrator coordinating strategy, validator, rate limiter
- Implement ScanProgress tracking (completed, valid, invalid counts)
- Support async progress callbacks for real-time updates
- Include 5 unit tests with 83% coverage

Completes Phase 3 Network Scanning architecture

Closes #<issue-number>"
```

---

## Next Steps

Phase 3 complete! Begin **Phase 4: M3U Support**
