# Task 5.2: Smart Port Scanner

## Task Overview

**Phase**: 5 - Multicast Support  
**Duration**: 4 hours  
**Complexity**: High

**Goal**: Optimize multicast scanning by detecting port pattern on first IP, reducing scan time by 80%.

**Success Criteria**:

- [ ] All tests pass
- [ ] Type checking passes (mypy --strict)
- [ ] Test coverage ≥ 75%
- [ ] Module size < 500 lines

---

## Design Context

**Smart Port Scanning** (Design.md Section 13, lines 1082-1125):

**Problem**:

- 255 IPs × 30 ports = 7,650 URLs → 21 hours (unacceptable)

**Solution**:

- Phase 1: Scan first IP with all ports, discover pattern (e.g., 5 valid ports)
- Phase 2: Scan remaining IPs with only discovered ports
- Result: 30 + (254 × 5) = 1,300 URLs → 3.6 hours (83% reduction)

---

## Prerequisites

- [x] Task 5.1: Multicast Scan Strategy
- [x] Task 2.2: HTTP Stream Validator

---

## Implementation

**File**: `iptv_sniffer/scanner/smart_port_scanner.py`

```python
class SmartPortScanner:
    """Smart port scanner with pattern detection"""

    def __init__(
        self,
        strategy: MulticastScanStrategy,
        validator: StreamValidator,
        enable_smart_scan: bool = True
    ):
        self.strategy = strategy
        self.validator = validator
        self.enable_smart_scan = enable_smart_scan

    async def scan(self) -> AsyncIterator[StreamValidationResult]:
        if not self.enable_smart_scan:
            # Fallback to full scan
            async for url in self.strategy.generate_targets():
                yield await self.validator.validate(url)
            return

        # Phase 1: Discover ports on first IP
        discovered_ports = await self._discover_ports_on_first_ip()

        if not discovered_ports:
            logger.warning("No valid ports discovered on first IP")
            return

        # Phase 2: Scan remaining IPs with discovered ports
        async for result in self._scan_remaining_ips(discovered_ports):
            yield result

    async def _discover_ports_on_first_ip(self) -> Set[int]:
        """Scan first IP with all ports to discover pattern"""
        discovered = set()
        first_ip = self._get_first_ip()

        for port in self.strategy.ports:
            url = f"{self.strategy.protocol}://{first_ip}:{port}"
            result = await self.validator.validate(url, timeout=20)
            if result.is_valid:
                discovered.add(port)

        return discovered
```

---

## Commit

```bash
git commit -m "feat(scanner): implement smart port scanning with 80% time reduction

- Add SmartPortScanner with two-phase pattern detection
- Phase 1: Discover valid ports on first IP
- Phase 2: Apply pattern to remaining IPs
- Reduce Beijing Unicom scan from 21h to 3.6h (83% reduction)
- Optional disable for exhaustive scanning
- Include 4 unit tests with 78% coverage

Implements Design.md Section 13 optimization strategy

Closes #<issue-number>"
```
