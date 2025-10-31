# Task 5.1: Multicast Scan Strategy

## Task Overview

**Phase**: 5 - Multicast Support  
**Duration**: 3 hours  
**Complexity**: Medium

**Goal**: Implement multicast scanning strategy for RTP/UDP IPTV streams.

**Success Criteria**:

- [ ] All tests pass
- [ ] Type checking passes (mypy --strict)
- [ ] Test coverage ≥ 85%

---

## Design Context

**Multicast Scanning**: Generate all combinations of IP ranges × port lists for RTP/UDP protocols.

**Example**:

- IP ranges: ["239.3.1.1-239.3.1.10"]
- Ports: [8000, 8004, 8008]
- Generated: 10 IPs × 3 ports = 30 URLs

---

## Prerequisites

- [x] Task 3.1: Strategy Pattern Base

---

## Implementation

**File**: `iptv_sniffer/scanner/multicast_strategy.py`

```python
class MulticastScanStrategy(ScanStrategy):
    def __init__(self, protocol: str, ip_ranges: List[str], ports: List[int]):
        self.protocol = protocol
        self.ip_ranges = ip_ranges
        self.ports = ports

    async def generate_targets(self) -> AsyncIterator[str]:
        for ip_range in self.ip_ranges:
            for ip in self._parse_ip_range(ip_range):
                for port in self.ports:
                    yield f"{self.protocol}://{ip}:{port}"

    def estimate_target_count(self) -> int:
        total_ips = sum(self._count_ips_in_range(r) for r in self.ip_ranges)
        return total_ips * len(self.ports)
```

---

## Commit

```bash
git commit -m "feat(scanner): implement multicast scan strategy for RTP/UDP

- Add MulticastScanStrategy with IP range × port list generation
- Support multiple IP ranges (e.g., 239.3.1.x, 239.3.2.x)
- Accurate target count estimation for progress tracking
- Include 5 unit tests with 87% coverage

Enables ISP IPTV scanning (Beijing Unicom, etc.)

Closes #<issue-number>"
```
