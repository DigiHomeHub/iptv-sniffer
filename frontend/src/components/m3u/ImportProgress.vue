<script setup lang="ts">
import { computed } from "vue";

import type { M3UImportResult } from "@/api/m3u";

defineOptions({ name: "ImportProgress" });

const props = defineProps<{
  result: M3UImportResult;
}>();

const emit = defineEmits<{
  (e: "reset"): void;
  (e: "view-channels"): void;
}>();

const successRate = computed(() => {
  const total = props.result.imported + props.result.failed;
  return total === 0 ? 0 : Math.round((props.result.imported / total) * 100);
});
</script>

<template>
  <div class="card space-y-6">
    <div class="text-center">
      <svg
        v-if="result.failed === 0"
        class="mx-auto h-16 w-16 text-green-500"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <svg
        v-else
        class="mx-auto h-16 w-16 text-amber-500"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      </svg>
      <h2 class="mt-4 text-2xl font-semibold text-slate-900">
        Import {{ result.failed === 0 ? "Complete" : "Finished with warnings" }}
      </h2>
    </div>

    <div class="grid gap-4 sm:grid-cols-3">
      <div class="rounded-lg bg-slate-50 p-4 text-center">
        <p class="text-3xl font-bold text-slate-900">
          {{ result.imported + result.failed }}
        </p>
        <p class="text-sm text-slate-600">Total channels</p>
      </div>
      <div class="rounded-lg bg-slate-50 p-4 text-center">
        <p class="text-3xl font-bold text-green-600">
          {{ result.imported }}
        </p>
        <p class="text-sm text-slate-600">Imported</p>
      </div>
      <div class="rounded-lg bg-slate-50 p-4 text-center">
        <p class="text-3xl font-bold text-red-500">
          {{ result.failed }}
        </p>
        <p class="text-sm text-slate-600">Failed</p>
      </div>
    </div>

    <div>
      <div class="flex justify-between text-sm text-slate-600">
        <span>Success rate</span>
        <span>{{ successRate }}%</span>
      </div>
      <div class="mt-1 h-2 rounded-full bg-slate-200">
        <div
          class="h-full rounded-full transition-all"
          :class="successRate === 100 ? 'bg-green-500' : 'bg-amber-500'"
          :style="{ width: `${successRate}%` }"
        />
      </div>
    </div>

    <div v-if="result.errors.length" class="space-y-2">
      <h3 class="text-sm font-semibold text-red-600">Errors</h3>
      <ul class="max-h-32 space-y-1 overflow-y-auto text-sm text-slate-600">
        <li v-for="(error, index) in result.errors" :key="index">
          {{ error }}
        </li>
      </ul>
    </div>

    <div class="flex flex-wrap justify-center gap-3">
      <button type="button" class="btn-secondary" @click="emit('reset')">
        Import another file
      </button>
      <button type="button" class="btn-primary" @click="emit('view-channels')">
        View channels
      </button>
    </div>
  </div>
</template>
