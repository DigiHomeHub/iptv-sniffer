# Task 7.3: Screenshot Display with Vue

## Overview

Implement screenshot display components using Vue 3 with lazy loading, full-screen lightbox modal (using Headless UI Dialog), and secure FastAPI endpoint for serving screenshot images.

**Priority**: P0 - Critical for visual stream validation

**Estimated Duration**: 6-8 hours

## Prerequisites

- Task 7.0: Vue 3 + Vite Frontend Setup (completed)
- Task 7.2: Stream Test Page with Vue (completed for integration)
- Backend: Screenshot capture (Task 2.3) completed

## Implementation Summary

### Key Components

1. **ChannelCard.vue** - Enhanced channel card with screenshot thumbnail
   - Lazy-loaded screenshot images
   - Click to open lightbox
   - Valid/Invalid status badge
   - Channel metadata display

2. **ImageLightbox.vue** - Full-screen image viewer
   - Headless UI Dialog for accessibility
   - Keyboard navigation (Esc to close, Arrow keys for next/prev)
   - Smooth transitions
   - Optional: Zoom controls

3. **Screenshot API Endpoint** (`/api/screenshots/{filename}`)
   - Secure file serving with path traversal protection
   - Cache headers for performance
   - 404 handling for missing screenshots

## TDD Implementation

### Test First (Red)

#### Backend Tests

```python
# tests/unit/web/test_screenshot_api.py

from pathlib import Path
from fastapi.testclient import TestClient
from iptv_sniffer.web.app import app

client = TestClient(app)

def test_screenshot_endpoint_serves_image(tmp_path):
    """Screenshot endpoint should serve PNG images with correct headers"""
    # Setup: create test screenshot
    screenshot_dir = tmp_path / "screenshots"
    screenshot_dir.mkdir()
    screenshot_path = screenshot_dir / "test_192.168.1.1.png"
    screenshot_path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)  # Minimal PNG header

    # Mock config to use tmp_path
    with patch('iptv_sniffer.web.api.screenshots.AppConfig') as mock_config:
        mock_config.return_value.screenshot_dir = screenshot_dir

        response = client.get("/api/screenshots/test_192.168.1.1.png")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert "Cache-Control" in response.headers
    assert response.content.startswith(b"\x89PNG")

def test_missing_screenshot_returns_404():
    """Non-existent screenshot should return 404"""
    response = client.get("/api/screenshots/nonexistent.png")
    assert response.status_code == 404
    assert response.json()["detail"] == "Screenshot not found"

def test_directory_traversal_blocked():
    """Should prevent directory traversal attacks"""
    malicious_paths = [
        "../../../etc/passwd",
        "..%2F..%2F..%2Fetc%2Fpasswd",
        "....//....//etc/passwd"
    ]

    for path in malicious_paths:
        response = client.get(f"/api/screenshots/{path}")
        assert response.status_code in [403, 404]  # Either forbidden or not found

def test_screenshot_cache_headers():
    """Should set appropriate cache headers for browser caching"""
    response = client.get("/api/screenshots/test.png")
    assert "Cache-Control" in response.headers
    assert "public" in response.headers["Cache-Control"]
    assert "max-age" in response.headers["Cache-Control"]
```

#### Frontend Tests

```typescript
// frontend/tests/unit/components/ImageLightbox.spec.ts

import { mount } from '@vue/test-utils'
import { describe, it, expect } from 'vitest'
import ImageLightbox from '@/components/common/ImageLightbox.vue'

describe('ImageLightbox', () => {
  it('renders image in modal when open', () => {
    const wrapper = mount(ImageLightbox, {
      props: {
        isOpen: true,
        imageUrl: '/test-image.png',
        altText: 'Test Channel'
      }
    })

    expect(wrapper.find('img').attributes('src')).toBe('/test-image.png')
    expect(wrapper.find('img').attributes('alt')).toBe('Test Channel')
  })

  it('emits close event when close button clicked', async () => {
    const wrapper = mount(ImageLightbox, {
      props: {
        isOpen: true,
        imageUrl: '/test.png'
      }
    })

    await wrapper.find('[aria-label="Close"]').trigger('click')

    expect(wrapper.emitted('close')).toBeTruthy()
  })

  it('closes on Escape key press', async () => {
    const wrapper = mount(ImageLightbox, {
      props: {
        isOpen: true,
        imageUrl: '/test.png'
      }
    })

    await wrapper.trigger('keydown', { key: 'Escape' })

    expect(wrapper.emitted('close')).toBeTruthy()
  })

  it('does not render when closed', () => {
    const wrapper = mount(ImageLightbox, {
      props: {
        isOpen: false,
        imageUrl: '/test.png'
      }
    })

    expect(wrapper.find('img').exists()).toBe(false)
  })
})
```

### Implement (Green)

#### Step 1: Implement Backend Screenshot API

