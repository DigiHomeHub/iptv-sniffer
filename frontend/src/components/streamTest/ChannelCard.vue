<script setup lang="ts">
import { computed, ref } from "vue";

import ImageLightbox from "@/components/common/ImageLightbox.vue";
import type { Channel } from "@/types/channel";

defineOptions({ name: "ChannelCard" });

const props = defineProps<{
  channel: Channel;
}>();

const lightboxOpen = ref(false);

const placeholderImage =
  "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='640' height='360' viewBox='0 0 640 360'%3E%3Crect width='640' height='360' fill='%23e2e8f0'/%3E%3Ctext x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' fill='%2394a3b8' font-size='24'%3ENo Screenshot%3C/text%3E%3C/svg%3E";

const screenshotUrl = computed(() => {
  const path = props.channel.screenshot_path;
  if (!path) {
    return placeholderImage;
  }
  const filename = path.split("/").pop();
  return filename ? `/api/screenshots/${filename}` : placeholderImage;
});

function openLightbox() {
  if (props.channel.screenshot_path) {
    lightboxOpen.value = true;
  }
}

function closeLightbox() {
  lightboxOpen.value = false;
}
</script>

<template>
  <article
    class="group card space-y-3 transition-shadow hover:shadow-lg"
  >
    <div
      class="relative flex cursor-pointer items-center justify-center overflow-hidden rounded-lg"
      @click="openLightbox"
    >
      <img
        :src="screenshotUrl"
        :alt="channel.name ?? channel.url"
        class="h-48 w-full object-cover"
        loading="lazy"
      />
      <div class="absolute inset-0 flex items-center justify-center bg-black/0 transition-colors group-hover:bg-black/20">
        <svg
          class="h-10 w-10 text-white opacity-0 transition-opacity group-hover:opacity-100"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </div>
      <span
        :class="[
          'absolute right-2 top-2 rounded-full px-3 py-1 text-xs font-semibold text-white shadow',
          channel.is_online ? 'bg-green-500' : 'bg-red-500',
        ]"
      >
        {{ channel.is_online ? "Valid" : "Invalid" }}
      </span>
    </div>

    <div class="space-y-2">
      <h3 class="truncate text-lg font-semibold text-slate-900">
        {{ channel.name || channel.url }}
      </h3>
      <div class="flex justify-between text-sm text-slate-600">
        <span>{{ channel.resolution ?? "Unknown" }}</span>
        <span>{{ channel.codec_video ?? "?" }}</span>
      </div>
    </div>

    <ImageLightbox
      :is-open="lightboxOpen"
      :image-url="screenshotUrl"
      :alt-text="channel.name ?? channel.url"
      @close="closeLightbox"
    />
  </article>
</template>
