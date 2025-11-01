# Task 7.2: Stream Test Page with Vue

## Overview

Implement the Stream Test page using Vue 3 Composition API with scan configuration form, real-time progress tracking via HTTP polling, and filterable results display with screenshot thumbnails.

**Priority**: P0 - Core user workflow for stream discovery

**Estimated Duration**: 12-16 hours

## Prerequisites

- Task 7.0: Vue 3 + Vite Frontend Setup (completed)
- Task 7.1: Vue Router + Tab Navigation (completed)
- Backend: Scan API (`/api/scan/start`, `/api/scan/{scan_id}`) implemented

## Implementation Summary

### Key Components

1. **StreamTest.vue** - Main page component
   - Manages scan lifecycle state (idle → running → completed/cancelled)
   - Coordinates child components
   - Handles HTTP polling for progress updates

2. **ScanConfigForm.vue** - Input form component
   - Base URL template with `{ip}` placeholder
   - IP range inputs (start_ip, end_ip) with validation
   - Scan mode selector (template, multicast, preset)
   - Form validation using Vuelidate or VeeValidate

3. **ScanProgress.vue** - Progress tracking component
   - Animated progress bar
   - Real-time statistics: Total, Completed, Valid, Invalid
   - Elapsed time and estimated remaining time
   - Cancel scan button

4. **ChannelResultsGrid.vue** - Results display component
   - Grid layout (responsive: 1/2/3 columns)
   - Filter buttons: All, Valid Only, Invalid Only
   - Resolution filters: 4K, 1080p, 720p
   - Lazy-loaded screenshot thumbnails

5. **Toast.vue** - Notification component (shared)
   - Auto-dismiss after 3 seconds
   - Types: success, error, info, warning
   - Positioned at top-right corner

## TDD Implementation

### Test First (Red)

```typescript
// frontend/tests/unit/components/ScanConfigForm.spec.ts

import { mount } from '@vue/test-utils'
import { describe, it, expect } from 'vitest'
import ScanConfigForm from '@/components/streamTest/ScanConfigForm.vue'

describe('ScanConfigForm', () => {
  it('renders form inputs correctly', () => {
    const wrapper = mount(ScanConfigForm)

    expect(wrapper.find('input[name="baseUrl"]').exists()).toBe(true)
    expect(wrapper.find('input[name="startIp"]').exists()).toBe(true)
    expect(wrapper.find('input[name="endIp"]').exists()).toBe(true)
    expect(wrapper.find('button[type="submit"]').exists()).toBe(true)
  })

  it('validates IP address format', async () => {
    const wrapper = mount(ScanConfigForm)
    const startIpInput = wrapper.find('input[name="startIp"]')

    await startIpInput.setValue('invalid-ip')
    await wrapper.find('form').trigger('submit')

    expect(wrapper.text()).toContain('Invalid IP address')
  })

  it('emits scan-start event with valid config', async () => {
    const wrapper = mount(ScanConfigForm)

    await wrapper.find('input[name="baseUrl"]').setValue('http://192.168.2.2:7788/rtp/{ip}:8000')
    await wrapper.find('input[name="startIp"]').setValue('192.168.1.1')
    await wrapper.find('input[name="endIp"]').setValue('192.168.1.10')
    await wrapper.find('form').trigger('submit')

    expect(wrapper.emitted('scan-start')).toBeTruthy()
    expect(wrapper.emitted('scan-start')![0]).toEqual([{
      mode: 'template',
      base_url: 'http://192.168.2.2:7788/rtp/{ip}:8000',
      start_ip: '192.168.1.1',
      end_ip: '192.168.1.10'
    }])
  })

  it('disables form when scan is running', async () => {
    const wrapper = mount(ScanConfigForm, {
      props: { isScanning: true }
    })

    expect(wrapper.find('button[type="submit"]').attributes('disabled')).toBeDefined()
    expect(wrapper.find('input[name="startIp"]').attributes('disabled')).toBeDefined()
  })
})
```

