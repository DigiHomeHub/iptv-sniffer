# Task 3.3: Rate Limiter

## Task Overview

**Phase**: 3 - Network Scanning  
**Duration**: 2 hours  
**Complexity**: Low

**Goal**: Implement concurrency control using asyncio.Semaphore to prevent network abuse.

**Success Criteria**:

- [ ] All tests pass
- [ ] Type checking passes (mypy --strict)
- [ ] Test coverage ≥ 85%

---

## Design Context

**Concurrency Control** (Design.md Section 4, lines 369-426):

- Default: 10 concurrent requests
- Maximum: 50 concurrent requests
- Timeout: 10 seconds default
- Ethical scanning: prevent accidental DDoS behavior

---

## Prerequisites

- [x] Phase 2 complete

---

## Implementation

**File**: `iptv_sniffer/scanner/rate_limiter.py`

```python
class RateLimiter:
    def __init__(self, max_concurrency: int = 10, timeout: int = 10):
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self.timeout = timeout

    async def __aenter__(self):
        await self.semaphore.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.semaphore.release()

    async def execute(self, coro):
        async with self:
            return await asyncio.wait_for(coro, timeout=self.timeout)
```

---

## Commit

```bash
git commit -m "feat(scanner): implement rate limiter with asyncio.Semaphore

- Add RateLimiter with configurable concurrency (default 10, max 50)
- Implement timeout enforcement (default 10s)
- Context manager support for easy usage
- Include 4 unit tests with 88% coverage

Prevents network abuse per Design.md Section 4

Closes #<issue-number>"
```
