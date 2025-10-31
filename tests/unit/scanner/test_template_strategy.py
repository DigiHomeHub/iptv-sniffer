from __future__ import annotations

import unittest

from iptv_sniffer.scanner.template_strategy import TemplateScanStrategy


class TemplateScanStrategyTestCase(unittest.IsolatedAsyncioTestCase):
    """Validate TemplateScanStrategy behaviour."""

    async def test_template_strategy_generates_urls(self) -> None:
        strategy = TemplateScanStrategy(
            base_url="http://192.168.2.2:7788/rtp/{ip}:8000",
            start_ip="192.168.1.1",
            end_ip="192.168.1.3",
        )

        targets = []
        async for url in strategy.generate_targets():
            targets.append(url)

        self.assertEqual(
            targets,
            [
                "http://192.168.2.2:7788/rtp/192.168.1.1:8000",
                "http://192.168.2.2:7788/rtp/192.168.1.2:8000",
                "http://192.168.2.2:7788/rtp/192.168.1.3:8000",
            ],
        )
        self.assertEqual(strategy.estimate_target_count(), 3)

    def test_template_strategy_requires_private_ips(self) -> None:
        with self.assertRaises(ValueError):
            TemplateScanStrategy(
                base_url="http://192.168.2.2:7788/rtp/{ip}:8000",
                start_ip="8.8.8.1",
                end_ip="8.8.8.10",
            )

    def test_template_strategy_range_limit(self) -> None:
        with self.assertRaises(ValueError):
            TemplateScanStrategy(
                base_url="http://gateway/stream/{ip}",
                start_ip="192.168.0.0",
                end_ip="192.168.4.0",
            )

    def test_template_strategy_requires_placeholder(self) -> None:
        with self.assertRaises(ValueError):
            TemplateScanStrategy(
                base_url="http://192.168.2.2:7788/rtp/",
                start_ip="192.168.1.1",
                end_ip="192.168.1.1",
            )

    def test_template_strategy_requires_start_not_greater_than_end(self) -> None:
        with self.assertRaises(ValueError):
            TemplateScanStrategy(
                base_url="http://192.168.2.2:7788/rtp/{ip}:8000",
                start_ip="192.168.1.10",
                end_ip="192.168.1.1",
            )


if __name__ == "__main__":
    unittest.main()
