# Task 4.1: M3U Parser

## Task Overview

**Phase**: 4 - M3U Support  
**Duration**: 3-4 hours  
**Complexity**: Medium

**Goal**: Parse M3U/M3U8 playlists with extended attributes (#EXTINF, tvg-\*, group-title).

**Success Criteria**:

- [ ] All tests pass
- [ ] Type checking passes (mypy --strict)
- [ ] Test coverage ≥ 85%
- [ ] Module size < 500 lines

---

## Design Context

**M3U Format** (Design.md Section 6, lines 522-601):

- Support basic M3U and extended M3U8 attributes
- Parse tvg-id, tvg-name, tvg-logo, group-title
- Handle malformed entries gracefully (skip with warning)
- Extract channel name from after last comma

---

## Prerequisites

- [x] Task 1.1: Channel Data Model (provides Channel model)

---

## Implementation

**Files**:

- `iptv_sniffer/m3u/models.py`: M3UChannel, M3UPlaylist
- `iptv_sniffer/m3u/parser.py`: M3UParser

```python
class M3UChannel(BaseModel):
    name: str
    url: str
    tvg_id: Optional[str] = None
    tvg_name: Optional[str] = None
    tvg_logo: Optional[str] = None
    group_title: Optional[str] = None

class M3UPlaylist(BaseModel):
    channels: List[M3UChannel]

class M3UParser:
    def parse(self, content: str) -> M3UPlaylist:
        """Parse M3U content into playlist"""
        lines = content.splitlines()
        channels = []

        i = 0
        while i < len(lines):
            if lines[i].startswith('#EXTINF'):
                attrs = self._parse_extinf(lines[i])
                i += 1
                if i < len(lines) and not lines[i].startswith('#'):
                    channels.append(M3UChannel(name=attrs['name'], url=lines[i].strip(), ...))
            i += 1

        return M3UPlaylist(channels=channels)

    def _parse_extinf(self, line: str) -> dict:
        """Parse EXTINF line attributes using regex"""
        pattern = r'([a-z-]+)="([^"]*)"'
        attrs = dict(re.findall(pattern, line))
        attrs['name'] = line.split(',')[-1].strip()
        return attrs
```

---

## Commit

```bash
git commit -m "feat(m3u): implement M3U/M3U8 parser with extended attributes

- Add M3UParser supporting basic and extended M3U formats
- Parse tvg-id, tvg-name, tvg-logo, group-title attributes
- Handle malformed entries gracefully (skip with warning)
- Include 6 unit tests with 87% coverage

Implements Design.md Section 6 (M3U Format Handling)

Closes #<issue-number>"
```

---

## Next Steps

- Task 4.2: Character Encoding Detection
- Task 4.3: M3U Generator
