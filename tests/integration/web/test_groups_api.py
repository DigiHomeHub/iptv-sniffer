import asyncio
from pathlib import Path
from typing import List, Tuple

import pytest
from fastapi.testclient import TestClient

from iptv_sniffer.channel.models import Channel
from iptv_sniffer.storage.json_repository import JSONChannelRepository
from iptv_sniffer.web.api.channels import get_repository
from iptv_sniffer.web.app import app


@pytest.fixture()
def seeded_repository(tmp_path: Path) -> Tuple[JSONChannelRepository, List[Channel]]:
    repo = JSONChannelRepository(tmp_path / "channels.json")
    channels: List[Channel] = [
        Channel(name="CCTV-1", url="http://test1.com", group="央视", is_online=True),
        Channel(name="CCTV-2", url="http://test2.com", group="央视", is_online=True),
        Channel(name="CCTV-3", url="http://test3.com", group="央视", is_online=False),
        Channel(name="湖南卫视", url="http://test4.com", group="卫视", is_online=True),
        Channel(name="浙江卫视", url="http://test5.com", group="卫视", is_online=True),
        Channel(name="HBO", url="http://test6.com", group="影视", is_online=False),
        Channel(name="Orphan", url="http://test7.com", group=None, is_online=True),
    ]

    async def seed() -> None:
        for channel in channels:
            await repo.add(channel)

    asyncio.run(seed())
    return repo, channels


@pytest.fixture()
def client(seeded_repository):
    repo, _ = seeded_repository
    app.dependency_overrides[get_repository] = lambda: repo
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_repository, None)


def test_list_groups_with_statistics(client: TestClient) -> None:
    response = client.get("/api/groups")
    assert response.status_code == 200
    payload = response.json()

    groups = payload["groups"]
    assert payload["total_groups"] == len(groups) == 4

    cctv_group = next(group for group in groups if group["name"] == "央视")
    assert cctv_group == {
        "name": "央视",
        "total": 3,
        "online": 2,
        "offline": 1,
        "online_percentage": 66.7,
    }

    uncategorized = next(group for group in groups if group["name"] == "Uncategorized")
    assert uncategorized["total"] == 1
    assert uncategorized["online"] == 1


def test_get_channels_by_group(client: TestClient) -> None:
    response = client.get("/api/groups/央视/channels")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["channels"]) == 3
    assert all(channel["group"] == "央视" for channel in data["channels"])


def test_get_uncategorized_channels(client: TestClient) -> None:
    response = client.get("/api/groups/Uncategorized/channels")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["channels"][0]["group"] is None


def test_group_channels_pagination(client: TestClient) -> None:
    response = client.get("/api/groups/央视/channels?page=1&page_size=2")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["channels"]) == 2
    assert data["page"] == 1
    assert data["pages"] == 2


def test_move_channel_via_update(client: TestClient, seeded_repository) -> None:
    repo, original_channels = seeded_repository
    channel_id = original_channels[0].id

    response = client.put(f"/api/channels/{channel_id}", json={"group": "精选频道"})
    assert response.status_code == 200
    updated = response.json()
    assert updated["group"] == "精选频道"

    # Verify repository reflects update
    refreshed = asyncio.run(repo.get_by_id(channel_id))
    assert refreshed is not None and refreshed.group == "精选频道"


def test_merge_groups(client: TestClient) -> None:
    response = client.post(
        "/api/groups/merge",
        json={"source_groups": ["央视", "卫视"], "target_group": "综合频道"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body == {"merged": 5, "target_group": "综合频道"}

    merged_response = client.get("/api/groups/综合频道/channels")
    assert merged_response.status_code == 200
    assert merged_response.json()["total"] == 5


def test_merge_from_uncategorized(client: TestClient) -> None:
    response = client.post(
        "/api/groups/merge",
        json={"source_groups": ["Uncategorized"], "target_group": "新分类"},
    )
    assert response.status_code == 200
    assert response.json()["merged"] == 1


def test_rename_group(client: TestClient) -> None:
    response = client.put("/api/groups/央视", json={"new_name": "CCTV频道"})
    assert response.status_code == 200
    assert response.json() == {"renamed": 3, "new_name": "CCTV频道"}

    verify = client.get("/api/groups/CCTV频道/channels")
    assert verify.status_code == 200
    assert verify.json()["total"] == 3


def test_delete_group_moves_to_uncategorized(client: TestClient) -> None:
    response = client.delete("/api/groups/央视")
    assert response.status_code == 200
    body = response.json()
    assert body["deleted"] is True
    assert body["affected_channels"] == 3

    uncategorized = client.get("/api/groups/Uncategorized/channels").json()
    assert uncategorized["total"] >= 4  # previous orphan + moved entries


def test_delete_uncategorized_prohibited(client: TestClient) -> None:
    response = client.delete("/api/groups/Uncategorized")
    assert response.status_code == 400


def test_rename_missing_group_returns_not_found(client: TestClient) -> None:
    response = client.put("/api/groups/不存在", json={"new_name": "不会出现"})
    assert response.status_code == 404
