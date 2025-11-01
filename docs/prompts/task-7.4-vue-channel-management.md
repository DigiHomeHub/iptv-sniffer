# Task 7.4: Channel Management Page with Vue

## Overview

Implement TV Channels page with Vue 3, featuring filterable channel list, inline editing, batch operations, and pagination. Backend provides RESTful Channel API with comprehensive CRUD operations.

**Priority**: P1 - Required for channel browsing and management

**Estimated Duration**: 16-20 hours

## Prerequisites

- Task 7.0: Vue 3 + Vite Frontend Setup (completed)
- Task 7.1: Vue Router + Tab Navigation (completed)
- Task 7.3: Screenshot Display with Vue (completed for reusing ChannelCard)
- Backend: JSON storage repository (Task 1.3) completed

## Implementation Summary

### Key Components

1. **TVChannels.vue** - Main channel management page
   - Search bar and filter controls
   - Channel table/grid view toggle
   - Pagination controls

2. **ChannelTable.vue** - Data table with sorting
   - Virtual scrolling for large datasets (>1000 channels)
   - Multi-select for batch operations
   - Inline editing for name, group, logo

3. **ChannelEditModal.vue** - Full channel metadata editor
   - Edit all channel fields
   - Preview screenshot
   - Validation with Vuelidate

4. **BatchActionBar.vue** - Batch operation toolbar
   - Delete selected channels
   - Validate selected channels (trigger scan)
   - Export selected to M3U

5. **Channel API** (`/api/channels`)
   - `GET /api/channels` - List with pagination and filters
   - `GET /api/channels/{id}` - Get single channel
   - `PUT /api/channels/{id}` - Update channel
   - `DELETE /api/channels/{id}` - Delete channel

## TDD Implementation

### Test First (Red)

#### Backend Tests

```python
# tests/integration/web/test_channels_api.py

import pytest
import asyncio
from fastapi.testclient import TestClient
from iptv_sniffer.web.app import app
from iptv_sniffer.channel.models import Channel
from iptv_sniffer.storage.json_repository import JSONChannelRepository

client = TestClient(app)

@pytest.fixture
async def sample_channels(tmp_path):
    """Create sample channels for testing"""
    repo = JSONChannelRepository(tmp_path / "channels.json")
    channels = [
        Channel(name="CCTV-1", url="http://test1.com", group="央视", resolution="1080p"),
        Channel(name="CCTV-2", url="http://test2.com", group="央视", resolution="720p"),
        Channel(name="Phoenix TV", url="http://test3.com", group="凤凰", is_online=True),
        Channel(name="HBO", url="http://test4.com", group="影视", resolution="4K", is_online=True)
    ]
    for ch in channels:
        await repo.add(ch)
    return channels

def test_list_channels_with_pagination(sample_channels):
    """GET /api/channels should support pagination"""
    response = client.get("/api/channels?page=1&page_size=2")
    assert response.status_code == 200

    data = response.json()
    assert data["total"] == 4
    assert len(data["channels"]) == 2
    assert data["page"] == 1
    assert data["pages"] == 2

def test_filter_channels_by_group(sample_channels):
    """Should filter channels by group"""
    response = client.get("/api/channels?group=央视")
    assert response.status_code == 200

    data = response.json()
    assert data["total"] == 2
    assert all(ch["group"] == "央视" for ch in data["channels"])

def test_filter_channels_by_resolution(sample_channels):
    """Should filter channels by resolution"""
    response = client.get("/api/channels?resolution=1080p")
    data = response.json()
    assert data["total"] == 1
    assert data["channels"][0]["resolution"] == "1080p"

def test_filter_channels_by_status(sample_channels):
    """Should filter channels by online status"""
    response = client.get("/api/channels?status=online")
    data = response.json()
    assert data["total"] == 2
    assert all(ch["is_online"] for ch in data["channels"])

def test_search_channels_by_name(sample_channels):
    """Should search channels by name"""
    response = client.get("/api/channels?search=CCTV")
    data = response.json()
    assert data["total"] == 2
    assert all("CCTV" in ch["name"] for ch in data["channels"])

def test_update_channel_info(sample_channels):
    """PUT /api/channels/{id} should update channel"""
    channel_id = sample_channels[0].id

    response = client.put(f"/api/channels/{channel_id}", json={
        "name": "CCTV-1 HD",
        "logo": "http://logo.com/cctv1.png",
        "tvg_id": "cctv1",
        "group": "央视频道"
    })

    assert response.status_code == 200
    updated = response.json()
    assert updated["name"] == "CCTV-1 HD"
    assert updated["group"] == "央视频道"
    assert updated["manually_edited"] is True

def test_update_nonexistent_channel(sample_channels):
    """Should return 404 for non-existent channel"""
    response = client.put("/api/channels/nonexistent-id", json={"name": "New Name"})
    assert response.status_code == 404

def test_delete_channel(sample_channels):
    """DELETE /api/channels/{id} should remove channel"""
    channel_id = sample_channels[0].id

    response = client.delete(f"/api/channels/{channel_id}")
    assert response.status_code == 200
    assert response.json()["deleted"] is True

    # Verify deletion
    response = client.get(f"/api/channels/{channel_id}")
    assert response.status_code == 404

def test_get_channel_by_id(sample_channels):
    """GET /api/channels/{id} should return channel details"""
    channel_id = sample_channels[0].id

    response = client.get(f"/api/channels/{channel_id}")
    assert response.status_code == 200

    channel = response.json()
    assert channel["id"] == channel_id
    assert channel["name"] == "CCTV-1"
```

