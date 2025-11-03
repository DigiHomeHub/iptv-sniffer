<script setup lang="ts">
import { computed } from "vue";

defineOptions({ name: "ScanProgress" });

interface ScanStatusSummary {
  total: number;
  completed: number;
  valid: number;
  invalid: number;
}

const props = defineProps<{
  status: ScanStatusSummary;
  elapsedTime: number;
}>();

const emit = defineEmits<{
  (e: "cancel"): void;
}>();

const percentage = computed(() => {
  if (!props.status.total) {
    return 0;
  }
  return Math.min(100, Math.round((props.status.completed / props.status.total) * 100));
});

const formatTime = (seconds: number) => {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${secs.toString().padStart(2, "0")}`;
};

const estimatedRemaining = computed(() => {
  if (!props.status.completed || props.status.completed >= props.status.total) {
    return 0;
  }
  const averagePerChannel = props.elapsedTime / props.status.completed;
  const remaining = props.status.total - props.status.completed;
  return Math.round(averagePerChannel * remaining);
});
</script>

<template>
  <div class="card space-y-5">
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-xl font-semibold text-slate-900">Scan Progress</h2>
        <p class="text-sm text-slate-600">
          Monitoring validation status across the configured IP range.
        </p>
      </div>
      <button type="button" class="btn-secondary" @click="emit('cancel')">
        Cancel Scan
      </button>
    </div>

    <div>
      <div class="progress-container">
        <div
          class="progress-bar"
          :style="{ width: `${percentage}%` }"
        />
      </div>
      <div class="mt-2 text-right text-sm font-medium text-slate-600">
        {{ percentage }}% Complete
      </div>
    </div>

    <div class="grid gap-4 rounded-lg bg-slate-50 p-4 md:grid-cols-4">
      <div class="text-center">
        <div class="text-2xl font-semibold text-slate-900">
          {{ status.total }}
        </div>
        <div class="text-xs uppercase tracking-wide text-slate-500">
          Total Targets
        </div>
      </div>
      <div class="text-center">
        <div class="text-2xl font-semibold text-slate-900">
          {{ status.completed }}
        </div>
        <div class="text-xs uppercase tracking-wide text-slate-500">
          Completed
        </div>
      </div>
      <div class="text-center">
        <div class="text-2xl font-semibold text-green-600">
          {{ status.valid }}
        </div>
        <div class="text-xs uppercase tracking-wide text-slate-500">
          Valid
        </div>
      </div>
      <div class="text-center">
        <div class="text-2xl font-semibold text-red-600">
          {{ status.invalid }}
        </div>
        <div class="text-xs uppercase tracking-wide text-slate-500">
          Invalid
        </div>
      </div>
    </div>

    <div class="flex flex-wrap justify-between text-sm text-slate-600">
      <span>Elapsed: {{ formatTime(elapsedTime) }}</span>
      <span>Est. remaining: {{ formatTime(estimatedRemaining) }}</span>
    </div>
  </div>
</template>
