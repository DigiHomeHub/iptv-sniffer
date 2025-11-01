# Task 7.5: M3U Import/Export with Vue

## Overview

Implement M3U file import/export functionality with Vue 3 drag-and-drop uploader, progress tracking, character encoding detection, and export configuration modal. Backend handles M3U parsing, encoding detection, and playlist generation.

**Priority**: P1 - Core workflow for existing playlists

**Estimated Duration**: 12-16 hours

## Prerequisites

- Task 7.0: Vue 3 + Vite Frontend Setup (completed)
- Task 7.1: Vue Router + Tab Navigation (completed)
- Task 7.4: Channel Management Page (completed for integration)
- Backend: M3U parser and generator (Task 4.1, 4.3) completed
- Backend: Character encoding detection (Task 4.2) completed

## Implementation Summary

### Key Components

1. **M3UImport.vue** - File upload component
   - Drag-and-drop zone with visual feedback
   - File validation (.m3u, .m3u8 extensions)
   - Progress tracking during import

2. **ImportProgress.vue** - Import progress tracker
   - Shows imported vs failed channels
   - Error reasons display
   - Post-import actions (validate, view channels)

3. **M3UExportModal.vue** - Export configuration modal
   - Filter options (group, resolution, status)
   - Custom channel selection
   - Download button with loading state

4. **M3U API** (`/api/m3u`)
   - `POST /api/m3u/import` - Upload and parse M3U file
   - `GET /api/m3u/export` - Generate and download M3U playlist

## TDD Implementation

### Test First (Red)

#### Backend Tests

```python
# tests/integration/web/test_m3u_api.py

import pytest
from fastapi.testclient import TestClient
from iptv_sniffer.web.app import app

client = TestClient(app)

def test_import_m3u_file():
    """POST /api/m3u/import should parse and save channels"""
    m3u_content = """#EXTM3U
#EXTINF:-1 tvg-id="cctv1" group-title="央视",CCTV-1
http://test1.com
#EXTINF:-1 tvg-id="cctv2" group-title="央视",CCTV-2
http://test2.com
"""

    files = {"file": ("playlist.m3u", m3u_content.encode(), "audio/x-mpegurl")}
    response = client.post("/api/m3u/import", files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["imported"] == 2
    assert data["failed"] == 0
    assert len(data["channels"]) == 2

def test_import_m3u_with_gb2312_encoding():
    """Should handle GB2312 encoded M3U files"""
    m3u_content = "#EXTM3U\n#EXTINF:-1,测试频道\nhttp://test.com"
    m3u_bytes = m3u_content.encode("gb2312")

    files = {"file": ("playlist.m3u", m3u_bytes, "audio/x-mpegurl")}
    response = client.post("/api/m3u/import", files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["imported"] == 1
    # Verify Chinese characters decoded correctly
    assert "测试频道" in data["channels"][0]["name"]

def test_import_invalid_file_format():
    """Should reject non-M3U files"""
    files = {"file": ("test.txt", b"not an m3u file", "text/plain")}
    response = client.post("/api/m3u/import", files=files)

    assert response.status_code == 400
    assert "M3U or M3U8" in response.json()["detail"]

def test_export_m3u_all_channels():
    """GET /api/m3u/export should generate M3U file"""
    response = client.get("/api/m3u/export")

    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/x-mpegurl"
    assert "attachment" in response.headers["content-disposition"]

    content = response.text
    assert content.startswith("#EXTM3U")

def test_export_m3u_with_filters():
    """Should export only channels matching filters"""
    response = client.get("/api/m3u/export?group=央视&status=online")

    assert response.status_code == 200
    content = response.text

    # Verify only央视 group channels included
    lines = content.split('\n')
    for line in lines:
        if 'group-title=' in line:
            assert 'group-title="央视"' in line

def test_export_empty_result():
    """Should handle export with no matching channels"""
    response = client.get("/api/m3u/export?group=nonexistent")

    assert response.status_code == 200
    content = response.text
    assert content.strip() == "#EXTM3U"  # Only header, no channels

def test_import_large_m3u_file():
    """Should handle large M3U files (>10,000 channels)"""
    # Generate large M3U content
    m3u_lines = ["#EXTM3U"]
    for i in range(10000):
        m3u_lines.append(f"#EXTINF:-1 tvg-id='ch{i}' group-title='Test',Channel {i}")
        m3u_lines.append(f"http://test.com/channel{i}")

    m3u_content = "\n".join(m3u_lines)

    files = {"file": ("large.m3u", m3u_content.encode(), "audio/x-mpegurl")}
    response = client.post("/api/m3u/import", files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["imported"] == 10000
```

