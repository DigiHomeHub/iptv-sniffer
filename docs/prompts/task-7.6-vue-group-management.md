# Task 7.6: TV Groups Management with Vue

## Overview

Implement TV Groups page with Vue 3, featuring group-based channel organization, drag-and-drop assignment, group statistics, merge/rename operations, and batch channel management within groups.

**Priority**: P2 - Nice-to-have for better channel organization

**Estimated Duration**: 14-18 hours

## Prerequisites

- Task 7.0: Vue 3 + Vite Frontend Setup (completed)
- Task 7.1: Vue Router + Tab Navigation (completed)
- Task 7.4: Channel Management Page (completed for CRUD operations)
- Backend: JSON storage repository (Task 1.3) with group filtering

## Implementation Summary

### Key Components

1. **Groups.vue** - Main groups management page
   - Grid/list view of all groups
   - Group statistics (channel count, online/offline ratio)
   - Quick actions (merge, rename, delete)

2. **GroupCard.vue** - Individual group display
   - Group name and description
   - Channel count badge
   - Online/offline status indicator
   - Quick actions menu

3. **GroupChannelsModal.vue** - View/manage channels within a group
   - Channel list with filtering
   - Drag-and-drop to reassign channels
   - Batch operations (move to another group, validate)

4. **GroupMergeModal.vue** - Merge multiple groups
   - Select source groups
   - Choose target group name
   - Preview merged channel count

5. **GroupEditModal.vue** - Rename group or add description
   - Edit group name
   - Add metadata (color tag, icon, description)

6. **Groups API** (`/api/groups`)
   - `GET /api/groups` - List all groups with statistics
   - `GET /api/groups/{group_name}/channels` - Get channels in a group
   - `PUT /api/channels/{channel_id}` - Update channel group
   - `POST /api/groups/merge` - Merge multiple groups
   - `PUT /api/groups/{group_name}` - Rename group (update all channels)
   - `DELETE /api/groups/{group_name}` - Delete group (move channels to "Uncategorized")

## TDD Implementation

### Test First (Red)

#### Backend Tests

