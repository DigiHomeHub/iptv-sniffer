import io
import asyncio
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from iptv_sniffer.channel.models import Channel
from iptv_sniffer.storage.json_repository import JSONChannelRepository
from iptv_sniffer.web.api.channels import get_repository
from iptv_sniffer.web.app import app


@pytest.fixture()
def repository(tmp_path: Path):
    repo = JSONChannelRepository(tmp_path / "channels.json")
    channels = [
        Channel(
            name="CCTV-1", url="http://example.com/cctv1", group="央视", is_online=True
        ),
        Channel(
            name="CCTV-2",
            url="http://example.com/cctv2",
            group="央视",
            resolution="1080p",
        ),
        Channel(
            name="HBO",
            url="http://example.com/hbo",
            group="影视",
            resolution="4K",
            is_online=True,
        ),
    ]

    async def seed() -> None:
        for channel in channels:
            await repo.add(channel)

    asyncio.run(seed())

    app.dependency_overrides[get_repository] = lambda: repo
    return repo


@pytest.fixture()
def client(repository: JSONChannelRepository):
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_repository, None)


def test_import_m3u_file(client: TestClient):
    payload = io.BytesIO(
        b'#EXTM3U\n#EXTINF:-1 tvg-id="cctv1" group-title="\xe5\xb0\x8f\xe7\xbb\x84",CCTV-1\nhttp://test1.com\n'
        b'#EXTINF:-1 tvg-id="cctv2" group-title="\xe5\xb0\x8f\xe7\xbb\x84",CCTV-2\nhttp://test2.com\n'
    )

    response = client.post(
        "/api/m3u/import",
        files={"file": ("playlist.m3u", payload, "audio/x-mpegurl")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["imported"] == 2
    assert data["failed"] == 0


def test_import_m3u_with_gb2312_encoding(client: TestClient):
    content = "#EXTM3U\n#EXTINF:-1,测试频道\nhttp://test.com".encode("gb2312")

    response = client.post(
        "/api/m3u/import",
        files={"file": ("playlist.m3u", content, "audio/x-mpegurl")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["imported"] == 1
    assert any(
        "测试频道" in (channel.get("name") or "") for channel in data["channels"]
    )


def test_import_invalid_file_format(client: TestClient):
    response = client.post(
        "/api/m3u/import",
        files={"file": ("notes.txt", b"not an m3u\n...", "text/plain")},
    )

    assert response.status_code == 400
    assert "M3U" in response.json()["detail"]


def test_export_all_channels(client: TestClient):
    response = client.get("/api/m3u/export")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("audio/x-mpegurl")
    assert response.text.startswith("#EXTM3U")


def test_export_with_filters(client: TestClient):
    response = client.get("/api/m3u/export?group=央视&status=online")
    assert response.status_code == 200
    body = response.text
    assert "央视" in body
    assert "http://example.com/hbo" not in body


def test_export_empty_result(client: TestClient):
    response = client.get("/api/m3u/export?group=nonexistent")
    assert response.status_code == 200
    assert response.text.strip() == "#EXTM3U"


def test_import_large_m3u_file(client: TestClient):
    lines = ["#EXTM3U"]
    for index in range(2_000):
        lines.append(
            f'#EXTINF:-1 tvg-id="bulk{index}" group-title="Batch",Channel {index}'
        )
        lines.append(f"http://example.com/bulk/{index}")

    payload = "\n".join(lines).encode("utf-8")

    response = client.post(
        "/api/m3u/import",
        files={"file": ("bulk.m3u", payload, "audio/x-mpegurl")},
    )

    assert response.status_code == 200
    assert response.json()["imported"] == 2_000
