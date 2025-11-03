<script setup lang="ts">
import type { Channel } from "@/types/channel";

const props = defineProps<{
  channels: Channel[];
  isLoading: boolean;
  selected: Set<string>;
}>();

const emit = defineEmits<{
  (e: "edit", channel: Channel): void;
  (e: "delete", channelId: string): void;
  (e: "selection-change", selection: Set<string>): void;
}>();

function toggleSelection(channelId: string) {
  const updated = new Set(props.selected);
  if (updated.has(channelId)) {
    updated.delete(channelId);
  } else {
    updated.add(channelId);
  }
  emit("selection-change", updated);
}

function toggleSelectAll() {
  if (props.selected.size === props.channels.length) {
    emit("selection-change", new Set());
  } else {
    emit(
      "selection-change",
      new Set(props.channels.map((channel) => channel.id)),
    );
  }
}
</script>

<template>
  <div class="card overflow-x-auto">
    <table class="min-w-full divide-y divide-slate-200">
      <thead class="bg-slate-50">
        <tr>
          <th class="px-4 py-3 text-left">
            <input
              type="checkbox"
              :checked="selected.size === channels.length && channels.length > 0"
              @change="toggleSelectAll"
            />
          </th>
          <th class="px-4 py-3 text-left text-sm font-semibold text-slate-600">Name</th>
          <th class="px-4 py-3 text-left text-sm font-semibold text-slate-600">Group</th>
          <th class="px-4 py-3 text-left text-sm font-semibold text-slate-600">Resolution</th>
          <th class="px-4 py-3 text-left text-sm font-semibold text-slate-600">Status</th>
          <th class="px-4 py-3 text-right text-sm font-semibold text-slate-600">Actions</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-slate-200">
        <tr v-if="isLoading">
          <td colspan="6" class="px-4 py-8 text-center text-slate-500">
            Loading channels...
          </td>
        </tr>
        <tr v-else-if="channels.length === 0">
          <td colspan="6" class="px-4 py-8 text-center text-slate-500">
            No channels available
          </td>
        </tr>
        <tr
          v-for="channel in channels"
          :key="channel.id"
          :class="{ 'bg-blue-50': selected.has(channel.id) }"
        >
          <td class="px-4 py-3">
            <input
              type="checkbox"
              :checked="selected.has(channel.id)"
              @change="toggleSelection(channel.id)"
            />
          </td>
          <td class="px-4 py-3">
            <div class="flex items-center gap-2">
              <img
                v-if="channel.tvg_logo"
                :src="channel.tvg_logo"
                alt=""
                class="h-8 w-8 rounded object-cover"
              />
              <span class="font-medium text-slate-900">{{ channel.name || channel.url }}</span>
            </div>
          </td>
          <td class="px-4 py-3 text-sm text-slate-600">{{ channel.group || '-' }}</td>
          <td class="px-4 py-3 text-sm text-slate-600">{{ channel.resolution || 'Unknown' }}</td>
          <td class="px-4 py-3">
            <span
              :class="[
                'rounded-full px-2 py-1 text-xs font-semibold',
                channel.is_online ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700',
              ]"
            >
              {{ channel.is_online ? 'Online' : 'Offline' }}
            </span>
          </td>
          <td class="px-4 py-3 text-right">
            <button type="button" class="btn-secondary mr-2 text-sm" @click="emit('edit', channel)">
              Edit
            </button>
            <button type="button" class="btn-danger text-sm" @click="emit('delete', channel.id)">
              Delete
            </button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
