<script setup lang="ts">
import { computed } from "vue";

defineOptions({ name: "ToastMessage" });

const props = defineProps<{
  message: string;
  type: "success" | "error" | "info" | "warning";
}>();

const colorClass = computed(() => {
  switch (props.type) {
    case "success":
      return "bg-green-500";
    case "error":
      return "bg-red-500";
    case "warning":
      return "bg-amber-500";
    default:
      return "bg-blue-500";
  }
});
</script>

<template>
  <div
    :class="[
      'fixed right-4 top-4 z-50 flex max-w-sm items-center gap-3 rounded-lg px-4 py-3 text-sm font-medium text-white shadow-lg',
      colorClass,
    ]"
    role="status"
  >
    <span>{{ message }}</span>
  </div>
</template>
