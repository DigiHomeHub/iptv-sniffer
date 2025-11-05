<script setup lang="ts">
import { Dialog, DialogPanel, TransitionChild, TransitionRoot } from "@headlessui/vue";
import { computed, ref, watch } from "vue";

import { channelsAPI } from "@/api/channels";
import { groupsAPI, type GroupChannelsResponse } from "@/api/groups";
import type { Channel } from "@/types/channel";

const props = defineProps<{
  groupName: string;
}>();

const emit = defineEmits<{
  (e: "close"): void;
  (e: "channels-updated"): void;
}>();

const channels = ref<Channel[]>([]);
const isLoading = ref(false);
const page = ref(1);
const pages = ref(1);
const PAGE_SIZE = 25;
const selected = ref<Set<string>>(new Set());
const moveTarget = ref<string>("");

const hasSelection = computed(() => selected.value.size > 0);
const isFirstPage = computed(() => page.value <= 1);
const isLastPage = computed(() => page.value >= pages.value);

async function fetchChannels() {
  isLoading.value = true;
  try {
    const response: GroupChannelsResponse = await groupsAPI.getChannels(props.groupName, page.value, PAGE_SIZE);
    channels.value = response.channels;
    pages.value = response.pages;
  } catch (error) {
    console.error("Failed to load channels", error);
  } finally {
    isLoading.value = false;
  }
}

function toggleSelection(channelId: string) {
  if (selected.value.has(channelId)) {
    selected.value.delete(channelId);
  } else {
    selected.value.add(channelId);
  }
}

function selectAll() {
  if (selected.value.size === channels.value.length) {
    selected.value.clear();
  } else {
    selected.value = new Set(channels.value.map((channel) => channel.id));
  }
}

async function moveSelectedChannels() {
  if (!hasSelection.value) {
    return;
  }
  const target = moveTarget.value.trim();
  const targetGroup = target === "" ? null : target;

  await Promise.all(
    Array.from(selected.value).map((channelId) =>
      channelsAPI.update(channelId, {
        group: targetGroup,
      }),
    ),
  );

  selected.value.clear();
  moveTarget.value = "";
  await fetchChannels();
  emit("channels-updated");
}

function handleDragStart(channel: Channel, event: DragEvent) {
  if (!event.dataTransfer) {
    return;
  }
  event.dataTransfer.setData("text/channel-id", channel.id);
  event.dataTransfer.setData("text/plain", channel.name ?? channel.url);
  event.dataTransfer.effectAllowed = "move";
}

function statusBadge(channel: Channel) {
  return channel.is_online ? "bg-emerald-100 text-emerald-700" : "bg-rose-100 text-rose-700";
}

function goToPage(nextPage: number) {
  if (nextPage === page.value || nextPage < 1 || nextPage > pages.value) {
    return;
  }
  page.value = nextPage;
  fetchChannels();
}

watch(
  () => props.groupName,
  () => {
    page.value = 1;
    fetchChannels();
  },
  { immediate: true },
);
</script>

<template>
  <TransitionRoot :show="true" as="template">
    <Dialog as="div" class="relative z-50" @close="emit('close')">
      <TransitionChild
        as="template"
        enter="ease-out duration-300"
        enter-from="opacity-0"
        enter-to="opacity-100"
        leave="ease-in duration-200"
        leave-from="opacity-100"
        leave-to="opacity-0"
      >
        <div class="fixed inset-0 bg-black/50" />
      </TransitionChild>

      <div class="fixed inset-0 overflow-y-auto">
        <div class="flex min-h-full items-center justify-center p-4">
          <TransitionChild
            as="template"
            enter="ease-out duration-300"
            enter-from="opacity-0 scale-95"
            enter-to="opacity-100 scale-100"
            leave="ease-in duration-200"
            leave-from="opacity-100 scale-100"
            leave-to="opacity-0 scale-95"
          >
            <DialogPanel class="w-full max-w-4xl transform overflow-hidden rounded-xl bg-white p-6 shadow-xl">
              <header class="mb-4 flex items-start justify-between">
                <div>
                  <Dialog.Title class="text-xl font-semibold text-slate-900">
                    Channels in {{ groupName }}
                  </Dialog.Title>
                  <p class="mt-1 text-sm text-slate-600">
                    Drag a channel onto a group card to reassign, or batch move using the controls below.
                  </p>
                </div>
                <button type="button" class="btn-secondary" @click="emit('close')">
                  Close
                </button>
              </header>

              <section class="mb-4 flex flex-wrap items-center gap-3">
                <button type="button" class="btn-secondary btn-sm" @click="selectAll">
                  {{ selected.size === channels.length ? "Clear Selection" : "Select All" }}
                </button>
                <div class="flex items-center gap-2">
                  <label class="text-sm text-slate-600" for="move-target">Move selected to</label>
                  <input
                    id="move-target"
                    v-model="moveTarget"
                    type="text"
                    placeholder="Target group"
                    class="input-field"
                  />
                  <button
                    type="button"
                    class="btn-primary btn-sm"
                    :disabled="!hasSelection"
                    @click="moveSelectedChannels"
                  >
                    Move ({{ selected.size }})
                  </button>
                </div>
              </section>

              <section class="max-h-[420px] space-y-3 overflow-y-auto">
                <div v-if="isLoading" class="flex justify-center py-10">
                  <div class="h-10 w-10 animate-spin rounded-full border-4 border-blue-500 border-t-transparent" />
                </div>

                <template v-else>
                  <div
                    v-for="channel in channels"
                    :key="channel.id"
                    draggable="true"
                    class="flex items-center justify-between rounded-lg border border-slate-200 bg-white px-3 py-2 hover:border-blue-400"
                    @dragstart="handleDragStart(channel, $event)"
                  >
                    <div class="flex items-center gap-3">
                      <input
                        type="checkbox"
                        :checked="selected.has(channel.id)"
                        @change="toggleSelection(channel.id)"
                      />
                      <div>
                        <p class="text-sm font-medium text-slate-900">
                          {{ channel.name ?? channel.url }}
                        </p>
                        <p class="text-xs text-slate-500">{{ channel.url }}</p>
                      </div>
                    </div>
                    <span :class="['rounded-full px-2 py-1 text-xs font-medium', statusBadge(channel)]">
                      {{ channel.is_online ? "Online" : "Offline" }}
                    </span>
                  </div>

                  <div v-if="channels.length === 0" class="py-10 text-center text-sm text-slate-500">
                    No channels in this group.
                  </div>
                </template>
              </section>

              <footer class="mt-4 flex items-center justify-between text-sm text-slate-600">
                <span>Page {{ page }} / {{ pages }}</span>
                <div class="flex items-center gap-2">
                  <button type="button" class="btn-secondary btn-sm" :disabled="isFirstPage" @click="goToPage(page - 1)">
                    Previous
                  </button>
                  <button
                    type="button"
                    class="btn-secondary btn-sm"
                    :disabled="isLastPage"
                    @click="goToPage(page + 1)"
                  >
                    Next
                  </button>
                </div>
              </footer>
            </DialogPanel>
          </TransitionChild>
        </div>
      </div>
    </Dialog>
  </TransitionRoot>
</template>
