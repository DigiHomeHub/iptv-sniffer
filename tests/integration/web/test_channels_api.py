import asyncio
from typing import List

import pytest
from fastapi.testclient import TestClient

from iptv_sniffer.channel.models import Channel
from iptv_sniffer.storage.json_repository import JSONChannelRepository
from iptv_sniffer.web.api.channels import get_repository
from iptv_sniffer.web.app import app


@pytest.fixture
def repository(tmp_path):
    repo = JSONChannelRepository(tmp_path / "channels.json")

    channels: List[Channel] = [
        Channel(
            name="CCTV-1", url="http://test1.com", group="央视", resolution="1080p"
        ),
        Channel(name="CCTV-2", url="http://test2.com", group="央视", resolution="720p"),
        Channel(
            name="Phoenix TV", url="http://test3.com", group="凤凰", is_online=True
        ),
        Channel(
            name="HBO",
            url="http://test4.com",
            group="影视",
            resolution="4K",
            is_online=True,
        ),
    ]

    async def seed():
        for channel in channels:
            await repo.add(channel)

    asyncio.run(seed())

    return repo


@pytest.fixture
def client(repository):
    app.dependency_overrides[get_repository] = lambda: repository
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_repository, None)


def test_list_channels_with_pagination(client, repository):
    response = client.get("/api/channels?page=1&page_size=2")
    assert response.status_code == 200

    data = response.json()
    assert data["total"] == 4
    assert len(data["channels"]) == 2
    assert data["page"] == 1
    assert data["pages"] == 2


def test_filter_channels_by_group(client):
    response = client.get("/api/channels?group=央视")
    assert response.status_code == 200

    data = response.json()
    assert data["total"] == 2
    assert all(ch["group"] == "央视" for ch in data["channels"])


def test_filter_channels_by_resolution(client):
    response = client.get("/api/channels?resolution=1080p")
    assert response.status_code == 200

    data = response.json()
    assert data["total"] == 1
    assert data["channels"][0]["resolution"] == "1080p"


def test_filter_channels_by_status(client):
    response = client.get("/api/channels?status=online")
    assert response.status_code == 200

    data = response.json()
    assert data["total"] == 2
    assert all(ch["is_online"] for ch in data["channels"])


def test_search_channels_by_name(client):
    response = client.get("/api/channels?search=CCTV")
    assert response.status_code == 200

    data = response.json()
    assert data["total"] == 2
    assert all("cctv" in ch["name"].lower() for ch in data["channels"])


def test_get_channel_by_id(client, repository):
    [channel] = [ch for ch in asyncio.run(repository.find_all()) if ch.name == "CCTV-1"]
    response = client.get(f"/api/channels/{channel.id}")
    assert response.status_code == 200
    assert response.json()["id"] == channel.id


def test_update_channel_info(client, repository):
    [channel] = [ch for ch in asyncio.run(repository.find_all()) if ch.name == "CCTV-1"]
    response = client.put(
        f"/api/channels/{channel.id}",
        json={
            "name": "CCTV-1 HD",
            "logo": "http://logo.com/cctv1.png",
            "tvg_id": "cctv1",
            "group": "央视频道",
        },
    )
    assert response.status_code == 200

    updated = response.json()
    assert updated["name"] == "CCTV-1 HD"
    assert updated["group"] == "央视频道"
    assert updated["manually_edited"] is True


def test_update_nonexistent_channel(client):
    response = client.put("/api/channels/nonexistent", json={"name": "New Name"})
    assert response.status_code == 404


def test_delete_channel(client, repository):
    [channel] = [ch for ch in asyncio.run(repository.find_all()) if ch.name == "CCTV-2"]
    response = client.delete(f"/api/channels/{channel.id}")
    assert response.status_code == 200
    assert response.json()["deleted"] is True

    response = client.get(f"/api/channels/{channel.id}")
    assert response.status_code == 404