### Implement (Green)

#### Step 1: Implement Channel API

```python
# iptv_sniffer/web/api/channels.py

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, List
from pydantic import BaseModel
from math import ceil
from datetime import datetime
from iptv_sniffer.channel.models import Channel
from iptv_sniffer.storage.json_repository import JSONChannelRepository
from iptv_sniffer.utils.config import AppConfig
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/channels", tags=["channels"])

# Initialize repository
config = AppConfig()
repo = JSONChannelRepository(config.data_dir / "channels.json")


class ChannelListResponse(BaseModel):
    channels: List[Channel]
    total: int
    page: int
    pages: int


class ChannelUpdateRequest(BaseModel):
    name: Optional[str] = None
    logo: Optional[str] = None
    tvg_id: Optional[str] = None
    tvg_logo: Optional[str] = None
    group: Optional[str] = None


@router.get("", response_model=ChannelListResponse)
async def list_channels(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
    group: Optional[str] = Query(None, description="Filter by group"),
    resolution: Optional[str] = Query(None, description="Filter by resolution"),
    status: Optional[str] = Query(None, description="Filter by status: online/offline"),
    search: Optional[str] = Query(None, description="Search in name and URL")
):
    """
    List channels with pagination and filters

    Returns paginated channel list with total count and page info
    """
    # Build repository filters
    filters = {}
    if group:
        filters["group"] = group
    if status == "online":
        filters["is_online"] = True
    elif status == "offline":
        filters["is_online"] = False

    # Get all matching channels
    all_channels = await repo.find_all(filters)

    # Apply resolution filter (not in repository yet)
    if resolution:
        all_channels = [ch for ch in all_channels if ch.resolution == resolution]

    # Apply search filter
    if search:
        search_lower = search.lower()
        all_channels = [
            ch for ch in all_channels
            if search_lower in ch.name.lower() or search_lower in ch.url.lower()
        ]

    # Calculate pagination
    total = len(all_channels)
    pages = ceil(total / page_size) if total > 0 else 1
    start = (page - 1) * page_size
    end = start + page_size

    logger.info(f"Listed {len(all_channels[start:end])} channels (page {page}/{pages}, total: {total})")

    return ChannelListResponse(
        channels=all_channels[start:end],
        total=total,
        page=page,
        pages=pages
    )


@router.get("/{channel_id}", response_model=Channel)
async def get_channel(channel_id: str):
    """Get single channel by ID"""
    channel = await repo.get_by_id(channel_id)
    if not channel:
        raise HTTPException(404, "Channel not found")
    return channel


@router.put("/{channel_id}", response_model=Channel)
async def update_channel(channel_id: str, update: ChannelUpdateRequest):
    """
    Update channel information

    Sets manually_edited flag to track user modifications
    """
    channel = await repo.get_by_id(channel_id)
    if not channel:
        raise HTTPException(404, "Channel not found")

    # Apply updates
    update_data = update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(channel, field, value)

    # Mark as manually edited
    channel.manually_edited = True
    channel.updated_at = datetime.utcnow()

    # Save changes
    updated = await repo.add(channel)  # add() handles upsert

    logger.info(f"Updated channel {channel_id}: {update_data}")

    return updated


@router.delete("/{channel_id}")
async def delete_channel(channel_id: str):
    """Delete channel"""
    deleted = await repo.delete(channel_id)
    if not deleted:
        raise HTTPException(404, "Channel not found")

    logger.info(f"Deleted channel {channel_id}")

    return {"deleted": True}
```