```typescript
// frontend/tests/unit/views/StreamTest.spec.ts

import { mount } from '@vue/test-utils'
import { describe, it, expect, vi } from 'vitest'
import StreamTest from '@/views/StreamTest.vue'
import api from '@/api/client'

vi.mock('@/api/client', () => ({
  default: {
    scan: {
      start: vi.fn(),
      getStatus: vi.fn(),
      cancel: vi.fn()
    }
  }
}))

describe('StreamTest.vue', () => {
  it('starts scan and polls for progress', async () => {
    const startMock = vi.spyOn(api.scan, 'start').mockResolvedValue({
      scan_id: 'test-scan-123'
    })

    const getStatusMock = vi.spyOn(api.scan, 'getStatus').mockResolvedValue({
      scan_id: 'test-scan-123',
      status: 'running',
      total: 10,
      completed: 5,
      valid: 3,
      invalid: 2
    })

    const wrapper = mount(StreamTest)

    // Trigger scan start
    await wrapper.findComponent({ name: 'ScanConfigForm' }).vm.$emit('scan-start', {
      mode: 'template',
      base_url: 'http://test.com/{ip}',
      start_ip: '192.168.1.1',
      end_ip: '192.168.1.10'
    })

    await wrapper.vm.$nextTick()

    expect(startMock).toHaveBeenCalled()
    expect(wrapper.vm.scanId).toBe('test-scan-123')

    // Wait for polling
    await new Promise(resolve => setTimeout(resolve, 1100))

    expect(getStatusMock).toHaveBeenCalled()
    expect(wrapper.vm.scanProgress.completed).toBe(5)
  })

  it('stops polling when scan completes', async () => {
    const getStatusMock = vi.spyOn(api.scan, 'getStatus').mockResolvedValue({
      scan_id: 'test-scan-123',
      status: 'completed',
      total: 10,
      completed: 10,
      valid: 8,
      invalid: 2
    })

    const wrapper = mount(StreamTest, {
      data() {
        return {
          scanId: 'test-scan-123',
          isPolling: true
        }
      }
    })

    wrapper.vm.startPolling()
    await new Promise(resolve => setTimeout(resolve, 1100))

    expect(wrapper.vm.isPolling).toBe(false)
  })
})
```

### Implement (Green)

#### Step 1: Create ScanConfigForm Component

```vue
<!-- frontend/src/components/streamTest/ScanConfigForm.vue -->

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useVuelidate } from '@vuelidate/core'
import { required, helpers } from '@vuelidate/validators'

interface ScanConfig {
  mode: string
  base_url: string
  start_ip: string
  end_ip: string
}

interface Props {
  isScanning?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  isScanning: false
})

const emit = defineEmits<{
  (e: 'scan-start', config: ScanConfig): void
}>()

const form = ref<ScanConfig>({
  mode: 'template',
  base_url: 'http://192.168.2.2:7788/rtp/{ip}:8000',
  start_ip: '',
  end_ip: ''
})

const ipRegex = /^(\d{1,3}\.){3}\d{1,3}$/

const rules = {
  base_url: {
    required: helpers.withMessage('Base URL is required', required),
    hasPlaceholder: helpers.withMessage('Base URL must contain {ip} placeholder', (value: string) => value.includes('{ip}'))
  },
  start_ip: {
    required: helpers.withMessage('Start IP is required', required),
    validIp: helpers.withMessage('Invalid IP address', (value: string) => ipRegex.test(value))
  },
  end_ip: {
    required: helpers.withMessage('End IP is required', required),
    validIp: helpers.withMessage('Invalid IP address', (value: string) => ipRegex.test(value))
  }
}

const v$ = useVuelidate(rules, form)

const handleSubmit = async () => {
  const isValid = await v$.value.$validate()
  if (!isValid) return

  emit('scan-start', { ...form.value })
}
</script>

<template>
  <div class="card">
    <h2 class="text-xl font-semibold mb-4">Scan Configuration</h2>
    <form @submit.prevent="handleSubmit" class="space-y-4">
      <div>
        <label for="base-url" class="block text-sm font-medium mb-1">
          Base URL (use {ip} as placeholder)
        </label>
        <input
          id="base-url"
          v-model="form.base_url"
          type="text"
          name="baseUrl"
          :disabled="isScanning"
          class="input-field"
          placeholder="http://192.168.2.2:7788/rtp/{ip}:8000"
        />
        <p v-if="v$.base_url.$error" class="text-red-600 text-sm mt-1">
          {{ v$.base_url.$errors[0].$message }}
        </p>
      </div>

      <div class="grid grid-cols-2 gap-4">
        <div>
          <label for="start-ip" class="block text-sm font-medium mb-1">
            Start IP
          </label>
          <input
            id="start-ip"
            v-model="form.start_ip"
            type="text"
            name="startIp"
            :disabled="isScanning"
            class="input-field"
            placeholder="192.168.1.1"
          />
          <p v-if="v$.start_ip.$error" class="text-red-600 text-sm mt-1">
            {{ v$.start_ip.$errors[0].$message }}
          </p>
        </div>

        <div>
          <label for="end-ip" class="block text-sm font-medium mb-1">
            End IP
          </label>
          <input
            id="end-ip"
            v-model="form.end_ip"
            type="text"
            name="endIp"
            :disabled="isScanning"
            class="input-field"
            placeholder="192.168.1.255"
          />
          <p v-if="v$.end_ip.$error" class="text-red-600 text-sm mt-1">
            {{ v$.end_ip.$errors[0].$message }}
          </p>
        </div>
      </div>

      <div>
        <button
          type="submit"
          :disabled="isScanning"
          class="btn btn-primary"
        >
          Start Test
        </button>
      </div>
    </form>
  </div>
</template>
```