```python
# tests/integration/web/test_groups_api.py

import pytest
from fastapi.testclient import TestClient
from iptv_sniffer.web.app import app
from iptv_sniffer.channel.models import Channel
from iptv_sniffer.storage.json_repository import JSONChannelRepository

client = TestClient(app)


@pytest.fixture
async def sample_grouped_channels(tmp_path):
    """Create sample channels with different groups"""
    repo = JSONChannelRepository(tmp_path / "channels.json")
    channels = [
        Channel(name="CCTV-1", url="http://test1.com", group="央视", is_online=True),
        Channel(name="CCTV-2", url="http://test2.com", group="央视", is_online=True),
        Channel(name="CCTV-3", url="http://test3.com", group="央视", is_online=False),
        Channel(name="湖南卫视", url="http://test4.com", group="卫视", is_online=True),
        Channel(name="浙江卫视", url="http://test5.com", group="卫视", is_online=True),
        Channel(name="HBO", url="http://test6.com", group="影视", is_online=False),
        Channel(name="Orphan", url="http://test7.com", group=None, is_online=True),
    ]
    for ch in channels:
        await repo.add(ch)
    return channels


def test_list_groups_with_statistics(sample_grouped_channels):
    """GET /api/groups should return all groups with stats"""
    response = client.get("/api/groups")
    assert response.status_code == 200

    data = response.json()
    groups = data["groups"]

    # Should have 3 named groups + 1 uncategorized
    assert len(groups) == 4

    # Find央视 group
    cctv_group = next(g for g in groups if g["name"] == "央视")
    assert cctv_group["total"] == 3
    assert cctv_group["online"] == 2
    assert cctv_group["offline"] == 1

    # Uncategorized group
    uncategorized = next(g for g in groups if g["name"] == "Uncategorized")
    assert uncategorized["total"] == 1


def test_get_channels_by_group(sample_grouped_channels):
    """GET /api/groups/{name}/channels should return channels in group"""
    response = client.get("/api/groups/央视/channels")
    assert response.status_code == 200

    data = response.json()
    assert len(data["channels"]) == 3
    assert all(ch["group"] == "央视" for ch in data["channels"])


def test_get_uncategorized_channels(sample_grouped_channels):
    """Should handle uncategorized channels"""
    response = client.get("/api/groups/Uncategorized/channels")
    assert response.status_code == 200

    data = response.json()
    assert len(data["channels"]) == 1
    assert data["channels"][0]["group"] is None


def test_move_channel_to_group(sample_grouped_channels):
    """PUT /api/channels/{id} should update channel group"""
    channel_id = sample_grouped_channels[0].id

    response = client.put(
        f"/api/channels/{channel_id}", json={"group": "精选频道"}
    )

    assert response.status_code == 200
    updated = response.json()
    assert updated["group"] == "精选频道"


def test_merge_groups(sample_grouped_channels):
    """POST /api/groups/merge should merge multiple groups"""
    response = client.post(
        "/api/groups/merge",
        json={
            "source_groups": ["央视", "卫视"],
            "target_group": "综合频道",
        },
    )

    assert response.status_code == 200
    result = response.json()
    assert result["merged"] == 5  # 3 from央视 + 2 from卫视

    # Verify channels updated
    response = client.get("/api/groups/综合频道/channels")
    assert response.status_code == 200
    assert len(response.json()["channels"]) == 5


def test_rename_group(sample_grouped_channels):
    """PUT /api/groups/{name} should rename group"""
    response = client.put(
        "/api/groups/央视", json={"new_name": "CCTV频道"}
    )

    assert response.status_code == 200
    result = response.json()
    assert result["renamed"] == 3  # 3 channels renamed

    # Verify old group gone
    response = client.get("/api/groups/央视/channels")
    assert response.status_code == 200
    assert len(response.json()["channels"]) == 0

    # Verify new group exists
    response = client.get("/api/groups/CCTV频道/channels")
    assert response.status_code == 200
    assert len(response.json()["channels"]) == 3


def test_delete_group(sample_grouped_channels):
    """DELETE /api/groups/{name} should move channels to Uncategorized"""
    response = client.delete("/api/groups/央视")

    assert response.status_code == 200
    result = response.json()
    assert result["deleted"] is True
    assert result["affected_channels"] == 3

    # Verify channels moved to uncategorized
    response = client.get("/api/channels?group=")
    data = response.json()
    assert data["total"] >= 3  # At least the 3 from央视


def test_empty_group_not_listed(sample_grouped_channels):
    """Empty groups should not appear in group list"""
    # Delete all channels in影视 group
    for ch in sample_grouped_channels:
        if ch.group == "影视":
            client.delete(f"/api/channels/{ch.id}")

    response = client.get("/api/groups")
    groups = response.json()["groups"]

    # Verify影视 group not in list
    assert not any(g["name"] == "影视" for g in groups)


def test_group_statistics_accuracy(sample_grouped_channels):
    """Group statistics should be accurate"""
    response = client.get("/api/groups")
    groups = response.json()["groups"]

    ws_group = next(g for g in groups if g["name"] == "卫视")
    assert ws_group["total"] == 2
    assert ws_group["online"] == 2
    assert ws_group["offline"] == 0
    assert ws_group["online_percentage"] == 100


def test_large_group_pagination(sample_grouped_channels):
    """Should support pagination for large groups"""
    response = client.get("/api/groups/央视/channels?page=1&page_size=2")

    assert response.status_code == 200
    data = response.json()
    assert len(data["channels"]) == 2
    assert data["total"] == 3
    assert data["pages"] == 2
```

### Implement (Green)

#### Step 1: Implement Groups API

