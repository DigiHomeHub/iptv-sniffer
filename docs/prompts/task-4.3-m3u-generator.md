# Task 4.3: M3U Generator

## Task Overview

**Phase**: 4 - M3U Support  
**Duration**: 2 hours  
**Complexity**: Low

**Goal**: Generate M3U playlists from channel lists with extended attributes.

**Success Criteria**:

- [ ] All tests pass
- [ ] Type checking passes (uv run pyrefly check)
- [ ] Test coverage ≥ 85%

---

## Design Context

**M3U Generation**: Create valid M3U files compatible with VLC, Kodi, and other players.

---

## Prerequisites

- [x] Task 1.1: Channel Data Model
- [x] Task 4.1: M3U Parser (provides M3U models)

---

## Implementation

**File**: `iptv_sniffer/m3u/generator.py`

```python
class M3UGenerator:
    def generate(self, channels: List[Channel]) -> str:
        """Generate M3U content from channel list"""
        lines = ["#EXTM3U"]

        for channel in channels:
            extinf_parts = ["#EXTINF:-1"]

            if channel.tvg_id:
                extinf_parts.append(f'tvg-id="{channel.tvg_id}"')
            if channel.name:
                extinf_parts.append(f'tvg-name="{channel.name}"')
            if channel.tvg_logo:
                extinf_parts.append(f'tvg-logo="{channel.tvg_logo}"')
            if channel.group:
                extinf_parts.append(f'group-title="{channel.group}"')

            extinf_parts.append(channel.name)
            lines.append(" ".join(extinf_parts))
            lines.append(str(channel.url))

        return "\n".join(lines)
```

---

## Commit

```bash
git commit -m "feat(m3u): implement M3U playlist generator

- Add M3UGenerator creating valid M3U format from channels
- Support extended attributes (tvg-*, group-title)
- Output compatible with VLC, Kodi, other players
- Include 4 unit tests with 88% coverage

Completes Phase 4 M3U Support

Closes #<issue-number>"
```

---

## Next Steps

Phase 4 complete! Begin **Phase 5: Multicast Support**
