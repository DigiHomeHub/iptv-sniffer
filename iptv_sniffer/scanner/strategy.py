"""Strategy pattern abstractions for IPTV scanning modes."""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import AsyncIterator


class ScanMode(str, Enum):
    """Available scanning modes."""

    TEMPLATE = "template"
    MULTICAST = "multicast"
    M3U_BATCH = "m3u_batch"


class ScanStrategy(ABC):
    """Abstract base class for all scanning strategies."""

    @abstractmethod
    def generate_targets(self) -> AsyncIterator[str]:
        """
        Yield stream URLs for validation.

        Implementations must be declared with `async def` and yield strings.
        """

    @abstractmethod
    def estimate_target_count(self) -> int:
        """Return an estimated number of targets for progress reporting."""


__all__ = ["ScanMode", "ScanStrategy"]