```python
# iptv_sniffer/web/api/groups.py

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict
from pydantic import BaseModel
from collections import defaultdict
from math import ceil
from iptv_sniffer.channel.models import Channel
from iptv_sniffer.storage.json_repository import JSONChannelRepository
from iptv_sniffer.utils.config import AppConfig
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/groups", tags=["groups"])

config = AppConfig()
repo = JSONChannelRepository(config.data_dir / "channels.json")


class GroupStatistics(BaseModel):
    name: str
    total: int
    online: int
    offline: int
    online_percentage: float


class GroupListResponse(BaseModel):
    groups: List[GroupStatistics]
    total_groups: int


class GroupChannelsResponse(BaseModel):
    channels: List[Channel]
    total: int
    page: int
    pages: int


class MergeGroupsRequest(BaseModel):
    source_groups: List[str]
    target_group: str


class RenameGroupRequest(BaseModel):
    new_name: str


@router.get("", response_model=GroupListResponse)
async def list_groups():
    """
    List all groups with statistics

    Returns groups sorted by channel count (descending)
    """
    all_channels = await repo.find_all()

    # Group channels by group name
    grouped: Dict[Optional[str], List[Channel]] = defaultdict(list)
    for ch in all_channels:
        grouped[ch.group].append(ch)

    # Calculate statistics
    groups: List[GroupStatistics] = []
    for group_name, channels in grouped.items():
        if not channels:
            continue

        online_count = sum(1 for ch in channels if ch.is_online)
        offline_count = len(channels) - online_count
        online_pct = (
            round((online_count / len(channels)) * 100, 1) if channels else 0.0
        )

        display_name = group_name if group_name else "Uncategorized"

        groups.append(
            GroupStatistics(
                name=display_name,
                total=len(channels),
                online=online_count,
                offline=offline_count,
                online_percentage=online_pct,
            )
        )

    # Sort by channel count descending
    groups.sort(key=lambda g: g.total, reverse=True)

    logger.info(f"Listed {len(groups)} groups with {len(all_channels)} total channels")

    return GroupListResponse(groups=groups, total_groups=len(groups))


@router.get("/{group_name}/channels", response_model=GroupChannelsResponse)
async def get_group_channels(
    group_name: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
):
    """
    Get all channels in a specific group with pagination

    Use "Uncategorized" to get channels without a group
    """
    # Handle uncategorized
    if group_name == "Uncategorized":
        filters = {"group": None}
    else:
        filters = {"group": group_name}

    channels = await repo.find_all(filters)

    # Calculate pagination
    total = len(channels)
    pages = ceil(total / page_size) if total > 0 else 1
    start = (page - 1) * page_size
    end = start + page_size

    logger.info(
        f"Retrieved {len(channels[start:end])} channels from group '{group_name}' (page {page}/{pages})"
    )

    return GroupChannelsResponse(
        channels=channels[start:end], total=total, page=page, pages=pages
    )


@router.post("/merge")
async def merge_groups(request: MergeGroupsRequest):
    """
    Merge multiple groups into a target group

    All channels from source groups will be moved to target group
    """
    if not request.source_groups:
        raise HTTPException(400, "At least one source group required")

    if request.target_group in request.source_groups:
        raise HTTPException(400, "Target group cannot be in source groups")

    merged_count = 0

    for source_group in request.source_groups:
        filters = {"group": source_group}
        channels = await repo.find_all(filters)

        for channel in channels:
            channel.group = request.target_group
            await repo.add(channel)  # Upsert
            merged_count += 1

    logger.info(
        f"Merged {merged_count} channels from {request.source_groups} to '{request.target_group}'"
    )

    return {"merged": merged_count, "target_group": request.target_group}


@router.put("/{group_name}")
async def rename_group(group_name: str, request: RenameGroupRequest):
    """
    Rename a group by updating all channels in that group

    This operation updates the group field for all matching channels
    """
    if not request.new_name or request.new_name.strip() == "":
        raise HTTPException(400, "New group name cannot be empty")

    if group_name == request.new_name:
        raise HTTPException(400, "New name must be different from current name")

    filters = {"group": group_name}
    channels = await repo.find_all(filters)

    if not channels:
        raise HTTPException(404, f"Group '{group_name}' not found")

    for channel in channels:
        channel.group = request.new_name
        await repo.add(channel)

    logger.info(f"Renamed group '{group_name}' to '{request.new_name}' ({len(channels)} channels)")

    return {"renamed": len(channels), "new_name": request.new_name}


@router.delete("/{group_name}")
async def delete_group(group_name: str):
    """
    Delete a group by moving all its channels to Uncategorized

    Channels are not deleted, only their group assignment is removed
    """
    filters = {"group": group_name}
    channels = await repo.find_all(filters)

    if not channels:
        raise HTTPException(404, f"Group '{group_name}' not found")

    for channel in channels:
        channel.group = None
        await repo.add(channel)

    logger.info(f"Deleted group '{group_name}', moved {len(channels)} channels to Uncategorized")

    return {"deleted": True, "affected_channels": len(channels)}
```