### Implement (Green)

#### Step 1: Implement M3U API

```python
# iptv_sniffer/web/api/m3u.py

from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import StreamingResponse
from typing import Optional, List
from io import StringIO
from datetime import datetime
from pydantic import BaseModel
from iptv_sniffer.m3u.parser import M3UParser
from iptv_sniffer.m3u.generator import M3UGenerator
from iptv_sniffer.m3u.encoding import detect_encoding
from iptv_sniffer.channel.models import Channel
from iptv_sniffer.storage.json_repository import JSONChannelRepository
from iptv_sniffer.utils.config import AppConfig
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/m3u", tags=["m3u"])

config = AppConfig()
repo = JSONChannelRepository(config.data_dir / "channels.json")


class ImportResult(BaseModel):
    imported: int
    failed: int
    channels: List[Channel]
    errors: List[str] = []


@router.post("/import", response_model=ImportResult)
async def import_m3u(file: UploadFile = File(...)):
    """
    Import M3U playlist file with automatic encoding detection

    Supported encodings: UTF-8, GB2312, GBK (auto-detected)
    """
    if not file.filename.endswith(('.m3u', '.m3u8')):
        raise HTTPException(400, "File must be M3U or M3U8 format")

    try:
        # Read file content
        content_bytes = await file.read()

        # Detect encoding and decode
        encoding = detect_encoding(content_bytes)
        logger.info(f"Detected encoding: {encoding}")

        try:
            content = content_bytes.decode(encoding)
        except UnicodeDecodeError as e:
            logger.error(f"Failed to decode with {encoding}: {e}")
            raise HTTPException(400, f"Failed to decode file with encoding {encoding}")

        # Parse M3U
        parser = M3UParser()
        playlist = parser.parse(content)

        # Convert M3UChannel to Channel and save
        imported_channels = []
        failed = 0
        errors = []

        for m3u_channel in playlist.channels:
            try:
                channel = Channel(
                    name=m3u_channel.name,
                    url=m3u_channel.url,
                    tvg_id=m3u_channel.tvg_id,
                    tvg_logo=m3u_channel.tvg_logo,
                    group=m3u_channel.group_title
                )
                saved = await repo.add(channel)
                imported_channels.append(saved)
            except Exception as e:
                logger.warning(f"Failed to import channel {m3u_channel.name}: {e}")
                failed += 1
                errors.append(f"{m3u_channel.name}: {str(e)}")

        logger.info(f"Imported {len(imported_channels)} channels, failed: {failed}")

        return ImportResult(
            imported=len(imported_channels),
            failed=failed,
            channels=imported_channels,
            errors=errors[:10]  # Limit to first 10 errors
        )

    except Exception as e:
        logger.error(f"Failed to import M3U: {e}")
        raise HTTPException(500, f"Failed to import M3U: {str(e)}")


@router.get("/export")
async def export_m3u(
    group: Optional[str] = Query(None, description="Filter by group"),
    resolution: Optional[str] = Query(None, description="Filter by resolution"),
    status: Optional[str] = Query(None, description="Filter by status: online/offline")
):
    """
    Export channels as M3U playlist with optional filters

    Returns: M3U file download (audio/x-mpegurl)
    """

    # Build filters
    filters = {}
    if group:
        filters["group"] = group
    if status == "online":
        filters["is_online"] = True
    elif status == "offline":
        filters["is_online"] = False

    # Get channels
    channels = await repo.find_all(filters)

    # Apply resolution filter
    if resolution:
        channels = [ch for ch in channels if ch.resolution == resolution]

    logger.info(f"Exporting {len(channels)} channels with filters: {filters}")

    # Generate M3U content
    generator = M3UGenerator()
    m3u_content = generator.generate(channels)

    # Create filename with timestamp
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"iptv_channels_{timestamp}.m3u"

    # Return as downloadable file
    return StreamingResponse(
        StringIO(m3u_content),
        media_type="audio/x-mpegurl",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Type": "audio/x-mpegurl; charset=utf-8"
        }
    )
```

