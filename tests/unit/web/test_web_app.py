from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from iptv_sniffer.web.app import app


class FastAPIAppTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_health_endpoint_returns_status(self) -> None:
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "ok")
        self.assertIn("checks", body)
        self.assertIn("ffmpeg", body["checks"])

    def test_openapi_docs_available(self) -> None:
        response = self.client.get("/docs")
        self.assertEqual(response.status_code, 200)

        response_json = self.client.get("/openapi.json")
        self.assertEqual(response_json.status_code, 200)
        self.assertIn("paths", response_json.json())


if __name__ == "__main__":
    unittest.main()