#### Step 2: Create ScanProgress Component

```vue
<!-- frontend/src/components/streamTest/ScanProgress.vue -->

<script setup lang="ts">
import { computed } from 'vue'

interface ScanStatus {
  total: number
  completed: number
  valid: number
  invalid: number
}

interface Props {
  status: ScanStatus
  elapsedTime: number
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'cancel'): void
}>()

const percentage = computed(() => {
  if (props.status.total === 0) return 0
  return Math.round((props.status.completed / props.status.total) * 100)
})

const formatTime = (seconds: number): string => {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

const estimatedRemaining = computed(() => {
  if (props.status.completed === 0) return 0
  const avgTimePerChannel = props.elapsedTime / props.status.completed
  const remaining = props.status.total - props.status.completed
  return Math.round(avgTimePerChannel * remaining)
})
</script>

<template>
  <div class="card">
    <div class="flex justify-between items-center mb-4">
      <h2 class="text-xl font-semibold">Scan Progress</h2>
      <button @click="emit('cancel')" class="btn btn-secondary">
        Cancel Scan
      </button>
    </div>

    <div class="mb-4">
      <div class="relative pt-1">
        <div class="overflow-hidden h-4 text-xs flex rounded bg-gray-200">
          <div
            :style="{ width: percentage + '%' }"
            class="shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center bg-blue-500 transition-all duration-300"
          />
        </div>
        <div class="text-center mt-1 text-sm font-medium">
          {{ percentage }}%
        </div>
      </div>
    </div>

    <div class="grid grid-cols-4 gap-4">
      <div class="text-center">
        <div class="text-2xl font-bold">{{ status.total }}</div>
        <div class="text-sm text-gray-600">Total</div>
      </div>
      <div class="text-center">
        <div class="text-2xl font-bold">{{ status.completed }}</div>
        <div class="text-sm text-gray-600">Completed</div>
      </div>
      <div class="text-center">
        <div class="text-2xl font-bold text-green-600">{{ status.valid }}</div>
        <div class="text-sm text-gray-600">Valid</div>
      </div>
      <div class="text-center">
        <div class="text-2xl font-bold text-red-600">{{ status.invalid }}</div>
        <div class="text-sm text-gray-600">Invalid</div>
      </div>
    </div>

    <div class="mt-4 flex justify-between text-sm text-gray-600">
      <span>Elapsed: {{ formatTime(elapsedTime) }}</span>
      <span>Remaining: ~{{ formatTime(estimatedRemaining) }}</span>
    </div>
  </div>
</template>
```

#### Step 3: Create ChannelResultsGrid Component