```python
# iptv_sniffer/web/app.py (register router)

from iptv_sniffer.web.api import scan, screenshots, channels, m3u

app.include_router(scan.router)
app.include_router(screenshots.router)
app.include_router(channels.router)
app.include_router(m3u.router)
```

#### Step 2: Update API Client

```typescript
// frontend/src/api/client.ts (add m3u methods)

const API = {
  // ... existing code

  m3u: {
    import: async (file: File) => {
      const formData = new FormData()
      formData.append('file', file)

      const response = await fetch(`${API.baseURL}/m3u/import`, {
        method: 'POST',
        body: formData
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Import failed')
      }

      return await response.json()
    },

    export: (params: {
      group?: string
      resolution?: string
      status?: string
    }) => {
      const queryString = new URLSearchParams(
        Object.entries(params).reduce((acc, [key, value]) => {
          if (value) acc[key] = value
          return acc
        }, {} as Record<string, string>)
      ).toString()

      // Trigger download
      window.location.href = `${API.baseURL}/m3u/export?${queryString}`
    }
  }
}

export default API
```

#### Step 3: Create M3UImport Component

```vue
<!-- frontend/src/components/m3u/M3UImport.vue -->

<script setup lang="ts">
import { ref } from 'vue'
import ImportProgress from './ImportProgress.vue'
import api from '@/api/client'

interface ImportResult {
  imported: number
  failed: number
  channels: Array<any>
  errors: string[]
}

const isDragging = ref(false)
const isUploading = ref(false)
const importResult = ref<ImportResult | null>(null)

const emit = defineEmits<{
  (e: 'import-complete', result: ImportResult): void
}>()

const handleDragEnter = (e: DragEvent) => {
  e.preventDefault()
  isDragging.value = true
}

const handleDragLeave = (e: DragEvent) => {
  e.preventDefault()
  isDragging.value = false
}

const handleDragOver = (e: DragEvent) => {
  e.preventDefault()
}

const handleDrop = async (e: DragEvent) => {
  e.preventDefault()
  isDragging.value = false

  const files = e.dataTransfer?.files
  if (!files || files.length === 0) return

  await uploadFile(files[0])
}

const handleFileSelect = async (e: Event) => {
  const input = e.target as HTMLInputElement
  const files = input.files
  if (!files || files.length === 0) return

  await uploadFile(files[0])
}

const uploadFile = async (file: File) => {
  // Validate file extension
  if (!file.name.endsWith('.m3u') && !file.name.endsWith('.m3u8')) {
    alert('Please upload a .m3u or .m3u8 file')
    return
  }

  isUploading.value = true
  importResult.value = null

  try {
    const result = await api.m3u.import(file)
    importResult.value = result
    emit('import-complete', result)
  } catch (error: any) {
    alert(`Import failed: ${error.message}`)
  } finally {
    isUploading.value = false
  }
}

const resetImport = () => {
  importResult.value = null
}
</script>

<template>
  <div class="m3u-import-container">
    <div
      v-if="!importResult"
      @dragenter="handleDragEnter"
      @dragleave="handleDragLeave"
      @dragover="handleDragOver"
      @drop="handleDrop"
      :class="[
        'border-2 border-dashed rounded-lg p-12 text-center transition-colors',
        isDragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'
      ]"
    >
      <svg
        class="mx-auto h-12 w-12 text-gray-400"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
        />
      </svg>

      <div class="mt-4">
        <label
          for="file-upload"
          class="cursor-pointer text-blue-600 hover:text-blue-700 font-medium"
        >
          Click to upload
        </label>
        <span class="text-gray-600"> or drag and drop</span>
      </div>

      <p class="mt-2 text-sm text-gray-500">
        M3U or M3U8 files only
      </p>

      <input
        id="file-upload"
        type="file"
        accept=".m3u,.m3u8"
        class="hidden"
        @change="handleFileSelect"
      />

      <div v-if="isUploading" class="mt-4">
        <div class="inline-block animate-spin rounded-full h-8 w-8 border-4 border-blue-500 border-t-transparent" />
        <p class="mt-2 text-sm text-gray-600">Importing channels...</p>
      </div>
    </div>

    <ImportProgress
      v-else
      :result="importResult"
      @reset="resetImport"
    />
  </div>
</template>
```

