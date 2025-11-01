from __future__ import annotations

import unittest

from iptv_sniffer.scanner.multicast_strategy import MulticastScanStrategy


class MulticastScanStrategyTestCase(unittest.IsolatedAsyncioTestCase):
    """Validate multicast scan strategy target generation."""

    async def test_generate_targets_from_range_and_ports(self) -> None:
        strategy = MulticastScanStrategy(
            protocol="udp",
            ip_ranges=["239.3.1.1-239.3.1.3"],
            ports=[8000, 8004],
        )

        targets = []
        async for url in strategy.generate_targets():
            targets.append(url)

        self.assertEqual(
            targets,
            [
                "udp://239.3.1.1:8000",
                "udp://239.3.1.1:8004",
                "udp://239.3.1.2:8000",
                "udp://239.3.1.2:8004",
                "udp://239.3.1.3:8000",
                "udp://239.3.1.3:8004",
            ],
        )
        self.assertEqual(strategy.estimate_target_count(), 6)

    async def test_generate_targets_supports_single_address(self) -> None:
        strategy = MulticastScanStrategy(
            protocol="rtp",
            ip_ranges=["239.3.5.10"],
            ports=[9000],
        )

        targets = []
        async for url in strategy.generate_targets():
            targets.append(url)

        self.assertEqual(targets, ["rtp://239.3.5.10:9000"])
        self.assertEqual(strategy.estimate_target_count(), 1)

    def test_rejects_invalid_protocol(self) -> None:
        with self.assertRaises(ValueError):
            MulticastScanStrategy(
                protocol="http",
                ip_ranges=["239.1.1.1-239.1.1.2"],
                ports=[8000],
            )

    def test_rejects_non_multicast_range(self) -> None:
        with self.assertRaises(ValueError):
            MulticastScanStrategy(
                protocol="udp",
                ip_ranges=["192.168.1.1-192.168.1.10"],
                ports=[8000],
            )

    def test_rejects_malformed_range(self) -> None:
        with self.assertRaises(ValueError):
            MulticastScanStrategy(
                protocol="udp",
                ip_ranges=["239.3.1.10-239.3.1.1"],
                ports=[8000],
            )

    def test_rejects_empty_ports(self) -> None:
        with self.assertRaises(ValueError):
            MulticastScanStrategy(
                protocol="udp",
                ip_ranges=["239.3.1.1-239.3.1.2"],
                ports=[],
            )


if __name__ == "__main__":
    unittest.main()