```python
# iptv_sniffer/web/api/screenshots.py

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
from iptv_sniffer.utils.config import AppConfig
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/screenshots", tags=["screenshots"])

@router.get("/{filename}")
async def get_screenshot(filename: str):
    """
    Serve screenshot image with security and performance optimizations

    Args:
        filename: Screenshot filename (e.g., "192.168.1.1_1234567890.png")

    Returns:
        FileResponse with PNG image and cache headers

    Raises:
        HTTPException 404: Screenshot not found
        HTTPException 403: Access denied (path traversal attempt)
    """
    config = AppConfig()
    screenshot_path = config.screenshot_dir / filename

    # Security: Check file exists
    if not screenshot_path.exists():
        logger.warning(f"Screenshot not found: {filename}")
        raise HTTPException(404, "Screenshot not found")

    # Security: Prevent directory traversal
    try:
        resolved = screenshot_path.resolve()
        screenshot_dir_resolved = config.screenshot_dir.resolve()

        if not resolved.is_relative_to(screenshot_dir_resolved):
            logger.error(f"Directory traversal attempt blocked: {filename}")
            raise HTTPException(403, "Access denied")
    except (ValueError, OSError):
        logger.error(f"Invalid path: {filename}")
        raise HTTPException(403, "Access denied")

    # Serve with cache headers for performance
    return FileResponse(
        screenshot_path,
        media_type="image/png",
        headers={
            "Cache-Control": "public, max-age=3600, immutable",
            "X-Content-Type-Options": "nosniff"  # Security: prevent MIME sniffing
        }
    )
```

```python
# iptv_sniffer/web/app.py (register router)

from iptv_sniffer.web.api import scan, screenshots

app.include_router(scan.router)
app.include_router(screenshots.router)
```

#### Step 2: Create ImageLightbox Component

```vue
<!-- frontend/src/components/common/ImageLightbox.vue -->

<script setup lang="ts">
import { ref, watch } from 'vue'
import {
  Dialog,
  DialogPanel,
  TransitionRoot,
  TransitionChild
} from '@headlessui/vue'

interface Props {
  isOpen: boolean
  imageUrl: string
  altText?: string
}

const props = withDefaults(defineProps<Props>(), {
  altText: 'Screenshot'
})

const emit = defineEmits<{
  (e: 'close'): void
}>()

const imageLoaded = ref(false)

const handleClose = () => {
  imageLoaded.value = false
  emit('close')
}

const handleKeydown = (event: KeyboardEvent) => {
  if (event.key === 'Escape') {
    handleClose()
  }
}

watch(() => props.isOpen, (newValue) => {
  if (newValue) {
    window.addEventListener('keydown', handleKeydown)
  } else {
    window.removeEventListener('keydown', handleKeydown)
  }
})
</script>

<template>
  <TransitionRoot :show="isOpen" as="template">
    <Dialog @close="handleClose" class="relative z-50">
      <!-- Background overlay -->
      <TransitionChild
        as="template"
        enter="ease-out duration-300"
        enter-from="opacity-0"
        enter-to="opacity-100"
        leave="ease-in duration-200"
        leave-from="opacity-100"
        leave-to="opacity-0"
      >
        <div class="fixed inset-0 bg-black/80" />
      </TransitionChild>

      <!-- Modal content -->
      <div class="fixed inset-0 overflow-y-auto">
        <div class="flex min-h-full items-center justify-center p-4">
          <TransitionChild
            as="template"
            enter="ease-out duration-300"
            enter-from="opacity-0 scale-95"
            enter-to="opacity-100 scale-100"
            leave="ease-in duration-200"
            leave-from="opacity-100 scale-100"
            leave-to="opacity-0 scale-95"
          >
            <DialogPanel class="relative max-w-7xl transform overflow-hidden rounded-lg bg-white p-2">
              <!-- Close button -->
              <button
                @click="handleClose"
                aria-label="Close"
                class="absolute top-2 right-2 z-10 rounded-full bg-black/50 p-2 text-white hover:bg-black/70 transition-colors"
              >
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>

              <!-- Image -->
              <div class="relative">
                <img
                  :src="imageUrl"
                  :alt="altText"
                  class="max-h-[90vh] w-auto object-contain"
                  @load="imageLoaded = true"
                />

                <!-- Loading indicator -->
                <div
                  v-if="!imageLoaded"
                  class="absolute inset-0 flex items-center justify-center bg-gray-100"
                >
                  <svg class="animate-spin h-12 w-12 text-blue-500" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                </div>
              </div>
            </DialogPanel>
          </TransitionChild>
        </div>
      </div>
    </Dialog>
  </TransitionRoot>
</template>
```

#### Step 3: Update ChannelCard Component

