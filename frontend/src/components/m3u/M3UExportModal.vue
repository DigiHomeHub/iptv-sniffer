<script setup lang="ts">
import { reactive, watch } from "vue";
import { Dialog, DialogPanel, DialogTitle } from "@headlessui/vue";

import m3uAPI from "@/api/m3u";

defineOptions({ name: "M3UExportModal" });

const props = defineProps<{
  isOpen: boolean;
}>();

const emit = defineEmits<{
  (e: "close"): void;
}>();

const filters = reactive({
  group: "",
  resolution: "",
  status: "",
});

function resetFilters() {
  filters.group = "";
  filters.resolution = "";
  filters.status = "";
}

function close() {
  emit("close");
}

watch(
  () => props.isOpen,
  (isOpen) => {
    if (!isOpen) {
      resetFilters();
    }
  },
);

function handleExport() {
  m3uAPI.export({
    group: filters.group || undefined,
    resolution: filters.resolution || undefined,
    status: filters.status || undefined,
  });
  close();
}

function handleCancel() {
  close();
}
</script>

<template>
  <Dialog :open="isOpen" @close="close" class="relative z-50">
    <div class="fixed inset-0 bg-black/40" />
    <div class="fixed inset-0 flex items-center justify-center p-4">
      <DialogPanel class="w-full max-w-md rounded-xl bg-white p-6 shadow-xl">
        <DialogTitle class="text-xl font-semibold text-slate-900">
          Export M3U Playlist
        </DialogTitle>

        <div class="mt-4 space-y-4">
          <div>
            <label class="input-label" for="export-group">Group (optional)</label>
            <input
              id="export-group"
              v-model="filters.group"
              class="input-field"
              type="text"
              placeholder="e.g. 央视"
            />
          </div>

          <div>
            <label class="input-label" for="export-resolution">Resolution (optional)</label>
            <select id="export-resolution" v-model="filters.resolution" class="input-field">
              <option value="">All</option>
              <option value="4K">4K</option>
              <option value="1080p">1080p</option>
              <option value="720p">720p</option>
            </select>
          </div>

          <div>
            <label class="input-label" for="export-status">Status (optional)</label>
            <select id="export-status" v-model="filters.status" class="input-field">
              <option value="">All</option>
              <option value="online">Online only</option>
              <option value="offline">Offline only</option>
            </select>
          </div>
        </div>

        <div class="mt-6 flex justify-end gap-3">
          <button type="button" class="btn-secondary" @click="handleCancel">
            Cancel
          </button>
          <button type="button" class="btn-primary" @click="handleExport">
            Export M3U
          </button>
        </div>
      </DialogPanel>
    </div>
  </Dialog>
</template>
