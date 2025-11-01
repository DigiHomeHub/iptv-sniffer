from __future__ import annotations

import asyncio
import unittest
from typing import AsyncIterator, List
from unittest.mock import patch

from iptv_sniffer.scanner.strategy import ScanMode, ScanStrategy
from iptv_sniffer.scanner.validator import StreamValidationResult
from iptv_sniffer.web.api.scan import ScanManager, ScanStartRequest, ScanStatus


class DummyStrategy(ScanStrategy):
    def __init__(self, targets: List[str]) -> None:
        self._targets = targets

    async def generate_targets(self) -> AsyncIterator[str]:
        for target in self._targets:
            yield target

    def estimate_target_count(self) -> int:
        return len(self._targets)


class StubOrchestrator:
    async def execute_scan(
        self, strategy: ScanStrategy
    ) -> AsyncIterator[StreamValidationResult]:
        async for target in strategy.generate_targets():
            yield StreamValidationResult(
                url=target, protocol="udp", is_valid="valid" in target
            )


class ScanManagerTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_scan_manager_completes_scan(self) -> None:
        manager = ScanManager(
            preset_loader=None, orchestrator_factory=lambda: StubOrchestrator()
        )
        strategy = DummyStrategy(
            ["udp://239.1.1.1:8000", "udp://239.1.1.2:8000", "udp://valid.example:8000"]
        )
        request = ScanStartRequest(
            mode=ScanMode.MULTICAST,
            protocol="udp",
            ip_ranges=["239.1.1.1-239.1.1.1"],
            ports=[8000],
        )

        with patch.object(
            manager, "_build_strategy_from_request", return_value=strategy
        ):
            session = await manager.start_scan(request, timeout=10)

        await asyncio.sleep(0)
        if session.task:
            await session.task

        updated = await manager.get_scan(session.scan_id)
        self.assertEqual(updated.status, ScanStatus.COMPLETED)
        self.assertEqual(updated.progress, 3)
        self.assertEqual(updated.valid, 1)
        self.assertEqual(updated.invalid, 2)

    async def test_cancel_scan_marks_session_cancelled(self) -> None:
        manager = ScanManager(
            preset_loader=None, orchestrator_factory=lambda: StubOrchestrator()
        )
        strategy = DummyStrategy(["udp://stream/1", "udp://stream/2"])
        request = ScanStartRequest(
            mode=ScanMode.MULTICAST,
            protocol="udp",
            ip_ranges=["239.1.1.1-239.1.1.1"],
            ports=[8000],
        )

        with patch.object(
            manager, "_build_strategy_from_request", return_value=strategy
        ):
            session = await manager.start_scan(request, timeout=10)

        await asyncio.sleep(0)
        await manager.cancel_scan(session.scan_id)
        updated = await manager.get_scan(session.scan_id)
        self.assertEqual(updated.status, ScanStatus.CANCELLED)


if __name__ == "__main__":
    unittest.main()
