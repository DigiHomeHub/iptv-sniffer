<script setup lang="ts">
defineProps<{
  selectedCount: number;
}>();

const emit = defineEmits<{
  (e: "delete"): void;
}>();
</script>

<template>
  <div class="card flex flex-wrap items-center justify-between gap-3 border border-blue-200 bg-blue-50/60">
    <div class="text-sm text-slate-700">
      {{ selectedCount }} channel(s) selected
    </div>
    <div class="flex gap-2">
      <button type="button" class="btn-danger" @click="emit('delete')">
        Delete Selected
      </button>
      <button type="button" class="btn-secondary" disabled>
        Validate (coming soon)
      </button>
      <button type="button" class="btn-secondary" disabled>
        Export to M3U (coming soon)
      </button>
    </div>
  </div>
</template>
