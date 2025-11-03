<script setup lang="ts">
import { computed } from "vue";

const description = computed(
  () =>
    "Validate IPTV streams one channel at a time. Configure protocol, timeout, and advanced FFmpeg options.",
);
</script>

<template>
  <section class="space-y-4">
    <header>
      <h2 class="text-2xl font-semibold text-slate-900">Stream Test</h2>
      <p class="mt-1 text-sm text-slate-600">
        {{ description }}
      </p>
    </header>

    <div class="rounded-xl border border-dashed border-slate-300 bg-white p-6 text-sm text-slate-500">
      <p>
        Stream testing UI coming in Task 7.2. This page will let you run quick validation checks on individual
        channels before adding them to your playlist.
      </p>
    </div>
  </section>
</template>
