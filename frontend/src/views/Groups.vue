<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { channelsAPI } from "@/api/channels";
import { groupsAPI, type GroupStatistics } from "@/api/groups";
import GroupCard from "@/components/groups/GroupCard.vue";
import GroupChannelsModal from "@/components/groups/GroupChannelsModal.vue";
import GroupEditModal from "@/components/groups/GroupEditModal.vue";
import GroupMergeModal from "@/components/groups/GroupMergeModal.vue";

const groups = ref<GroupStatistics[]>([]);
const isLoading = ref(false);
const selectedGroups = ref<Set<string>>(new Set());
const viewingGroup = ref<string | null>(null);
const editingGroup = ref<string | null>(null);
const showMergeModal = ref(false);

const hasSelection = computed(() => selectedGroups.value.size > 0);
const canMerge = computed(() => selectedGroups.value.size >= 2);
const totalChannels = computed(() => groups.value.reduce((sum, group) => sum + group.total, 0));

async function fetchGroups() {
  isLoading.value = true;
  try {
    const response = await groupsAPI.list();
    groups.value = response.groups;
  } catch (error) {
    console.error("Failed to load groups", error);
  } finally {
    isLoading.value = false;
  }
}

function toggleSelection(groupName: string) {
  if (selectedGroups.value.has(groupName)) {
    selectedGroups.value.delete(groupName);
  } else {
    selectedGroups.value.add(groupName);
  }
}

function handleViewChannels(groupName: string) {
  viewingGroup.value = groupName;
}

function handleEditGroup(groupName: string) {
  if (groupName === "Uncategorized") {
    alert("The Uncategorized group cannot be renamed.");
    return;
  }
  editingGroup.value = groupName;
}

async function handleRenameGroup(groupName: string, newName: string) {
  try {
    await groupsAPI.rename(groupName, newName);
    editingGroup.value = null;
    await fetchGroups();
  } catch (error) {
    console.error("Failed to rename group", error);
  }
}

async function handleDeleteGroup(groupName: string) {
  if (groupName === "Uncategorized") {
    alert("The Uncategorized group cannot be deleted.");
    return;
  }
  if (!confirm(`Delete group "${groupName}"? Channels will move to Uncategorized.`)) {
    return;
  }
  try {
    await groupsAPI.delete(groupName);
    selectedGroups.value.delete(groupName);
    await fetchGroups();
  } catch (error) {
    console.error("Failed to delete group", error);
  }
}

async function handleMergeGroups(sourceGroups: string[], targetGroup: string) {
  try {
    await groupsAPI.merge(sourceGroups, targetGroup);
    showMergeModal.value = false;
    selectedGroups.value.clear();
    await fetchGroups();
  } catch (error) {
    console.error("Failed to merge groups", error);
  }
}

async function handleChannelDrop(payload: { groupName: string; channelId: string }) {
  try {
    const target = payload.groupName === "Uncategorized" ? null : payload.groupName;
    await channelsAPI.update(payload.channelId, { group: target });
    await fetchGroups();
  } catch (error) {
    console.error("Failed to move channel", error);
  }
}

function closeChannelsModal() {
  viewingGroup.value = null;
}

onMounted(fetchGroups);
</script>

<template>
  <div class="space-y-6">
    <header class="space-y-2">
      <h1 class="text-3xl font-bold text-slate-900">TV Groups</h1>
      <p class="text-sm text-slate-600">
        Organize channels into logical groups (genres, providers, favorites). Drag channels onto another group or use
        batch tools to keep your library tidy.
      </p>
    </header>

    <section class="card flex flex-wrap items-center justify-between gap-3">
      <div class="text-sm text-slate-600">
        {{ groups.length }} groups &bull; {{ totalChannels }} channels
      </div>
      <div class="flex flex-wrap gap-2">
        <button
          v-if="hasSelection"
          type="button"
          class="btn-secondary"
          @click="selectedGroups.clear()"
        >
          Clear Selection ({{ selectedGroups.size }})
        </button>
        <button
          v-if="canMerge"
          type="button"
          class="btn-primary"
          @click="showMergeModal = true"
        >
          Merge Selected
        </button>
        <button type="button" class="btn-secondary" @click="fetchGroups">
          Refresh
        </button>
      </div>
    </section>

    <div v-if="isLoading" class="flex items-center justify-center py-12">
      <div class="h-12 w-12 animate-spin rounded-full border-4 border-blue-500 border-t-transparent" />
    </div>

    <div v-else-if="groups.length === 0" class="card py-12 text-center text-sm text-slate-500">
      No groups yet. Import a playlist or run a scan to populate channels.
    </div>

    <div v-else class="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
      <GroupCard
        v-for="group in groups"
        :key="group.name"
        :group="group"
        :is-selected="selectedGroups.has(group.name)"
        @toggle-selection="toggleSelection"
        @view-channels="handleViewChannels"
        @edit="handleEditGroup"
        @delete="handleDeleteGroup"
        @channel-drop="handleChannelDrop"
      />
    </div>

    <GroupChannelsModal
      v-if="viewingGroup"
      :group-name="viewingGroup"
      @close="closeChannelsModal"
      @channels-updated="fetchGroups"
    />

    <GroupEditModal
      v-if="editingGroup"
      :group-name="editingGroup"
      @close="editingGroup = null"
      @save="handleRenameGroup"
    />

    <GroupMergeModal
      v-if="showMergeModal"
      :source-groups="Array.from(selectedGroups)"
      @close="showMergeModal = false"
      @merge="handleMergeGroups"
    />
  </div>
</template>