```python
# iptv_sniffer/web/app.py (register router)

from iptv_sniffer.web.api import scan, screenshots, channels

app.include_router(scan.router)
app.include_router(screenshots.router)
app.include_router(channels.router)
```

#### Step 2: Update API Client

```typescript
// frontend/src/api/client.ts (add channels methods)

const API = {
  // ... existing code

  channels: {
    list: (params: {
      page?: number
      page_size?: number
      group?: string
      resolution?: string
      status?: string
      search?: string
    }) => {
      const queryString = new URLSearchParams(
        Object.entries(params).reduce((acc, [key, value]) => {
          if (value !== undefined && value !== null) {
            acc[key] = String(value)
          }
          return acc
        }, {} as Record<string, string>)
      ).toString()

      return API.request(`/channels?${queryString}`)
    },

    get: (id: string) => API.request(`/channels/${id}`),

    update: (id: string, data: Partial<Channel>) =>
      API.request(`/channels/${id}`, {
        method: 'PUT',
        body: JSON.stringify(data)
      }),

    delete: (id: string) =>
      API.request(`/channels/${id}`, { method: 'DELETE' })
  }
}

export default API
```

#### Step 3: Create TVChannels View

```vue
<!-- frontend/src/views/TVChannels.vue -->

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import ChannelTable from '@/components/channels/ChannelTable.vue'
import ChannelEditModal from '@/components/channels/ChannelEditModal.vue'
import BatchActionBar from '@/components/channels/BatchActionBar.vue'
import api from '@/api/client'
import type { Channel } from '@/types/channel'

interface ChannelListResponse {
  channels: Channel[]
  total: number
  page: number
  pages: number
}

const channels = ref<Channel[]>([])
const total = ref(0)
const currentPage = ref(1)
const totalPages = ref(1)
const isLoading = ref(false)

const filters = ref({
  group: '',
  resolution: '',
  status: '',
  search: ''
})

const selectedChannels = ref<Set<string>>(new Set())
const editingChannel = ref<Channel | null>(null)
const showEditModal = ref(false)

const fetchChannels = async () => {
  isLoading.value = true
  try {
    const response: ChannelListResponse = await api.channels.list({
      page: currentPage.value,
      page_size: 50,
      ...filters.value
    })

    channels.value = response.channels
    total.value = response.total
    currentPage.value = response.page
    totalPages.value = response.pages
  } catch (error) {
    console.error('Failed to fetch channels:', error)
  } finally {
    isLoading.value = false
  }
}

const handlePageChange = (page: number) => {
  currentPage.value = page
  fetchChannels()
}

const handleFilterChange = () => {
  currentPage.value = 1
  fetchChannels()
}

const handleEdit = (channel: Channel) => {
  editingChannel.value = { ...channel }
  showEditModal.value = true
}

const handleSaveChannel = async (updatedChannel: Channel) => {
  try {
    await api.channels.update(updatedChannel.id, updatedChannel)
    showEditModal.value = false
    fetchChannels()
  } catch (error) {
    console.error('Failed to update channel:', error)
  }
}

const handleDeleteChannel = async (channelId: string) => {
  if (!confirm('Are you sure you want to delete this channel?')) return

  try {
    await api.channels.delete(channelId)
    fetchChannels()
  } catch (error) {
    console.error('Failed to delete channel:', error)
  }
}

const handleBatchDelete = async () => {
  if (selectedChannels.value.size === 0) return
  if (!confirm(`Delete ${selectedChannels.value.size} channels?`)) return

  try {
    await Promise.all(
      Array.from(selectedChannels.value).map(id => api.channels.delete(id))
    )
    selectedChannels.value.clear()
    fetchChannels()
  } catch (error) {
    console.error('Failed to delete channels:', error)
  }
}

onMounted(() => {
  fetchChannels()
})
</script>

<template>
  <div class="tv-channels-container">
    <h1 class="text-3xl font-bold mb-6">TV Channels</h1>

    <!-- Filter Bar -->
    <div class="card mb-6">
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <input
          v-model="filters.search"
          @input="handleFilterChange"
          type="text"
          placeholder="Search channels..."
          class="input-field"
        />

        <select v-model="filters.group" @change="handleFilterChange" class="input-field">
          <option value="">All Groups</option>
          <option value="央视">央视</option>
          <option value="卫视">卫视</option>
          <option value="影视">影视</option>
        </select>

        <select v-model="filters.resolution" @change="handleFilterChange" class="input-field">
          <option value="">All Resolutions</option>
          <option value="4K">4K</option>
          <option value="1080p">1080p</option>
          <option value="720p">720p</option>
        </select>

        <select v-model="filters.status" @change="handleFilterChange" class="input-field">
          <option value="">All Status</option>
          <option value="online">Online</option>
          <option value="offline">Offline</option>
        </select>
      </div>
    </div>

    <!-- Batch Action Bar -->
    <BatchActionBar
      v-if="selectedChannels.size > 0"
      :selected-count="selectedChannels.size"
      @delete="handleBatchDelete"
    />

    <!-- Channel Table -->
    <ChannelTable
      :channels="channels"
      :is-loading="isLoading"
      :selected="selectedChannels"
      @edit="handleEdit"
      @delete="handleDeleteChannel"
      @selection-change="(selected) => { selectedChannels = selected }"
    />

    <!-- Pagination -->
    <div class="flex justify-center mt-6">
      <nav class="flex gap-2">
        <button
          @click="handlePageChange(currentPage - 1)"
          :disabled="currentPage === 1"
          class="btn btn-secondary"
        >
          Previous
        </button>

        <span class="px-4 py-2">
          Page {{ currentPage }} of {{ totalPages }} ({{ total }} total)
        </span>

        <button
          @click="handlePageChange(currentPage + 1)"
          :disabled="currentPage === totalPages"
          class="btn btn-secondary"
        >
          Next
        </button>
      </nav>
    </div>

    <!-- Edit Modal -->
    <ChannelEditModal
      v-if="showEditModal && editingChannel"
      :channel="editingChannel"
      @save="handleSaveChannel"
      @close="showEditModal = false"
    />
  </div>
</template>
```

