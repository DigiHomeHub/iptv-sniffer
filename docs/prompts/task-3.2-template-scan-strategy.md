# Task 3.2: Template Scan Strategy

## Task Overview

**Phase**: 3 - Network Scanning  
**Duration**: 3-4 hours  
**Complexity**: Medium  

**Goal**: Implement URL template scanning with IP range generation and private network validation.

**Success Criteria**:
- [ ] All tests pass
- [ ] Type checking passes (mypy --strict)
- [ ] Test coverage ≥ 90%
- [ ] Module size < 500 lines

---

## Design Context

**HTTP Probing Strategy** (Design.md Section 3, lines 321-368):
- User provides URL template: `http://192.168.2.2:7788/rtp/{ip}:8000`
- System generates URLs by replacing `{ip}` placeholder
- Security: Only RFC1918 private networks allowed (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)
- Maximum range: 1024 IPs to prevent DoS-like behavior

---

## Prerequisites

- [x] Task 3.1: Strategy Pattern Base (provides ScanStrategy ABC)

---

## TDD Implementation Guide

### Phase 1: Red - Tests

```python
@pytest.mark.asyncio
async def test_template_strategy_generates_urls():
    """Validate URL generation with {ip} substitution"""

def test_template_strategy_validates_private_ips():
    """Reject public IP ranges (security)"""

def test_template_strategy_validates_ip_range_size():
    """Reject ranges larger than 1024 IPs"""
```

### Phase 2: Green - Implementation

**File**: `iptv_sniffer/scanner/template_strategy.py`

```python
class TemplateScanStrategy(ScanStrategy):
    def __init__(self, base_url: str, start_ip: str, end_ip: str):
        self._validate_private_network()
        self._validate_range_size()

    async def generate_targets(self) -> AsyncIterator[str]:
        for ip in self._generate_ip_range():
            yield self.base_url.replace('{ip}', str(ip))

    def estimate_target_count(self) -> int:
        return self._calculate_ip_count()
```

---

## Commit

```bash
git commit -m "feat(scanner): implement template-based IP range scanning

- Add TemplateScanStrategy with {ip} placeholder substitution
- Enforce RFC1918 private network validation (security)
- Limit range to 1024 IPs maximum (prevent network abuse)
- Include 6 unit tests with 92% coverage

Implements Design.md Section 3 (HTTP Probing Strategy)

Closes #<issue-number>"
```

---

## Next Steps

- Task 3.3: Rate Limiter (throttle URL validation)
- Task 3.4: Scan Orchestrator (use this strategy for scanning)
