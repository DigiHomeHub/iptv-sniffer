<script setup lang="ts">
import { onBeforeUnmount, watch } from "vue";
import { Dialog, DialogPanel, TransitionChild, TransitionRoot } from "@headlessui/vue";

defineOptions({ name: "ImageLightbox" });

const props = withDefaults(
  defineProps<{
    isOpen: boolean;
    imageUrl: string;
    altText?: string;
  }>(),
  {
    altText: "Screenshot",
  },
);

const emit = defineEmits<{
  (e: "close"): void;
}>();

function handleClose() {
  emit("close");
}

function onKeyDown(event: KeyboardEvent) {
  if (event.key === "Escape") {
    handleClose();
  }
}

watch(
  () => props.isOpen,
  (open) => {
    if (typeof window === "undefined") {
      return;
    }
    if (open) {
      window.addEventListener("keydown", onKeyDown);
    } else {
      window.removeEventListener("keydown", onKeyDown);
    }
  },
  { immediate: true },
);

onBeforeUnmount(() => {
  if (typeof window !== "undefined") {
    window.removeEventListener("keydown", onKeyDown);
  }
});
</script>

<template>
  <TransitionRoot :show="isOpen" as="template">
    <Dialog as="div" class="relative z-50" @close="handleClose">
      <TransitionChild
        as="template"
        enter="ease-out duration-300"
        enter-from="opacity-0"
        enter-to="opacity-100"
        leave="ease-in duration-200"
        leave-from="opacity-100"
        leave-to="opacity-0"
      >
        <div class="fixed inset-0 bg-black/80" />
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
            <DialogPanel class="relative max-w-6xl transform overflow-hidden rounded-lg bg-black">
              <button
                type="button"
                aria-label="Close"
                class="absolute right-4 top-4 rounded-full bg-black/60 p-2 text-white transition hover:bg-black/80"
                @click="handleClose"
              >
                <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>

              <img
                :src="imageUrl"
                :alt="altText"
                class="max-h-[90vh] w-auto object-contain"
                loading="lazy"
              />
            </DialogPanel>
          </TransitionChild>
        </div>
      </div>
    </Dialog>
  </TransitionRoot>
</template>
