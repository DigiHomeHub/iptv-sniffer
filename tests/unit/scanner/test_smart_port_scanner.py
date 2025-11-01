from __future__ import annotations

import unittest
from typing import Dict, List, Tuple

from iptv_sniffer.scanner.multicast_strategy import MulticastScanStrategy
from iptv_sniffer.scanner.smart_port_scanner import SmartPortScanner
from iptv_sniffer.scanner.validator import StreamValidationResult


class FakeValidator:
    """Test fake implementing validator protocol."""

    def __init__(self, responses: Dict[str, bool]) -> None:
        self._responses = responses
        self.calls: List[Tuple[str, int]] = []

    async def validate(self, url: str, timeout: int = 10) -> StreamValidationResult:
        self.calls.append((url, timeout))
        protocol, _ = url.split("://", 1)
        is_valid = self._responses.get(url, False)
        return StreamValidationResult(url=url, protocol=protocol, is_valid=is_valid)


class SmartPortScannerTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_discovered_ports_reduce_follow_up_scan(self) -> None:
        strategy = MulticastScanStrategy(
            protocol="udp",
            ip_ranges=["239.3.1.1-239.3.1.2"],
            ports=[8000, 8004, 8008],
        )
        responses = {
            "udp://239.3.1.1:8004": True,
            "udp://239.3.1.2:8004": True,
        }
        validator = FakeValidator(responses)

        scanner = SmartPortScanner(strategy, validator)

        results = [result async for result in scanner.scan()]

        self.assertEqual(len(results), 4)  # 3 from first IP, 1 from second IP
        self.assertIn("udp://239.3.1.2:8004", {r.url for r in results})

        expected_urls = {
            "udp://239.3.1.1:8000",
            "udp://239.3.1.1:8004",
            "udp://239.3.1.1:8008",
            "udp://239.3.1.2:8004",
        }
        self.assertSetEqual({call[0] for call in validator.calls}, expected_urls)

        discovery_timeouts = {
            call for call in validator.calls if call[0].startswith("udp://239.3.1.1")
        }
        self.assertTrue(any(timeout == 20 for _, timeout in discovery_timeouts))

    async def test_fallback_scans_all_ports_when_none_discovered(self) -> None:
        strategy = MulticastScanStrategy(
            protocol="udp",
            ip_ranges=["239.3.2.1-239.3.2.3"],
            ports=[8000, 8004],
        )
        responses: Dict[str, bool] = {}
        validator = FakeValidator(responses)
        scanner = SmartPortScanner(strategy, validator)

        results = [result async for result in scanner.scan()]

        self.assertEqual(len(results), 6)  # 3 IPs × 2 ports

        expected_urls = {
            "udp://239.3.2.1:8000",
            "udp://239.3.2.1:8004",
            "udp://239.3.2.2:8000",
            "udp://239.3.2.2:8004",
            "udp://239.3.2.3:8000",
            "udp://239.3.2.3:8004",
        }
        self.assertSetEqual({call[0] for call in validator.calls}, expected_urls)

    async def test_disable_smart_scan_scans_full_matrix(self) -> None:
        strategy = MulticastScanStrategy(
            protocol="rtp",
            ip_ranges=["239.3.5.1-239.3.5.2"],
            ports=[7000, 7004],
        )
        validator = FakeValidator({"rtp://239.3.5.1:7004": True})
        scanner = SmartPortScanner(strategy, validator, enable_smart_scan=False)

        results = [result async for result in scanner.scan()]

        self.assertEqual(len(results), 4)
        expected_urls = {
            "rtp://239.3.5.1:7000",
            "rtp://239.3.5.1:7004",
            "rtp://239.3.5.2:7000",
            "rtp://239.3.5.2:7004",
        }
        self.assertSetEqual({call[0] for call in validator.calls}, expected_urls)

    async def test_single_ip_smart_scan_processes_ports_once(self) -> None:
        strategy = MulticastScanStrategy(
            protocol="udp",
            ip_ranges=["239.3.8.10"],
            ports=[8100, 8101],
        )
        validator = FakeValidator({"udp://239.3.8.10:8101": True})
        scanner = SmartPortScanner(strategy, validator)

        results = [result async for result in scanner.scan()]

        self.assertEqual(len(results), 2)
        expected_urls = {
            "udp://239.3.8.10:8100",
            "udp://239.3.8.10:8101",
        }
        self.assertSetEqual({call[0] for call in validator.calls}, expected_urls)


if __name__ == "__main__":
    unittest.main()
