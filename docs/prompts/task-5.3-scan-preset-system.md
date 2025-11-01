# Task 5.3: Scan Preset System

## Task Overview

**Phase**: 5 - Multicast Support  
**Duration**: 2-3 hours  
**Complexity**: Low-Medium

**Goal**: Implement preset configuration system for common IPTV providers (Beijing Unicom, Shanghai Telecom).

**Success Criteria**:

- [ ] All tests pass
- [ ] Type checking passes (uv run pyrefly check)
- [ ] Test coverage ≥ 80%

---

## Design Context

**Preset System** (Design.md Section 15, lines 1207-1305):

- Curated presets for common IPTV providers
- JSON configuration file: `config/multicast_presets.json`
- Each preset: id, name, description, protocol, ip_ranges, ports, estimated_targets
- Users can select preset or override fields

---

## Prerequisites

- [x] Task 5.1: Multicast Scan Strategy

---

## Implementation

**Files**:

- `iptv_sniffer/scanner/presets.py`: PresetLoader, ScanPreset
- `config/multicast_presets.json`: Default presets

```python
class ScanPreset(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    protocol: str
    ip_ranges: List[str]
    ports: List[int]
    estimated_targets: Optional[int] = None
    estimated_duration: Optional[str] = None
    reference: Optional[str] = None

    def to_strategy(self) -> MulticastScanStrategy:
        return MulticastScanStrategy(
            protocol=self.protocol,
            ip_ranges=self.ip_ranges,
            ports=self.ports
        )

class PresetLoader:
    def __init__(self, preset_file: Path):
        self.preset_file = preset_file

    def load_all(self) -> List[ScanPreset]:
        with open(self.preset_file) as f:
            data = json.load(f)
        return [ScanPreset(**p) for p in data.get("presets", [])]

    def get_by_id(self, preset_id: str) -> Optional[ScanPreset]:
        return next((p for p in self.load_all() if p.id == preset_id), None)
```

**Default Presets** (`config/multicast_presets.json`):

```json
{
  "presets": [
    {
      "id": "beijing-unicom",
      "name": "北京联通 IPTV",
      "protocol": "rtp",
      "ip_ranges": ["239.3.1.1-239.3.1.255"],
      "ports": [8000, 8004, 8008, 8012, 8016, 8020],
      "estimated_targets": 1530,
      "estimated_duration": "2-3 hours (with smart scanning)"
    }
  ]
}
```

---

## Commit

```bash
git commit -m "feat(scanner): add preset system for common IPTV providers

- Add ScanPreset model and PresetLoader
- Create default presets (Beijing Unicom, Shanghai Telecom)
- Enable preset selection in API/CLI
- Support preset field overrides
- Include 4 unit tests with 83% coverage

Lowers barrier to entry for multicast scanning (Design.md Section 15)

Closes #<issue-number>"
```

---

## Next Steps

Phase 5 complete! Begin **Phase 6: Web API**
