from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from iptv_sniffer.web.app import app

client = TestClient(app)


def test_screenshot_endpoint_serves_image(tmp_path: Path) -> None:
    screenshot_dir = tmp_path / "screenshots"
    screenshot_dir.mkdir()
    screenshot_file = screenshot_dir / "sample.png"
    screenshot_file.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 8)

    with patch("iptv_sniffer.web.api.screenshots.AppConfig") as mock_config:
        mock_config.return_value.screenshot_dir = screenshot_dir

        response = client.get("/api/screenshots/sample.png")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert "Cache-Control" in response.headers
    assert response.content.startswith(b"\x89PNG\r\n\x1a\n")


def test_missing_screenshot_returns_404(tmp_path: Path) -> None:
    with patch("iptv_sniffer.web.api.screenshots.AppConfig") as mock_config:
        mock_config.return_value.screenshot_dir = tmp_path / "screenshots"

        response = client.get("/api/screenshots/missing.png")

    assert response.status_code == 404
    assert response.json()["detail"] == "Screenshot not found"


def test_directory_traversal_blocked(tmp_path: Path) -> None:
    with patch("iptv_sniffer.web.api.screenshots.AppConfig") as mock_config:
        mock_config.return_value.screenshot_dir = tmp_path / "screenshots"

        response = client.get("/api/screenshots/..%2F..%2Fetc%2Fpasswd")

    assert response.status_code in (403, 404)
    detail = response.json().get("detail")
    assert detail in {"Access denied", "Screenshot not found", "Not Found"}
