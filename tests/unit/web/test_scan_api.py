from __future__ import annotations

import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from iptv_sniffer.scanner.strategy import ScanMode
from iptv_sniffer.web.api.scan import ScanNotFoundError, ScanSession, ScanStatus
from iptv_sniffer.web.app import app


class ScanApiTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    @patch("iptv_sniffer.web.api.scan.scan_manager.start_scan", new_callable=AsyncMock)
    def test_start_scan_template(self, mock_start: AsyncMock) -> None:
        session = ScanSession(
            scan_id="test-scan-id",
            strategy=MagicMock(),
            status=ScanStatus.PENDING,
            total=3,
        )
        mock_start.return_value = session

        response = self.client.post(
            "/api/scan/start",
            json={
                "mode": ScanMode.TEMPLATE.value,
                "base_url": "http://gateway/stream/{ip}",
                "start_ip": "192.168.1.10",
                "end_ip": "192.168.1.12",
            },
        )

        self.assertEqual(response.status_code, 202)
        payload = response.json()
        self.assertEqual(payload["scan_id"], "test-scan-id")
        self.assertEqual(payload["status"], ScanStatus.PENDING.value)
        self.assertEqual(payload["total"], 3)
        mock_start.assert_awaited()

    def test_start_scan_missing_template_fields_returns_422(self) -> None:
        response = self.client.post(
            "/api/scan/start",
            json={
                "mode": ScanMode.TEMPLATE.value,
                "base_url": "http://gateway/stream/{ip}",
            },
        )
        self.assertEqual(response.status_code, 422)

    @patch("iptv_sniffer.web.api.scan.scan_manager.get_scan", new_callable=AsyncMock)
    def test_get_scan_not_found(self, mock_get: AsyncMock) -> None:
        mock_get.side_effect = ScanNotFoundError()
        response = self.client.get("/api/scan/missing")
        self.assertEqual(response.status_code, 404)

    @patch("iptv_sniffer.web.api.scan.scan_manager.cancel_scan", new_callable=AsyncMock)
    def test_cancel_scan(self, mock_cancel: AsyncMock) -> None:
        session = ScanSession(
            scan_id="cancel-id",
            strategy=MagicMock(),
            status=ScanStatus.CANCELLED,
        )
        mock_cancel.return_value = session

        response = self.client.delete("/api/scan/cancel-id")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["scan_id"], "cancel-id")
        self.assertTrue(payload["cancelled"])


if __name__ == "__main__":
    unittest.main()
