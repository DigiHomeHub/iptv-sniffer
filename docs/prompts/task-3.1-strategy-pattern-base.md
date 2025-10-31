# Task 3.1: Strategy Pattern Base

## Task Overview

**Phase**: 3 - Network Scanning  
**Duration**: 2 hours  
**Complexity**: Low

**Goal**: Define abstract ScanStrategy interface enabling multiple scanning modes (Template, Multicast, M3U Batch).

**Success Criteria**:

- [ ] All tests pass
- [ ] Type checking passes (uv run pyrefly check)
- [ ] Test coverage 100% (abstract class tests)
- [ ] Module size < 500 lines

---

## Design Context

**Strategy Pattern Decision** (Design.md Section 11, lines 873-981):

- Support three scanning modes via pluggable strategies
- Unified interface: `generate_targets()` and `estimate_target_count()`
- Future-proof for SSDP, custom protocols
- Open/Closed Principle: add strategies without modifying existing code

---

## Prerequisites

- [x] Phase 2 complete (FFmpeg integration)

---

## TDD Implementation Guide

### Phase 1: Red - Write Failing Tests

**Test File**: `tests/unit/scanner/test_strategy.py`

```python
@pytest.mark.asyncio
async def test_scan_strategy_interface():
    """
    Design Intent: All strategies implement required interface
    Validates: Abstract methods defined and enforceable
    """

def test_scan_mode_enum_values():
    """
    Design Intent: ScanMode enum has all expected modes
    Validates: TEMPLATE, MULTICAST, M3U_BATCH present
    """
```

### Phase 2: Green - Minimal Implementation

**Implementation File**: `iptv_sniffer/scanner/strategy.py`

```python
from abc import ABC, abstractmethod
from enum import Enum
from typing import AsyncIterator

class ScanMode(str, Enum):
    TEMPLATE = "template"
    MULTICAST = "multicast"
    M3U_BATCH = "m3u_batch"

class ScanStrategy(ABC):
    """Abstract base class for scanning strategies"""

    @abstractmethod
    async def generate_targets(self) -> AsyncIterator[str]:
        """Generate stream URLs to validate"""
        pass

    @abstractmethod
    def estimate_target_count(self) -> int:
        """Estimate total targets for progress tracking"""
        pass
```

---

## Commit

```bash
git commit -m "feat(scanner): define ScanStrategy abstract base class

- Add ScanStrategy ABC with generate_targets() and estimate_target_count()
- Define ScanMode enum (TEMPLATE, MULTICAST, M3U_BATCH)
- Enable pluggable scanning strategies (Design.md Section 11)

Foundation for Tasks 3.2 (Template), 5.1 (Multicast), 4.1 (M3U Batch)

Closes #<issue-number>"
```

---

## Next Steps

- Task 3.2: Implement TemplateScanStrategy (first concrete strategy)
- Task 5.1: Implement MulticastScanStrategy
- Task 4.1: Implement M3UBatchStrategy