```vue
<!-- frontend/src/components/streamTest/ChannelResultsGrid.vue -->

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { Channel } from '@/types/channel'

interface Props {
  channels: Channel[]
}

const props = defineProps<Props>()

const activeFilter = ref<'all' | 'valid' | 'invalid'>('all')
const activeResolution = ref<string | null>(null)

const filteredChannels = computed(() => {
  let result = props.channels

  // Apply status filter
  if (activeFilter.value === 'valid') {
    result = result.filter(ch => ch.is_online)
  } else if (activeFilter.value === 'invalid') {
    result = result.filter(ch => !ch.is_online)
  }

  // Apply resolution filter
  if (activeResolution.value) {
    result = result.filter(ch => ch.resolution === activeResolution.value)
  }

  return result
})

const setFilter = (filter: 'all' | 'valid' | 'invalid') => {
  activeFilter.value = filter
}

const setResolution = (resolution: string | null) => {
  activeResolution.value = activeResolution.value === resolution ? null : resolution
}
</script>

<template>
  <div>
    <!-- Filter Bar -->
    <div class="card mb-6">
      <div class="flex gap-4 flex-wrap">
        <button
          @click="setFilter('all')"
          :class="['filter-btn', { 'active': activeFilter === 'all' }]"
        >
          All
        </button>
        <button
          @click="setFilter('valid')"
          :class="['filter-btn', { 'active': activeFilter === 'valid' }]"
        >
          Valid Only
        </button>
        <button
          @click="setFilter('invalid')"
          :class="['filter-btn', { 'active': activeFilter === 'invalid' }]"
        >
          Invalid Only
        </button>

        <div class="w-px bg-gray-300" />

        <button
          @click="setResolution('4K')"
          :class="['filter-btn', { 'active': activeResolution === '4K' }]"
        >
          4K
        </button>
        <button
          @click="setResolution('1080p')"
          :class="['filter-btn', { 'active': activeResolution === '1080p' }]"
        >
          1080p
        </button>
        <button
          @click="setResolution('720p')"
          :class="['filter-btn', { 'active': activeResolution === '720p' }]"
        >
          720p
        </button>
      </div>
    </div>

    <!-- Results Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <div
        v-for="channel in filteredChannels"
        :key="channel.id"
        class="card hover:shadow-lg transition-shadow"
      >
        <div class="relative">
          <img
            :src="channel.screenshot_path
              ? `/api/screenshots/${channel.screenshot_path.split('/').pop()}`
              : '/placeholder.png'"
            :alt="channel.name"
            class="w-full h-48 object-cover rounded"
            loading="lazy"
          />
          <span
            :class="[
              'absolute top-2 right-2 px-2 py-1 rounded text-sm font-medium',
              channel.is_online ? 'bg-green-500 text-white' : 'bg-red-500 text-white'
            ]"
          >
            {{ channel.is_online ? 'Valid' : 'Invalid' }}
          </span>
        </div>

        <div class="mt-3">
          <h3 class="font-semibold truncate">
            {{ channel.name || channel.url }}
          </h3>
          <div class="mt-2 flex justify-between text-sm text-gray-600">
            <span>{{ channel.resolution || 'Unknown' }}</span>
            <span>{{ channel.codec_video || 'N/A' }}</span>
          </div>
        </div>
      </div>
    </div>

    <div v-if="filteredChannels.length === 0" class="text-center py-12 text-gray-500">
      No channels match the current filter
    </div>
  </div>
</template>

<style scoped>
.filter-btn {
  @apply px-4 py-2 rounded border border-gray-300 hover:bg-gray-100 transition-colors;
}

.filter-btn.active {
  @apply bg-blue-500 text-white border-blue-500;
}
</style>
```

#### Step 4: Create Main StreamTest View

```vue
<!-- frontend/src/views/StreamTest.vue -->

<script setup lang="ts">
import { ref, onUnmounted } from 'vue'
import ScanConfigForm from '@/components/streamTest/ScanConfigForm.vue'
import ScanProgress from '@/components/streamTest/ScanProgress.vue'
import ChannelResultsGrid from '@/components/streamTest/ChannelResultsGrid.vue'
import Toast from '@/components/common/Toast.vue'
import api from '@/api/client'
import type { Channel } from '@/types/channel'

interface ScanStatus {
  scan_id: string
  status: 'pending' | 'running' | 'completed' | 'cancelled'
  total: number
  completed: number
  valid: number
  invalid: number
  channels: Channel[]
}

const scanId = ref<string | null>(null)
const isScanning = ref(false)
const scanProgress = ref<ScanStatus>({
  scan_id: '',
  status: 'pending',
  total: 0,
  completed: 0,
  valid: 0,
  invalid: 0,
  channels: []
})

const elapsedTime = ref(0)
let pollInterval: NodeJS.Timeout | null = null
let timerInterval: NodeJS.Timeout | null = null

const handleScanStart = async (config: any) => {
  try {
    const response = await api.scan.start(config)
    scanId.value = response.scan_id
    isScanning.value = true

    startPolling()
    startTimer()

    showToast('Scan started successfully', 'success')
  } catch (error: any) {
    showToast(`Failed to start scan: ${error.message}`, 'error')
  }
}

const startPolling = () => {
  pollInterval = setInterval(async () => {
    if (!scanId.value) return

    try {
      const status = await api.scan.getStatus(scanId.value)
      scanProgress.value = status

      if (status.status === 'completed' || status.status === 'cancelled') {
        stopPolling()
      }
    } catch (error) {
      console.error('Polling error:', error)
    }
  }, 1000)
}

const stopPolling = () => {
  if (pollInterval) {
    clearInterval(pollInterval)
    pollInterval = null
  }
  if (timerInterval) {
    clearInterval(timerInterval)
    timerInterval = null
  }
  isScanning.value = false
}

const startTimer = () => {
  elapsedTime.value = 0
  timerInterval = setInterval(() => {
    elapsedTime.value++
  }, 1000)
}

const handleCancelScan = async () => {
  if (!scanId.value) return

  try {
    await api.scan.cancel(scanId.value)
    stopPolling()
    showToast('Scan cancelled', 'info')
  } catch (error: any) {
    showToast(`Failed to cancel scan: ${error.message}`, 'error')
  }
}

const toastMessage = ref('')
const toastType = ref<'success' | 'error' | 'info' | 'warning'>('info')
const showToastFlag = ref(false)

const showToast = (message: string, type: 'success' | 'error' | 'info' | 'warning') => {
  toastMessage.value = message
  toastType.value = type
  showToastFlag.value = true

  setTimeout(() => {
    showToastFlag.value = false
  }, 3000)
}

onUnmounted(() => {
  stopPolling()
})
</script>

<template>
  <div class="stream-test-container">
    <h1 class="text-3xl font-bold mb-6">Stream Test</h1>

    <ScanConfigForm
      :is-scanning="isScanning"
      @scan-start="handleScanStart"
    />

    <ScanProgress
      v-if="isScanning"
      :status="scanProgress"
      :elapsed-time="elapsedTime"
      @cancel="handleCancelScan"
      class="mt-6"
    />

    <ChannelResultsGrid
      v-if="scanProgress.channels.length > 0"
      :channels="scanProgress.channels"
      class="mt-6"
    />

    <Toast
      v-if="showToastFlag"
      :message="toastMessage"
      :type="toastType"
    />
  </div>
</template>
```

