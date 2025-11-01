from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from iptv_sniffer.scanner.presets import PresetLoader, ScanPreset
from iptv_sniffer.scanner.multicast_strategy import MulticastScanStrategy


class PresetLoaderTestCase(unittest.TestCase):
    def _write_preset_file(self, data: dict) -> Path:
        temp = tempfile.NamedTemporaryFile("w+", delete=False, encoding="utf-8")
        json.dump(data, temp)
        temp.flush()
        temp.close()
        return Path(temp.name)

    def test_load_all_returns_presets(self) -> None:
        preset_path = self._write_preset_file(
            {
                "presets": [
                    {
                        "id": "beijing-unicom",
                        "name": "北京联通 IPTV",
                        "protocol": "rtp",
                        "ip_ranges": ["239.3.1.1-239.3.1.10"],
                        "ports": [8000, 8004],
                        "estimated_targets": 80,
                        "estimated_duration": "1h",
                    }
                ]
            }
        )

        try:
            loader = PresetLoader(preset_path)
            presets = loader.load_all()

            self.assertEqual(len(presets), 1)
            preset = presets[0]
            self.assertIsInstance(preset, ScanPreset)
            self.assertEqual(preset.id, "beijing-unicom")
            self.assertEqual(preset.ports, [8000, 8004])
        finally:
            preset_path.unlink(missing_ok=True)

    def test_get_by_id_returns_expected_preset(self) -> None:
        preset_path = self._write_preset_file(
            {
                "presets": [
                    {
                        "id": "beijing-unicom",
                        "name": "北京联通 IPTV",
                        "protocol": "rtp",
                        "ip_ranges": ["239.3.1.1-239.3.1.10"],
                        "ports": [8000, 8004],
                    },
                    {
                        "id": "shanghai-telecom",
                        "name": "Shanghai Telecom",
                        "protocol": "udp",
                        "ip_ranges": ["239.4.1.1-239.4.1.50"],
                        "ports": [9000, 9004],
                    },
                ]
            }
        )
        try:
            loader = PresetLoader(preset_path)

            preset = loader.get_by_id("shanghai-telecom")

            self.assertIsNotNone(preset)
            assert preset is not None  # typing guard
            self.assertEqual(preset.protocol, "udp")
            self.assertEqual(preset.ip_ranges, ["239.4.1.1-239.4.1.50"])
        finally:
            preset_path.unlink(missing_ok=True)

    def test_get_by_id_returns_none_when_missing(self) -> None:
        preset_path = self._write_preset_file({"presets": []})
        try:
            loader = PresetLoader(preset_path)

            preset = loader.get_by_id("missing")

            self.assertIsNone(preset)
        finally:
            preset_path.unlink(missing_ok=True)

    def test_scan_preset_to_strategy(self) -> None:
        preset = ScanPreset(
            id="custom",
            name="Custom Provider",
            protocol="udp",
            ip_ranges=["239.5.1.1-239.5.1.5"],
            ports=[7000, 7004],
            estimated_targets=30,
        )

        strategy = preset.to_strategy()

        self.assertIsInstance(strategy, MulticastScanStrategy)
        self.assertEqual(strategy.protocol, "udp")
        self.assertEqual(strategy.ports, (7000, 7004))
        self.assertEqual(list(strategy.iter_ip_addresses())[0].compressed, "239.5.1.1")


if __name__ == "__main__":
    unittest.main()
