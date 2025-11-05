<script setup lang="ts">
import { computed, ref } from "vue";

import type { GroupStatistics } from "@/api/groups";

interface Props {
  group: GroupStatistics;
  isSelected: boolean;
}

const props = defineProps<Props>();
const emit = defineEmits<{
  (e: "toggle-selection", groupName: string): void;
  (e: "view-channels", groupName: string): void;
  (e: "edit", groupName: string): void;
  (e: "delete", groupName: string): void;
  (e: "channel-drop", payload: { groupName: string; channelId: string }): void;
}>();

const isDropTarget = ref(false);

const onlineBadgeClass = computed(() => {
  const pct = props.group.online_percentage ?? 0;
  if (pct >= 80) return "bg-green-100 text-green-700";
  if (pct >= 50) return "bg-amber-100 text-amber-700";
  return "bg-rose-100 text-rose-700";
});

function handleDragOver(event: DragEvent) {
  event.preventDefault();
  isDropTarget.value = true;
}

function handleDragLeave() {
  isDropTarget.value = false;
}

function handleDrop(event: DragEvent) {
  event.preventDefault();
  isDropTarget.value = false;
  const channelId = event.dataTransfer?.getData("text/channel-id");
  if (!channelId) {
    return;
  }
  emit("channel-drop", { groupName: props.group.name, channelId });
}
</script>

<template>
  <div
    :class="[
      'card transition-shadow',
      isSelected ? 'ring-2 ring-blue-500' : 'hover:shadow-lg',
      isDropTarget ? 'border-blue-500 border-2' : 'border-transparent',
    ]"
    @click="emit('toggle-selection', group.name)"
    @dragover="handleDragOver"
    @dragleave="handleDragLeave"
    @drop="handleDrop"
  >
    <div class="flex items-start justify-between gap-2">
      <div class="flex items-center gap-2">
        <input
          type="checkbox"
          :checked="isSelected"
          class="h-4 w-4 text-blue-600"
          @click.stop="emit('toggle-selection', group.name)"
        />
        <h3 class="text-lg font-semibold text-slate-900">
          {{ group.name }}
        </h3>
      </div>
      <span
        :class="['rounded-full px-2 py-1 text-xs font-medium', onlineBadgeClass]"
        title="Online channel percentage"
      >
        {{ group.online_percentage }}%
      </span>
    </div>

    <div class="mt-4 grid grid-cols-3 gap-4 text-center text-sm">
      <div>
        <div class="text-2xl font-semibold text-slate-900">{{ group.total }}</div>
        <span class="text-xs text-slate-500">Total</span>
      </div>
      <div>
        <div class="text-2xl font-semibold text-emerald-600">{{ group.online }}</div>
        <span class="text-xs text-slate-500">Online</span>
      </div>
      <div>
        <div class="text-2xl font-semibold text-rose-600">{{ group.offline }}</div>
        <span class="text-xs text-slate-500">Offline</span>
      </div>
    </div>

    <div class="mt-6 flex gap-2" @click.stop>
      <button type="button" class="btn-secondary flex-1 text-sm" @click="emit('view-channels', group.name)">
        View Channels
      </button>
      <button type="button" class="btn-secondary text-sm" @click="emit('edit', group.name)">
        Edit
      </button>
      <button type="button" class="btn-danger text-sm" @click="emit('delete', group.name)">
        Delete
      </button>
    </div>
  </div>
</template>