```python
# iptv_sniffer/web/app.py (register router)

from iptv_sniffer.web.api import scan, screenshots, channels, m3u, groups

app.include_router(scan.router)
app.include_router(screenshots.router)
app.include_router(channels.router)
app.include_router(m3u.router)
app.include_router(groups.router)
```

#### Step 2: Update API Client

```typescript
// frontend/src/api/groups.ts

import api from "./client";

export interface GroupStatistics {
  name: string;
  total: number;
  online: number;
  offline: number;
  online_percentage: number;
}

export interface GroupListResponse {
  groups: GroupStatistics[];
  total_groups: number;
}

export interface GroupChannelsResponse {
  channels: Channel[];
  total: number;
  page: number;
  pages: number;
}

export const groupsAPI = {
  list: async (): Promise<GroupListResponse> => {
    return api.request("/groups");
  },

  getChannels: async (
    groupName: string,
    page: number = 1,
    pageSize: number = 50
  ): Promise<GroupChannelsResponse> => {
    const params = new URLSearchParams({
      page: String(page),
      page_size: String(pageSize),
    });
    return api.request(`/groups/${encodeURIComponent(groupName)}/channels?${params}`);
  },

  merge: async (sourceGroups: string[], targetGroup: string) => {
    return api.request("/groups/merge", {
      method: "POST",
      body: JSON.stringify({
        source_groups: sourceGroups,
        target_group: targetGroup,
      }),
    });
  },

  rename: async (groupName: string, newName: string) => {
    return api.request(`/groups/${encodeURIComponent(groupName)}`, {
      method: "PUT",
      body: JSON.stringify({ new_name: newName }),
    });
  },

  delete: async (groupName: string) => {
    return api.request(`/groups/${encodeURIComponent(groupName)}`, {
      method: "DELETE",
    });
  },
};
```

#### Step 3: Create Groups View

