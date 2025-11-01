from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from .multicast_strategy import MulticastScanStrategy


class ScanPreset(BaseModel):
    """Configuration describing a multicast scan preset."""

    model_config = ConfigDict(frozen=True)

    id: str
    name: str
    description: Optional[str] = None
    protocol: str = Field(description="Multicast protocol (udp/rtp).")
    ip_ranges: List[str] = Field(default_factory=list)
    ports: List[int] = Field(default_factory=list)
    estimated_targets: Optional[int] = None
    estimated_duration: Optional[str] = None
    reference: Optional[str] = None

    def to_strategy(self) -> MulticastScanStrategy:
        """Convert preset parameters into a multicast scan strategy."""
        return MulticastScanStrategy(
            protocol=self.protocol,
            ip_ranges=self.ip_ranges,
            ports=self.ports,
        )


class PresetLoader:
    """Load scan presets from JSON configuration files."""

    def __init__(self, preset_file: Path) -> None:
        self._preset_file = preset_file

    def load_all(self) -> List[ScanPreset]:
        """Load all presets contained in configured JSON file."""
        with self._preset_file.open("r", encoding="utf-8") as handle:
            raw = json.load(handle)
        preset_data = raw.get("presets", [])
        return [ScanPreset(**entry) for entry in preset_data]

    def get_by_id(self, preset_id: str) -> Optional[ScanPreset]:
        """Retrieve preset by identifier."""
        for preset in self.load_all():
            if preset.id == preset_id:
                return preset
        return None


__all__ = ["ScanPreset", "PresetLoader"]
