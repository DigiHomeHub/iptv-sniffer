from __future__ import annotations

import asyncio
import unittest
from typing import AsyncIterator

from iptv_sniffer.scanner.strategy import ScanMode, ScanStrategy


class ConcreteStrategy(ScanStrategy):
    """Simple concrete implementation for testing."""

    def __init__(self, targets: list[str]):
        self._targets = targets

    async def generate_targets(self) -> AsyncIterator[str]:
        for target in self._targets:
            await asyncio.sleep(0)
            yield target

    def estimate_target_count(self) -> int:
        return len(self._targets)


class ScanStrategyTestCase(unittest.IsolatedAsyncioTestCase):
    """Ensure base strategy interface behaves as expected."""

    async def test_scan_strategy_interface(self) -> None:
        targets = ["http://example.com/1", "http://example.com/2"]
        strategy = ConcreteStrategy(targets)

        collected = []
        async for target in strategy.generate_targets():
            collected.append(target)

        self.assertEqual(collected, targets)
        self.assertEqual(strategy.estimate_target_count(), len(targets))

    def test_scan_mode_enum_values(self) -> None:
        self.assertEqual(
            {mode.value for mode in ScanMode},
            {"template", "multicast", "m3u_batch"},
        )


if __name__ == "__main__":
    unittest.main()