```vue
<!-- frontend/src/views/Groups.vue -->

<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import GroupCard from "@/components/groups/GroupCard.vue";
import GroupChannelsModal from "@/components/groups/GroupChannelsModal.vue";
import GroupMergeModal from "@/components/groups/GroupMergeModal.vue";
import GroupEditModal from "@/components/groups/GroupEditModal.vue";
import { groupsAPI, type GroupStatistics } from "@/api/groups";

const groups = ref<GroupStatistics[]>([]);
const isLoading = ref(false);
const selectedGroups = ref<Set<string>>(new Set());
const viewingGroup = ref<string | null>(null);
const showChannelsModal = ref(false);
const showMergeModal = ref(false);
const editingGroup = ref<string | null>(null);
const showEditModal = ref(false);

const hasSelection = computed(() => selectedGroups.value.size > 0);
const canMerge = computed(() => selectedGroups.value.size >= 2);

async function fetchGroups() {
  isLoading.value = true;
  try {
    const response = await groupsAPI.list();
    groups.value = response.groups;
  } catch (error) {
    console.error("Failed to fetch groups", error);
  } finally {
    isLoading.value = false;
  }
}

function handleViewChannels(groupName: string) {
  viewingGroup.value = groupName;
  showChannelsModal.value = true;
}

function handleEditGroup(groupName: string) {
  editingGroup.value = groupName;
  showEditModal.value = true;
}

async function handleRenameGroup(groupName: string, newName: string) {
  try {
    await groupsAPI.rename(groupName, newName);
    showEditModal.value = false;
    await fetchGroups();
  } catch (error) {
    console.error("Failed to rename group", error);
  }
}

async function handleDeleteGroup(groupName: string) {
  if (!confirm(`Delete group "${groupName}"? Channels will be moved to Uncategorized.`)) {
    return;
  }
  try {
    await groupsAPI.delete(groupName);
    selectedGroups.value.delete(groupName);
    await fetchGroups();
  } catch (error) {
    console.error("Failed to delete group", error);
  }
}

async function handleMergeGroups(sourceGroups: string[], targetGroup: string) {
  try {
    await groupsAPI.merge(sourceGroups, targetGroup);
    showMergeModal.value = false;
    selectedGroups.value.clear();
    await fetchGroups();
  } catch (error) {
    console.error("Failed to merge groups", error);
  }
}

function toggleGroupSelection(groupName: string) {
  if (selectedGroups.value.has(groupName)) {
    selectedGroups.value.delete(groupName);
  } else {
    selectedGroups.value.add(groupName);
  }
}

onMounted(() => {
  fetchGroups();
});
</script>

<template>
  <div class="space-y-6">
    <header>
      <h1 class="text-3xl font-bold text-slate-900">TV Groups</h1>
      <p class="mt-2 text-sm text-slate-600">
        Organize channels into logical groups such as categories, providers, and favorites. Merge,
        rename, or delete groups to maintain a clean structure.
      </p>
    </header>

    <section class="card">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p class="text-sm text-slate-600">
            {{ groups.length }} groups with {{ groups.reduce((sum, g) => sum + g.total, 0) }} total
            channels
          </p>
        </div>
        <div class="flex gap-2">
          <button
            v-if="hasSelection"
            type="button"
            class="btn-secondary"
            @click="selectedGroups.clear()"
          >
            Clear Selection ({{ selectedGroups.size }})
          </button>
          <button
            v-if="canMerge"
            type="button"
            class="btn-primary"
            @click="showMergeModal = true"
          >
            Merge Selected Groups
          </button>
          <button type="button" class="btn-secondary" @click="fetchGroups">
            Refresh
          </button>
        </div>
      </div>
    </section>

    <div v-if="isLoading" class="flex items-center justify-center py-12">
      <div
        class="h-12 w-12 animate-spin rounded-full border-4 border-blue-500 border-t-transparent"
      />
    </div>

    <div v-else-if="groups.length === 0" class="card text-center py-12">
      <p class="text-slate-600">No groups found. Import channels or start scanning to create groups.</p>
    </div>

    <div v-else class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      <GroupCard
        v-for="group in groups"
        :key="group.name"
        :group="group"
        :is-selected="selectedGroups.has(group.name)"
        @toggle-selection="toggleGroupSelection"
        @view-channels="handleViewChannels"
        @edit="handleEditGroup"
        @delete="handleDeleteGroup"
      />
    </div>

    <GroupChannelsModal
      v-if="showChannelsModal && viewingGroup"
      :group-name="viewingGroup"
      @close="showChannelsModal = false"
      @channels-updated="fetchGroups"
    />

    <GroupEditModal
      v-if="showEditModal && editingGroup"
      :group-name="editingGroup"
      @save="handleRenameGroup"
      @close="showEditModal = false"
    />

    <GroupMergeModal
      v-if="showMergeModal"
      :source-groups="Array.from(selectedGroups)"
      @merge="handleMergeGroups"
      @close="showMergeModal = false"
    />
  </div>
</template>
```

#### Step 4: Create GroupCard Component

