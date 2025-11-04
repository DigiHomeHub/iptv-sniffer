<script setup lang="ts">
import { ref } from "vue";

import type { M3UImportResult } from "@/api/m3u";
import m3uAPI from "@/api/m3u";

import ImportProgress from "./ImportProgress.vue";

defineOptions({ name: "M3UImport" });

const isDragging = ref(false);
const isUploading = ref(false);
const importResult = ref<M3UImportResult | null>(null);

const emit = defineEmits<{
  (e: "import-complete", result: M3UImportResult): void;
}>();

function handleDragEnter(event: DragEvent) {
  event.preventDefault();
  isDragging.value = true;
}

function handleDragLeave(event: DragEvent) {
  event.preventDefault();
  isDragging.value = false;
}

function handleDragOver(event: DragEvent) {
  event.preventDefault();
}

async function handleDrop(event: DragEvent) {
  event.preventDefault();
  isDragging.value = false;
  const files = event.dataTransfer?.files;
  event.dataTransfer?.clearData();
  if (files && files.length > 0) {
    await uploadFile(files[0]);
  }
}

async function handleInput(event: Event) {
  const target = event.target as HTMLInputElement;
  if (target.files && target.files.length > 0) {
    await uploadFile(target.files[0]);
  }
  if (target) {
    target.value = "";
  }
}

async function uploadFile(file: File) {
  if (!file.name.toLowerCase().endsWith(".m3u") && !file.name.toLowerCase().endsWith(".m3u8")) {
    alert("Please upload a .m3u or .m3u8 file");
    return;
  }

  isUploading.value = true;
  importResult.value = null;

  try {
    const result = await m3uAPI.import(file);
    importResult.value = result;
    emit("import-complete", result);
  } catch (error) {
    const message = error instanceof Error ? error.message : "Playlist import failed";
    alert(message);
  } finally {
    isUploading.value = false;
  }
}

function resetImport() {
  importResult.value = null;
}
</script>

<template>
  <div class="space-y-4">
    <div
      v-if="!importResult"
      :class="[
        'rounded-xl border-2 border-dashed p-12 text-center transition-colors',
        isDragging ? 'border-primary-500 bg-primary-50' : 'border-slate-300 hover:border-slate-400',
      ]"
      @dragenter="handleDragEnter"
      @dragleave="handleDragLeave"
      @dragover="handleDragOver"
      @drop="handleDrop"
    >
      <svg class="mx-auto h-12 w-12 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 15l6-6 4 4 8-8" />
      </svg>
      <p class="mt-4 text-base font-medium text-slate-700">
        Drag & drop your M3U file here
      </p>
      <p class="text-sm text-slate-500">Supports .m3u and .m3u8 files with automatic encoding detection.</p>

      <div class="mt-6">
        <label class="btn-primary cursor-pointer" for="m3u-upload-input">
          Select File
          <input
            id="m3u-upload-input"
            type="file"
            class="hidden"
            accept=".m3u,.m3u8"
            @change="handleInput"
          />
        </label>
      </div>

      <div v-if="isUploading" class="mt-6 flex flex-col items-center gap-2 text-sm text-slate-600">
        <span class="flex h-10 w-10 animate-spin rounded-full border-4 border-primary-500 border-t-transparent" />
        Uploading and parsing playlist...
      </div>
    </div>

    <ImportProgress
      v-else
      :result="importResult"
      @reset="resetImport"
      @view-channels="$emit('import-complete', importResult!)"
    />
  </div>
</template>