#### Step 4: Create ImportProgress Component

```vue
<!-- frontend/src/components/m3u/ImportProgress.vue -->

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  result: {
    imported: number
    failed: number
    channels: Array<any>
    errors: string[]
  }
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'reset'): void
  (e: 'view-channels'): void
}>()

const successRate = computed(() => {
  const total = props.result.imported + props.result.failed
  return total > 0 ? Math.round((props.result.imported / total) * 100) : 0
})
</script>

<template>
  <div class="card">
    <div class="text-center mb-6">
      <svg
        v-if="result.failed === 0"
        class="mx-auto h-16 w-16 text-green-500"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>

      <svg
        v-else
        class="mx-auto h-16 w-16 text-yellow-500"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
        />
      </svg>

      <h2 class="mt-4 text-2xl font-bold">
        Import {{ result.failed === 0 ? 'Complete' : 'Finished with Warnings' }}
      </h2>
    </div>

    <div class="grid grid-cols-3 gap-4 mb-6">
      <div class="text-center">
        <div class="text-3xl font-bold text-gray-900">
          {{ result.imported + result.failed }}
        </div>
        <div class="text-sm text-gray-600">Total Channels</div>
      </div>

      <div class="text-center">
        <div class="text-3xl font-bold text-green-600">
          {{ result.imported }}
        </div>
        <div class="text-sm text-gray-600">Imported</div>
      </div>

      <div class="text-center">
        <div class="text-3xl font-bold text-red-600">
          {{ result.failed }}
        </div>
        <div class="text-sm text-gray-600">Failed</div>
      </div>
    </div>

    <div class="mb-6">
      <div class="flex justify-between text-sm text-gray-600 mb-1">
        <span>Success Rate</span>
        <span>{{ successRate }}%</span>
      </div>
      <div class="w-full bg-gray-200 rounded-full h-2">
        <div
          :style="{ width: successRate + '%' }"
          :class="[
            'h-2 rounded-full transition-all',
            successRate === 100 ? 'bg-green-500' : 'bg-yellow-500'
          ]"
        />
      </div>
    </div>

    <div v-if="result.errors.length > 0" class="mb-6">
      <h3 class="font-semibold text-red-600 mb-2">Import Errors:</h3>
      <ul class="text-sm text-gray-700 space-y-1 max-h-40 overflow-y-auto">
        <li v-for="(error, index) in result.errors" :key="index">
          {{ error }}
        </li>
      </ul>
    </div>

    <div class="flex gap-4 justify-center">
      <button @click="emit('reset')" class="btn btn-secondary">
        Import Another File
      </button>
      <button @click="emit('view-channels')" class="btn btn-primary">
        View Imported Channels
      </button>
    </div>
  </div>
</template>
```