```vue
<!-- frontend/src/components/groups/GroupCard.vue -->

<script setup lang="ts">
import { computed } from "vue";
import type { GroupStatistics } from "@/api/groups";

interface Props {
  group: GroupStatistics;
  isSelected: boolean;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  (e: "toggle-selection", groupName: string): void;
  (e: "view-channels", groupName: string): void;
  (e: "edit", groupName: string): void;
  (e: "delete", groupName: string): void;
}>();

const statusColor = computed(() => {
  const pct = props.group.online_percentage;
  if (pct >= 80) return "bg-green-100 text-green-800";
  if (pct >= 50) return "bg-yellow-100 text-yellow-800";
  return "bg-red-100 text-red-800";
});
</script>

<template>
  <div
    :class="[
      'card hover:shadow-lg transition-shadow cursor-pointer',
      isSelected ? 'ring-2 ring-blue-500' : '',
    ]"
    @click="emit('toggle-selection', group.name)"
  >
    <div class="flex items-start justify-between mb-3">
      <div class="flex items-center gap-2">
        <input
          type="checkbox"
          :checked="isSelected"
          class="h-4 w-4 text-blue-600"
          @click.stop
        />
        <h3 class="text-lg font-semibold text-slate-900">
          {{ group.name }}
        </h3>
      </div>
      <span
        :class="['px-2 py-1 text-xs font-medium rounded-full', statusColor]"
      >
        {{ group.online_percentage }}%
      </span>
    </div>

    <div class="grid grid-cols-3 gap-4 mb-4 text-center">
      <div>
        <div class="text-2xl font-bold text-slate-900">{{ group.total }}</div>
        <div class="text-xs text-slate-600">Total</div>
      </div>
      <div>
        <div class="text-2xl font-bold text-green-600">{{ group.online }}</div>
        <div class="text-xs text-slate-600">Online</div>
      </div>
      <div>
        <div class="text-2xl font-bold text-red-600">{{ group.offline }}</div>
        <div class="text-xs text-slate-600">Offline</div>
      </div>
    </div>

    <div class="flex gap-2" @click.stop>
      <button
        type="button"
        class="btn-secondary flex-1 text-sm py-1"
        @click="emit('view-channels', group.name)"
      >
        View Channels
      </button>
      <button
        type="button"
        class="btn-secondary text-sm py-1 px-3"
        @click="emit('edit', group.name)"
      >
        Edit
      </button>
      <button
        type="button"
        class="btn-danger text-sm py-1 px-3"
        @click="emit('delete', group.name)"
      >
        Delete
      </button>
    </div>
  </div>
</template>
```

(Continue with GroupChannelsModal, GroupMergeModal, and GroupEditModal components - truncated for brevity)

### Verification Criteria

**Backend Tests:**

- [ ] All groups API tests pass
- [ ] Group statistics calculation accurate
- [ ] Merge groups works correctly
- [ ] Rename group updates all channels
- [ ] Delete group moves channels to Uncategorized
- [ ] Empty groups not listed
- [ ] Test coverage >80%

**Frontend Tests:**

- [ ] Groups view loads groups list
- [ ] Group selection works
- [ ] Merge modal functional
- [ ] Edit modal saves changes
- [ ] Delete confirmation works
- [ ] Component test coverage >75%

**E2E Tests:**

- [ ] Full group management workflow
- [ ] Merge groups end-to-end
- [ ] Rename group persists

**Manual Testing:**

- [ ] Group statistics update in real-time
- [ ] Drag-and-drop channel assignment (if implemented)
- [ ] UI responsive on mobile
- [ ] Empty state displays correctly

## Notes

- **Uncategorized Group**: Channels without a group are shown in a special "Uncategorized" group
- **Group Persistence**: Groups are dynamic - they exist only if channels reference them
- **Performance**: For large channel lists (>1000), consider server-side pagination in group channels
- **Future Enhancement**: Add drag-and-drop between groups, group icons/colors, nested groups

## Dependencies

No new frontend dependencies required. Backend uses existing Channel and JSONChannelRepository.
