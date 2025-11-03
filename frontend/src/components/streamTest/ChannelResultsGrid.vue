<script setup lang="ts">
import { computed, ref } from "vue";

import ChannelCard from "@/components/streamTest/ChannelCard.vue";
import type { Channel } from "@/types/channel";

defineOptions({ name: "ChannelResultsGrid" });

const props = defineProps<{
  channels: Channel[];
}>();

const statusFilter = ref<"all" | "valid" | "invalid">("all");
const resolutionFilter = ref<string | null>(null);

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
      <ChannelCard
        v-for="channel in filteredChannels"
        :key="channel.id"
        :channel="channel"
      />
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