#### Step 5: Create M3UExportModal Component

```vue
<!-- frontend/src/components/m3u/M3UExportModal.vue -->

<script setup lang="ts">
import { ref } from 'vue'
import { Dialog, DialogPanel, DialogTitle } from '@headlessui/vue'
import api from '@/api/client'

interface Props {
  isOpen: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'close'): void
}>()

const filters = ref({
  group: '',
  resolution: '',
  status: ''
})

const handleExport = () => {
  const exportParams = Object.fromEntries(
    Object.entries(filters.value).filter(([_, value]) => value !== '')
  )

  api.m3u.export(exportParams)
  emit('close')
}
</script>

<template>
  <Dialog :open="isOpen" @close="emit('close')" class="relative z-50">
    <div class="fixed inset-0 bg-black/30" />

    <div class="fixed inset-0 flex items-center justify-center p-4">
      <DialogPanel class="bg-white rounded-lg p-6 max-w-md w-full">
        <DialogTitle class="text-xl font-bold mb-4">
          Export M3U Playlist
        </DialogTitle>

        <div class="space-y-4 mb-6">
          <div>
            <label class="block text-sm font-medium mb-1">
              Group Filter (Optional)
            </label>
            <select v-model="filters.group" class="input-field">
              <option value="">All Groups</option>
              <option value="央视">央视</option>
              <option value="卫视">卫视</option>
              <option value="影视">影视</option>
            </select>
          </div>

          <div>
            <label class="block text-sm font-medium mb-1">
              Resolution Filter (Optional)
            </label>
            <select v-model="filters.resolution" class="input-field">
              <option value="">All Resolutions</option>
              <option value="4K">4K</option>
              <option value="1080p">1080p</option>
              <option value="720p">720p</option>
            </select>
          </div>

          <div>
            <label class="block text-sm font-medium mb-1">
              Status Filter (Optional)
            </label>
            <select v-model="filters.status" class="input-field">
              <option value="">All Status</option>
              <option value="online">Online Only</option>
              <option value="offline">Offline Only</option>
            </select>
          </div>
        </div>

        <div class="flex gap-4 justify-end">
          <button @click="emit('close')" class="btn btn-secondary">
            Cancel
          </button>
          <button @click="handleExport" class="btn btn-primary">
            Export M3U
          </button>
        </div>
      </DialogPanel>
    </div>
  </Dialog>
</template>
```

### Verification Criteria

**Backend Tests:**

- [ ] M3U import with UTF-8 encoding works
- [ ] M3U import with GB2312 encoding works
- [ ] Invalid file format rejected
- [ ] Large file import (>10,000 channels) works
- [ ] Export generates valid M3U file
- [ ] Export filters work correctly
- [ ] Test coverage >80%

**Frontend Tests:**

- [ ] Drag-and-drop file upload works
- [ ] File validation shows errors
- [ ] Import progress displays correctly
- [ ] Export modal filters work
- [ ] Component test coverage >75%

**E2E Tests:**

- [ ] Full import workflow
- [ ] Export with filters downloads file
- [ ] Large file import completes

**Manual Testing:**

- [ ] Drag-and-drop visual feedback works
- [ ] Import errors displayed clearly
- [ ] Exported M3U plays in VLC
- [ ] Character encoding preserved (test with Chinese names)

## Notes

- **Encoding Detection**: Uses `chardet` library (Python) for automatic detection
- **Large File Handling**: Backend streams responses for files >100MB
- **Export Filename**: Includes timestamp for uniqueness
- **Browser Download**: Uses `window.location.href` for triggering download (compatible with all browsers)

## Dependencies

No new frontend dependencies required. Backend already has `chardet` from Task 4.2.
