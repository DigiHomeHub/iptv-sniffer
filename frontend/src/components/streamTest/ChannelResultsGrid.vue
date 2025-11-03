<script setup lang="ts">
import { computed, ref } from "vue";

import type { Channel } from "@/types/channel";

defineOptions({ name: "ChannelResultsGrid" });

const props = defineProps<{
  channels: Channel[];
}>();

const statusFilter = ref<"all" | "valid" | "invalid">("all");
const resolutionFilter = ref<string | null>(null);

const placeholderImage =
  "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='640' height='360' viewBox='0 0 640 360'%3E%3Crect width='640' height='360' fill='%23e2e8f0'/%3E%3Ctext x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' fill='%2394a3b8' font-size='24'%3ENo Preview%3C/text%3E%3C/svg%3E";

const filteredChannels = computed(() => {
  let list = [...props.channels];

  if (statusFilter.value === "valid") {
    list = list.filter((channel) => channel.is_online);
  } else if (statusFilter.value === "invalid") {
    list = list.filter((channel) => !channel.is_online);
  }

  if (resolutionFilter.value) {
    list = list.filter((channel) => channel.resolution === resolutionFilter.value);
  }

  return list;
});

function setStatusFilter(filter: "all" | "valid" | "invalid") {
  statusFilter.value = filter;
}

function toggleResolutionFilter(resolution: string) {
  resolutionFilter.value = resolutionFilter.value === resolution ? null : resolution;
}
</script>

<template>
  <div class="space-y-6">
    <div class="card flex flex-wrap items-center gap-3">
      <button
        type="button"
        :class="['filter-btn', { active: statusFilter === 'all' }]"
        @click="setStatusFilter('all')"
      >
        All
      </button>
      <button
        type="button"
        :class="['filter-btn', { active: statusFilter === 'valid' }]"
        @click="setStatusFilter('valid')"
      >
        Valid Only
      </button>
      <button
        type="button"
        :class="['filter-btn', { active: statusFilter === 'invalid' }]"
        @click="setStatusFilter('invalid')"
      >
        Invalid Only
      </button>

      <span class="mx-2 hidden h-5 w-px bg-slate-300 md:block" aria-hidden="true" />

      <button
        type="button"
        :class="['filter-btn', { active: resolutionFilter === '4K' }]"
        @click="toggleResolutionFilter('4K')"
      >
        4K
      </button>
      <button
        type="button"
        :class="['filter-btn', { active: resolutionFilter === '1080p' }]"
        @click="toggleResolutionFilter('1080p')"
      >
        1080p
      </button>
      <button
        type="button"
        :class="['filter-btn', { active: resolutionFilter === '720p' }]"
        @click="toggleResolutionFilter('720p')"
      >
        720p
      </button>
    </div>

    <div
      v-if="filteredChannels.length === 0"
      class="rounded-xl border border-dashed border-slate-300 bg-white py-12 text-center text-slate-500"
    >
      No channels match the current filters.
    </div>

    <div
      v-else
      class="grid gap-5 sm:grid-cols-2 xl:grid-cols-3"
    >
      <article
        v-for="channel in filteredChannels"
        :key="channel.id"
        class="card space-y-3 transition-shadow hover:shadow-lg"
      >
        <div class="relative overflow-hidden rounded-lg">
          <img
            :src="channel.screenshot_path ? channel.screenshot_path : placeholderImage"
            :alt="channel.name ?? channel.url"
            class="h-44 w-full object-cover"
            loading="lazy"
          />
          <span
            :class="[
              'absolute right-2 top-2 rounded-full px-3 py-1 text-xs font-semibold',
              channel.is_online ? 'bg-green-500 text-white' : 'bg-red-500 text-white',
            ]"
          >
            {{ channel.is_online ? "Valid" : "Invalid" }}
          </span>
        </div>

        <div class="space-y-2">
          <h3 class="truncate text-lg font-semibold text-slate-900">
            {{ channel.name || channel.url }}
          </h3>

          <div class="flex justify-between text-sm text-slate-600">
            <span>{{ channel.resolution ?? "Unknown resolution" }}</span>
            <span>{{ channel.codec_video ?? "?" }}</span>
          </div>
        </div>
      </article>
    </div>
  </div>
</template>

<style scoped>
.filter-btn {
  @apply rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2;
}

.filter-btn.active {
  @apply border-primary-500 bg-primary-600 text-white;
}
</style>
