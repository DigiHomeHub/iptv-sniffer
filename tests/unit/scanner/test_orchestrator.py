from __future__ import annotations

import asyncio
from typing import AsyncIterator, List
import unittest

from iptv_sniffer.scanner.orchestrator import ScanOrchestrator, ScanProgress
from iptv_sniffer.scanner.rate_limiter import RateLimiter
from iptv_sniffer.scanner.strategy import ScanStrategy
from iptv_sniffer.scanner.validator import StreamValidationResult, StreamValidator


class DummyStrategy(ScanStrategy):
    def __init__(self, targets: List[str]):
        self._targets = targets

    def estimate_target_count(self) -> int:
        return len(self._targets)

    async def generate_targets(self) -> AsyncIterator[str]:
        for target in self._targets:
            await asyncio.sleep(0)
            yield target


class DummyValidator(StreamValidator):  # type: ignore[misc]
    def __init__(self, results: List[StreamValidationResult]):
        self._results = results
        self.calls: List[str] = []

    async def validate(self, url: str) -> StreamValidationResult:  # type: ignore[override]
        await asyncio.sleep(0)
        self.calls.append(url)
        return self._results.pop(0)


class ScanOrchestratorTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_execute_scan_yields_results(self) -> None:
        targets = ["http://example.com/a", "http://example.com/b"]
        results = [
            StreamValidationResult(url=targets[0], is_valid=True, protocol="http"),
            StreamValidationResult(url=targets[1], is_valid=False, protocol="http"),
        ]
        validator = DummyValidator(results.copy())
        orchestrator = ScanOrchestrator(validator, max_concurrency=2)
        strategy = DummyStrategy(targets)

        collected = []
        async for result in orchestrator.execute_scan(strategy):
            collected.append(result)

        self.assertEqual([r.url for r in collected], targets)
        self.assertEqual([r.is_valid for r in collected], [True, False])

    async def test_progress_callbacks_receive_updates(self) -> None:
        targets = ["http://example.com/a", "http://example.com/b"]
        results = [
            StreamValidationResult(url=targets[0], is_valid=True, protocol="http"),
            StreamValidationResult(url=targets[1], is_valid=False, protocol="http"),
        ]
        validator = DummyValidator(results.copy())
        orchestrator = ScanOrchestrator(validator)
        strategy = DummyStrategy(targets)

        seen: List[ScanProgress] = []

        async def callback(progress: ScanProgress) -> None:
            seen.append(progress)

        orchestrator.on_progress(callback)

        async for _ in orchestrator.execute_scan(strategy):
            pass

        self.assertEqual(len(seen), 2)
        self.assertEqual(seen[-1].completed, 2)
        self.assertEqual(seen[-1].valid, 1)
        self.assertEqual(seen[-1].invalid, 1)
        self.assertEqual(seen[-1].total, 2)

    async def test_orchestrator_uses_custom_rate_limiter(self) -> None:
        targets = [
            "http://example.com/a",
            "http://example.com/b",
            "http://example.com/c",
        ]
        results = [
            StreamValidationResult(url=targets[0], is_valid=True, protocol="http"),
            StreamValidationResult(url=targets[1], is_valid=True, protocol="http"),
            StreamValidationResult(url=targets[2], is_valid=True, protocol="http"),
        ]
        validator = DummyValidator(results.copy())
        limiter = RateLimiter(max_concurrency=1, timeout=1)
        orchestrator = ScanOrchestrator(validator, rate_limiter=limiter)
        strategy = DummyStrategy(targets)

        collected = []
        async for result in orchestrator.execute_scan(strategy):
            collected.append(result)

        self.assertEqual([r.url for r in collected], targets)
        self.assertEqual(validator.calls, targets)

    async def test_progress_callbacks_run_concurrently(self) -> None:
        targets = ["http://example.com/a"]
        results = [
            StreamValidationResult(url=targets[0], is_valid=True, protocol="http")
        ]
        validator = DummyValidator(results.copy())
        orchestrator = ScanOrchestrator(validator)
        strategy = DummyStrategy(targets)

        order: List[str] = []

        async def cb1(progress: ScanProgress) -> None:
            await asyncio.sleep(0.01)
            order.append("cb1")

        async def cb2(progress: ScanProgress) -> None:
            order.append("cb2")

        orchestrator.on_progress(cb1)
        orchestrator.on_progress(cb2)

        async for _ in orchestrator.execute_scan(strategy):
            pass

        self.assertCountEqual(order, ["cb1", "cb2"])


if __name__ == "__main__":
    unittest.main()
