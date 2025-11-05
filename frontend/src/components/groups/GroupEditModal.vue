<script setup lang="ts">
import { Dialog, DialogPanel, TransitionChild, TransitionRoot } from "@headlessui/vue";
import { ref, watch } from "vue";

const props = defineProps<{
  groupName: string;
}>();

const emit = defineEmits<{
  (e: "save", groupName: string, newName: string): void;
  (e: "close"): void;
}>();

const newName = ref(props.groupName);

watch(
  () => props.groupName,
  (value) => {
    newName.value = value;
  },
);

function handleSave() {
  const trimmed = newName.value.trim();
  if (!trimmed || trimmed === props.groupName) {
    return;
  }
  emit("save", props.groupName, trimmed);
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
            <DialogPanel class="w-full max-w-md transform overflow-hidden rounded-xl bg-white p-6 shadow-xl">
              <header class="mb-4">
                <Dialog.Title class="text-lg font-semibold text-slate-900">Rename Group</Dialog.Title>
                <p class="mt-1 text-sm text-slate-600">
                  Update the group name. All channels assigned to this group will reflect the new name.
                </p>
              </header>

              <div class="space-y-4">
                <div>
                  <label class="input-label" for="group-name">Group name</label>
                  <input
                    id="group-name"
                    v-model="newName"
                    class="input-field"
                    type="text"
                    placeholder="Enter new name"
                  />
                </div>
              </div>

              <footer class="mt-6 flex justify-end gap-3">
                <button type="button" class="btn-secondary" @click="emit('close')">
                  Cancel
                </button>
                <button type="button" class="btn-primary" :disabled="!newName.trim()" @click="handleSave">
                  Save Changes
                </button>
              </footer>
            </DialogPanel>
          </TransitionChild>
        </div>
      </div>
    </Dialog>
  </TransitionRoot>
</template>
