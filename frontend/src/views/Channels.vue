<script setup lang="ts">
import { onMounted, ref } from "vue";

import BatchActionBar from "@/components/channels/BatchActionBar.vue";
import ChannelEditModal from "@/components/channels/ChannelEditModal.vue";
import ChannelTable from "@/components/channels/ChannelTable.vue";
import M3UExportModal from "@/components/m3u/M3UExportModal.vue";
import M3UImport from "@/components/m3u/M3UImport.vue";
import { channelsAPI, type ChannelListResponse } from "@/api/channels";
import type { M3UImportResult } from "@/api/m3u";
import type { Channel } from "@/types/channel";

const channels = ref<Channel[]>([]);
const total = ref(0);
const currentPage = ref(1);
const totalPages = ref(1);
const isLoading = ref(false);
const selectedChannels = ref<Set<string>>(new Set());
const showEditModal = ref(false);
const editingChannel = ref<Channel | null>(null);
const showExportModal = ref(false);

const filters = ref({
  search: "",
  group: "",
  resolution: "",
  status: "",
});

async function fetchChannels() {
  isLoading.value = true;
  try {
    const response: ChannelListResponse = await channelsAPI.list({
      page: currentPage.value,
      page_size: 50,
      ...filters.value,
    });
    channels.value = response.channels;
    total.value = response.total;
    currentPage.value = response.page;
    totalPages.value = response.pages;
  } catch (error) {
    console.error("Failed to fetch channels", error);
  } finally {
    isLoading.value = false;
  }
}

function handleFilterChange() {
  currentPage.value = 1;
  fetchChannels();
}

function handlePageChange(page: number) {
  currentPage.value = page;
  fetchChannels();
}

function handleEdit(channel: Channel) {
  editingChannel.value = { ...channel };
  showEditModal.value = true;
}

async function handleSaveChannel(updated: Channel) {
  if (!editingChannel.value) {
    return;
  }
  try {
    await channelsAPI.update(updated.id, {
      name: updated.name,
      group: updated.group,
      resolution: updated.resolution,
      tvg_id: updated.tvg_id,
      tvg_logo: updated.tvg_logo,
    });
    showEditModal.value = false;
    await fetchChannels();
  } catch (error) {
    console.error("Failed to update channel", error);
  }
}

async function handleDeleteChannel(channelId: string) {
  if (!confirm("Delete this channel?")) {
    return;
  }
  try {
    await channelsAPI.delete(channelId);
    selectedChannels.value.delete(channelId);
    await fetchChannels();
  } catch (error) {
    console.error("Failed to delete channel", error);
  }
}

async function handleBatchDelete() {
  if (selectedChannels.value.size === 0) {
    return;
  }
  if (!confirm(`Delete ${selectedChannels.value.size} channel(s)?`)) {
    return;
  }
  try {
    await Promise.all(Array.from(selectedChannels.value).map((id) => channelsAPI.delete(id)));
    selectedChannels.value.clear();
    await fetchChannels();
  } catch (error) {
    console.error("Failed to delete channels", error);
  }
}

function handleSelectionChange(selection: Set<string>) {
  selectedChannels.value = selection;
}

async function handleImportComplete(result: M3UImportResult) {
  if (result.imported > 0) {
    await fetchChannels();
  }
}

onMounted(() => {
  fetchChannels();
});
</script>

<template>
  <div class="space-y-6">
    <header>
      <h1 class="text-3xl font-bold text-slate-900">TV Channels</h1>
      <p class="mt-2 text-sm text-slate-600">
        Browse, filter, and manage discovered IPTV channels. Edit channel metadata, delete stale entries, and trigger
        validations.
      </p>
    </header>

    <section class="card space-y-4">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 class="text-lg font-semibold text-slate-900">Import Playlist</h2>
          <p class="text-sm text-slate-600">
            Drag and drop an M3U/M3U8 file to merge channels into your library.
          </p>
        </div>
        <div class="flex gap-2">
          <button type="button" class="btn-secondary" @click="fetchChannels">
            Refresh
          </button>
          <button type="button" class="btn-primary" @click="showExportModal = true">
            Export M3U
          </button>
        </div>
      </div>

      <M3UImport @import-complete="handleImportComplete" />
    </section>

    <section class="card space-y-3">
      <div class="grid gap-3 md:grid-cols-4">
        <input
          v-model="filters.search"
          class="input-field"
          type="text"
          placeholder="Search channel name or URL"
          @input="handleFilterChange"
        />
        <select v-model="filters.group" class="input-field" @change="handleFilterChange">
          <option value="">All groups</option>
          <option value="央视">央视</option>
          <option value="卫视">卫视</option>
          <option value="影视">影视</option>
        </select>
        <select v-model="filters.resolution" class="input-field" @change="handleFilterChange">
          <option value="">All resolutions</option>
          <option value="4K">4K</option>
          <option value="1080p">1080p</option>
          <option value="720p">720p</option>
        </select>
        <select v-model="filters.status" class="input-field" @change="handleFilterChange">
          <option value="">All status</option>
          <option value="online">Online</option>
          <option value="offline">Offline</option>
        </select>
      </div>
    </section>

    <BatchActionBar
      v-if="selectedChannels.size > 0"
      :selected-count="selectedChannels.size"
      @delete="handleBatchDelete"
    />

    <ChannelTable
      :channels="channels"
      :is-loading="isLoading"
      :selected="selectedChannels"
      @edit="handleEdit"
      @delete="handleDeleteChannel"
      @selection-change="handleSelectionChange"
    />

    <div class="flex items-center justify-between">
      <p class="text-sm text-slate-600">
        Showing {{ channels.length }} of {{ total }} channels
      </p>
      <div class="flex gap-2">
        <button
          type="button"
          class="btn-secondary"
          :disabled="currentPage === 1"
          @click="handlePageChange(currentPage - 1)"
        >
          Previous
        </button>
        <span class="px-4 py-2 text-sm text-slate-600">
          Page {{ currentPage }} / {{ totalPages }}
        </span>
        <button
          type="button"
          class="btn-secondary"
          :disabled="currentPage === totalPages"
          @click="handlePageChange(currentPage + 1)"
        >
          Next
        </button>
      </div>
    </div>

    <ChannelEditModal
      v-if="showEditModal && editingChannel"
      :channel="editingChannel"
      @save="handleSaveChannel"
      @close="showEditModal = false"
    />

    <M3UExportModal :is-open="showExportModal" @close="showExportModal = false" />
  </div>
</template>