#### Step 5: Create Toast Component

```vue
<!-- frontend/src/components/common/Toast.vue -->

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  message: string
  type: 'success' | 'error' | 'info' | 'warning'
}

const props = defineProps<Props>()

const bgColor = computed(() => {
  const colors = {
    success: 'bg-green-500',
    error: 'bg-red-500',
    info: 'bg-blue-500',
    warning: 'bg-yellow-500'
  }
  return colors[props.type]
})
</script>

<template>
  <div
    :class="['fixed top-4 right-4 px-6 py-3 rounded shadow-lg text-white z-50', bgColor]"
  >
    {{ message }}
  </div>
</template>
```

### Verification Criteria

**Unit Tests:**

- [ ] ScanConfigForm validation tests pass
- [ ] StreamTest polling lifecycle tests pass
- [ ] ChannelResultsGrid filter tests pass
- [ ] Component test coverage >80%

**Integration Tests (E2E with Playwright):**

- [ ] Full scan workflow: configure → start → progress → results
- [ ] Cancel scan midway
- [ ] Filter results by status and resolution
- [ ] Click screenshot thumbnail (prepare for Task 7.3 lightbox)

**Manual Testing:**

- [ ] Form validation displays errors correctly
- [ ] Progress bar animates smoothly
- [ ] Polling stops when scan completes
- [ ] Results grid updates in real-time
- [ ] Filters work correctly
- [ ] Toast notifications display and auto-dismiss
- [ ] Responsive layout on mobile/tablet/desktop

**Code Quality:**

- [ ] `npm run type-check` passes (no TypeScript errors)
- [ ] `npm run lint` passes
- [ ] No console errors in browser DevTools
- [ ] Vuelidate validation rules working correctly

## Notes

- **HTTP Polling vs WebSocket**: Initial implementation uses HTTP polling (simpler). Consider WebSocket upgrade in Task 7.6 for production.
- **Large Channel Lists**: For scans with >1000 channels, consider implementing virtual scrolling in ChannelResultsGrid (use `vue-virtual-scroller` library).
- **Screenshot Loading**: Uses lazy loading (`loading="lazy"`) for performance. Placeholder image required at `/public/placeholder.png`.
- **State Management**: Current implementation uses component-local state. For complex scenarios, consider Pinia store in Task 7.6.

## Dependencies

Add to `frontend/package.json`:

```json
{
  "dependencies": {
    "@vuelidate/core": "^2.0.3",
    "@vuelidate/validators": "^2.0.4"
  },
  "devDependencies": {
    "@vue/test-utils": "^2.4.6",
    "vitest": "^1.6.0"
  }
}
```

Install:

```bash
cd frontend
npm install
```
