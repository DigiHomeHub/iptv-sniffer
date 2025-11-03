<script setup lang="ts">
import { ref, watch } from "vue";
import { Dialog, DialogPanel, TransitionChild, TransitionRoot } from "@headlessui/vue";
import { useVuelidate } from "@vuelidate/core";
import { required } from "@vuelidate/validators";

import type { Channel } from "@/types/channel";

defineOptions({ name: "ChannelEditModal" });

const props = defineProps<{
  channel: Channel;
}>();

const emit = defineEmits<{
  (e: "save", channel: Channel): void;
  (e: "close"): void;
}>();

interface ChannelForm {
  name: string;
  group: string;
  resolution: string;
  tvg_id: string;
  tvg_logo: string;
}

const form = ref<ChannelForm>({
  name: props.channel.name ?? "",
  group: props.channel.group ?? "",
  resolution: props.channel.resolution ?? "",
  tvg_id: props.channel.tvg_id ?? "",
  tvg_logo: props.channel.tvg_logo ?? "",
});

watch(
  () => props.channel,
  (channel) => {
    form.value = {
      name: channel.name ?? "",
      group: channel.group ?? "",
      resolution: channel.resolution ?? "",
      tvg_id: channel.tvg_id ?? "",
      tvg_logo: channel.tvg_logo ?? "",
    };
    v$.value.$reset();
  },
);

const rules = {
  name: {
    required,
  },
  tvg_logo: {
    validUrl: (value: string) => {
      if (!value) {
        return true;
      }
      try {
        // eslint-disable-next-line no-new
        new URL(value);
        return true;
      } catch {
        return false;
      }
    },
  },
};

const v$ = useVuelidate(rules, form);

async function handleSubmit() {
  const valid = await v$.value.$validate();
  if (!valid) {
    return;
  }
  emit("save", {
    ...props.channel,
    name: form.value.name,
    group: form.value.group || undefined,
    resolution: form.value.resolution || undefined,
    tvg_id: form.value.tvg_id || undefined,
    tvg_logo: form.value.tvg_logo || undefined,
  });
}
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
            <DialogPanel class="w-full max-w-2xl transform overflow-hidden rounded-xl bg-white p-6 shadow-xl">
              <header class="mb-4 flex items-center justify-between">
                <Dialog.Title class="text-lg font-semibold text-slate-900">Edit Channel</Dialog.Title>
                <button type="button" class="btn-secondary" @click="emit('close')">
                  Close
                </button>
              </header>

              <form class="space-y-4" @submit.prevent="handleSubmit">
                <div>
                  <label class="input-label" for="channel-name">Name</label>
                  <input
                    id="channel-name"
                    v-model="form.name"
                    class="input-field"
                    type="text"
                  />
                  <p v-if="v$.name.$error" class="text-sm text-red-600">
                    Name is required
                  </p>
                </div>

                <div class="grid gap-4 md:grid-cols-2">
                  <div>
                    <label class="input-label" for="channel-group">Group</label>
                    <input
                      id="channel-group"
                      v-model="form.group"
                      class="input-field"
                      type="text"
                    />
                  </div>
                  <div>
                    <label class="input-label" for="channel-resolution">Resolution</label>
                    <input
                      id="channel-resolution"
                      v-model="form.resolution"
                      class="input-field"
                      type="text"
                    />
                  </div>
                </div>

                <div class="grid gap-4 md:grid-cols-2">
                  <div>
                    <label class="input-label" for="channel-logo">Logo URL</label>
                    <input
                      id="channel-logo"
                      v-model="form.tvg_logo"
                      class="input-field"
                      type="text"
                    />
                    <p v-if="v$.tvg_logo.$error" class="text-sm text-red-600">
                      Invalid logo URL
                    </p>
                  </div>
                  <div>
                    <label class="input-label" for="channel-tvg-id">TVG ID</label>
                    <input
                      id="channel-tvg-id"
                      v-model="form.tvg_id"
                      class="input-field"
                      type="text"
                    />
                  </div>
                </div>

                <div class="flex justify-end gap-3">
                  <button type="button" class="btn-secondary" @click="emit('close')">Cancel</button>
                  <button type="submit" class="btn-primary">Save Changes</button>
                </div>
              </form>
            </DialogPanel>
          </TransitionChild>
        </div>
      </div>
    </Dialog>
  </TransitionRoot>
</template>