#### Step 4: Create ChannelTable Component

```vue
<!-- frontend/src/components/channels/ChannelTable.vue -->

<script setup lang="ts">
import { computed } from 'vue'
import type { Channel } from '@/types/channel'

interface Props {
  channels: Channel[]
  isLoading: boolean
  selected: Set<string>
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'edit', channel: Channel): void
  (e: 'delete', channelId: string): void
  (e: 'selection-change', selected: Set<string>): void
}>()

const toggleSelection = (channelId: string) => {
  const newSelected = new Set(props.selected)
  if (newSelected.has(channelId)) {
    newSelected.delete(channelId)
  } else {
    newSelected.add(channelId)
  }
  emit('selection-change', newSelected)
}

const toggleSelectAll = () => {
  if (props.selected.size === props.channels.length) {
    emit('selection-change', new Set())
  } else {
    emit('selection-change', new Set(props.channels.map(ch => ch.id)))
  }
}
</script>

<template>
  <div class="card overflow-x-auto">
    <table class="min-w-full divide-y divide-gray-200">
      <thead>
        <tr>
          <th class="px-4 py-3 text-left">
            <input
              type="checkbox"
              :checked="selected.size === channels.length && channels.length > 0"
              @change="toggleSelectAll"
            />
          </th>
          <th class="px-4 py-3 text-left">Name</th>
          <th class="px-4 py-3 text-left">Group</th>
          <th class="px-4 py-3 text-left">Resolution</th>
          <th class="px-4 py-3 text-left">Status</th>
          <th class="px-4 py-3 text-right">Actions</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-gray-200">
        <tr v-if="isLoading">
          <td colspan="6" class="px-4 py-8 text-center text-gray-500">
            Loading channels...
          </td>
        </tr>

        <tr v-else-if="channels.length === 0">
          <td colspan="6" class="px-4 py-8 text-center text-gray-500">
            No channels found
          </td>
        </tr>

        <tr
          v-for="channel in channels"
          :key="channel.id"
          :class="{ 'bg-blue-50': selected.has(channel.id) }"
        >
          <td class="px-4 py-3">
            <input
              type="checkbox"
              :checked="selected.has(channel.id)"
              @change="toggleSelection(channel.id)"
            />
          </td>
          <td class="px-4 py-3">
            <div class="flex items-center gap-2">
              <img
                v-if="channel.tvg_logo"
                :src="channel.tvg_logo"
                :alt="channel.name"
                class="w-8 h-8 rounded"
              />
              <span class="font-medium">{{ channel.name }}</span>
            </div>
          </td>
          <td class="px-4 py-3 text-gray-600">
            {{ channel.group || '-' }}
          </td>
          <td class="px-4 py-3 text-gray-600">
            {{ channel.resolution || 'Unknown' }}
          </td>
          <td class="px-4 py-3">
            <span
              :class="[
                'px-2 py-1 rounded text-sm',
                channel.is_online ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
              ]"
            >
              {{ channel.is_online ? 'Online' : 'Offline' }}
            </span>
          </td>
          <td class="px-4 py-3 text-right">
            <button
              @click="emit('edit', channel)"
              class="btn btn-sm btn-secondary mr-2"
            >
              Edit
            </button>
            <button
              @click="emit('delete', channel.id)"
              class="btn btn-sm btn-danger"
            >
              Delete
            </button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
```

(Continue with ChannelEditModal and BatchActionBar components - truncated for brevity)

### Verification Criteria

**Backend Tests:**

- [ ] All channel API tests pass
- [ ] Pagination works correctly
- [ ] Multi-dimensional filtering (group + resolution + status + search)
- [ ] Update preserves manually_edited flag
- [ ] Test coverage >80%

**Frontend Tests:**

- [ ] TVChannels view loads channels
- [ ] Filters update channel list
- [ ] Pagination works
- [ ] Edit modal opens and saves
- [ ] Batch selection and delete work
- [ ] Component test coverage >75%

**E2E Tests:**

- [ ] Full CRUD workflow
- [ ] Filter combinations work
- [ ] Batch operations work correctly

**Manual Testing:**

- [ ] Search is responsive (debounced)
- [ ] Table is scrollable on mobile
- [ ] Edit modal validates inputs
- [ ] Delete confirmation shows

## Dependencies

No new dependencies required beyond existing Vuelidate and Headless UI.