```vue
<!-- frontend/src/components/streamTest/ChannelCard.vue -->

<script setup lang="ts">
import { ref, computed } from 'vue'
import ImageLightbox from '@/components/common/ImageLightbox.vue'
import type { Channel } from '@/types/channel'

interface Props {
  channel: Channel
}

const props = defineProps<Props>()

const lightboxOpen = ref(false)

const screenshotUrl = computed(() => {
  if (!props.channel.screenshot_path) {
    return '/placeholder.png'
  }
  const filename = props.channel.screenshot_path.split('/').pop()
  return `/api/screenshots/${filename}`
})

const openLightbox = () => {
  if (props.channel.screenshot_path) {
    lightboxOpen.value = true
  }
}

const closeLightbox = () => {
  lightboxOpen.value = false
}
</script>

<template>
  <div class="card hover:shadow-lg transition-shadow">
    <div class="relative cursor-pointer" @click="openLightbox">
      <img
        :src="screenshotUrl"
        :alt="channel.name || 'Channel screenshot'"
        class="w-full h-48 object-cover rounded"
        loading="lazy"
      />

      <!-- Status Badge -->
      <span
        :class="[
          'absolute top-2 right-2 px-2 py-1 rounded text-sm font-medium',
          channel.is_online ? 'bg-green-500 text-white' : 'bg-red-500 text-white'
        ]"
      >
        {{ channel.is_online ? 'Valid' : 'Invalid' }}
      </span>

      <!-- Zoom indicator on hover -->
      <div class="absolute inset-0 bg-black/0 hover:bg-black/10 transition-colors flex items-center justify-center">
        <svg
          class="w-8 h-8 text-white opacity-0 group-hover:opacity-100 transition-opacity"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v3m0 0v3m0-3h3m-3 0H7" />
        </svg>
      </div>
    </div>

    <div class="mt-3">
      <h3 class="font-semibold truncate text-gray-900">
        {{ channel.name || channel.url }}
      </h3>
      <div class="mt-2 flex justify-between text-sm text-gray-600">
        <span>{{ channel.resolution || 'Unknown' }}</span>
        <span>{{ channel.codec_video || 'N/A' }}</span>
      </div>
    </div>

    <!-- Lightbox -->
    <ImageLightbox
      :is-open="lightboxOpen"
      :image-url="screenshotUrl"
      :alt-text="channel.name || 'Channel screenshot'"
      @close="closeLightbox"
    />
  </div>
</template>
```

#### Step 4: Update ChannelResultsGrid to Use ChannelCard

```vue
<!-- frontend/src/components/streamTest/ChannelResultsGrid.vue -->

<script setup lang="ts">
import { ref, computed } from 'vue'
import ChannelCard from './ChannelCard.vue'
import type { Channel } from '@/types/channel'

// ... (previous code remains the same)
</script>

<template>
  <div>
    <!-- Filter Bar (unchanged) -->
    <!-- ... -->

    <!-- Results Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <ChannelCard
        v-for="channel in filteredChannels"
        :key="channel.id"
        :channel="channel"
      />
    </div>

    <div v-if="filteredChannels.length === 0" class="text-center py-12 text-gray-500">
      No channels match the current filter
    </div>
  </div>
</template>
```

### Verification Criteria

**Backend Tests:**

- [ ] Screenshot endpoint serves images correctly
- [ ] Path traversal attacks blocked
- [ ] 404 returned for missing screenshots
- [ ] Cache headers set correctly
- [ ] Test coverage >80%

**Frontend Tests:**

- [ ] ImageLightbox opens and displays image
- [ ] Close button works
- [ ] Escape key closes lightbox
- [ ] Loading indicator displays while image loads
- [ ] Component test coverage >75%

**E2E Tests (Playwright):**

- [ ] Click channel card opens lightbox
- [ ] Lightbox displays full-size screenshot
- [ ] Close button and Escape key work
- [ ] Multiple screenshots can be viewed sequentially

**Manual Testing:**

- [ ] Screenshots load lazily (check Network tab)
- [ ] Lightbox transitions are smooth
- [ ] Clicking outside lightbox closes it (Headless UI default behavior)
- [ ] Keyboard navigation works (Escape, Tab for accessibility)
- [ ] Placeholder image displays for missing screenshots
- [ ] Images are cached (check Response Headers in DevTools)

**Code Quality:**

- [ ] TypeScript types defined for all props
- [ ] No console errors
- [ ] Headless UI Dialog used correctly (accessibility)
- [ ] Responsive layout works on mobile

## Notes

- **Placeholder Image**: Add `/frontend/public/placeholder.png` (gray rectangle with "No Screenshot" text)
- **Image Optimization**: Backend uses FFmpeg for screenshot capture. Consider adding width/height to `<img>` tags for better CLS (Cumulative Layout Shift) scores.
- **Security**: Backend prevents directory traversal with `is_relative_to()` check (Python 3.9+)
- **Performance**: Browser caching reduces repeated requests. Screenshots are immutable after creation.

## Dependencies

Add to `frontend/package.json`:

```json
{
  "dependencies": {
    "@headlessui/vue": "^1.7.22"
  }
}
```

Install:

```bash
cd frontend
npm install @headlessui/vue
```
