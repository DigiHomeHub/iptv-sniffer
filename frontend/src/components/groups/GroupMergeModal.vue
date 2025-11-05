<script setup lang="ts">
import { Dialog, DialogPanel, TransitionChild, TransitionRoot } from "@headlessui/vue";
import { computed, ref } from "vue";

const props = defineProps<{
  sourceGroups: string[];
}>();

const emit = defineEmits<{
  (e: "merge", sourceGroups: string[], targetGroup: string): void;
  (e: "close"): void;
}>();

const targetGroup = ref("");

const canSubmit = computed(() => targetGroup.value.trim().length > 0 && props.sourceGroups.length >= 2);

function handleSubmit() {
  if (!canSubmit.value) {
    return;
  }
  emit("merge", props.sourceGroups, targetGroup.value.trim());
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
        <div class="fixed inset-0 bg-black/40" />
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
            <DialogPanel class="w-full max-w-lg transform overflow-hidden rounded-xl bg-white p-6 shadow-xl">
              <header class="mb-4">
                <Dialog.Title class="text-lg font-semibold text-slate-900">Merge Groups</Dialog.Title>
                <p class="mt-1 text-sm text-slate-600">
                  Selected groups will be combined into a single target group. Channel metadata remains unchanged.
                </p>
              </header>

              <section class="space-y-4">
                <div>
                  <p class="text-sm font-medium text-slate-700">Groups to merge</p>
                  <ul class="mt-2 list-disc pl-5 text-sm text-slate-600">
                    <li v-for="group in sourceGroups" :key="group">
                      {{ group }}
                    </li>
                  </ul>
                </div>

                <div>
                  <label class="input-label" for="merge-target">Target group name</label>
                  <input
                    id="merge-target"
                    v-model="targetGroup"
                    class="input-field"
                    placeholder="e.g. 综合频道"
                    type="text"
                  />
                </div>
              </section>

              <footer class="mt-6 flex justify-end gap-3">
                <button type="button" class="btn-secondary" @click="emit('close')">
                  Cancel
                </button>
                <button type="button" class="btn-primary" :disabled="!canSubmit" @click="handleSubmit">
                  Merge Groups
                </button>
              </footer>
            </DialogPanel>
          </TransitionChild>
        </div>
      </div>
    </Dialog>
  </TransitionRoot>
</template>
