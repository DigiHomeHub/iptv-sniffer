<script setup lang="ts">
import { Tab, TabGroup, TabList } from "@headlessui/vue";
import { computed } from "vue";
import { RouterLink, RouterView, useRoute, useRouter } from "vue-router";

interface TabItem {
  label: string;
  description: string;
  route: string;
}

const tabs: TabItem[] = [
  {
    label: "Stream Test",
    description: "Validate IPTV streams individually before adding them to playlists.",
    route: "/stream-test",
  },
  {
    label: "TV Channels",
    description: "Manage discovered channels, validation status, and export options.",
    route: "/channels",
  },
  {
    label: "TV Groups",
    description: "Organize channels into logical groups and presets.",
    route: "/groups",
  },
  {
    label: "Advanced Settings",
    description: "Configure scan strategies, FFmpeg options, and persistence.",
    route: "/settings",
  },
];

const route = useRoute();
const router = useRouter();

const selectedIndex = computed(() => {
  const index = tabs.findIndex((tab) => route.path.startsWith(tab.route));
  return index >= 0 ? index : 0;
});

const currentDescription = computed(() => tabs[selectedIndex.value]?.description ?? "");

function tabClasses(isActive: boolean) {
  return [
    "w-full rounded-lg px-4 py-2 text-sm font-medium transition focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2",
    isActive
      ? "bg-primary-600 text-white shadow focus-visible:ring-primary-500"
      : "text-slate-600 hover:bg-slate-100 focus-visible:ring-primary-500",
  ];
}

function onTabChange(index: number) {
  const tab = tabs[index];
  if (tab && route.path !== tab.route) {
    router.push(tab.route);
  }
}
</script>

<template>
  <div class="min-h-screen bg-slate-100">
    <header class="border-b border-slate-200 bg-white">
      <div class="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <div>
          <h1 class="text-2xl font-semibold text-slate-900">iptv-sniffer</h1>
          <p class="text-sm text-slate-500">
            Discover and validate IPTV channels on your local network.
          </p>
        </div>
        <div class="space-x-3">
          <a
            class="btn-secondary"
            href="https://github.com/thsrite/iptv-sniff"
            target="_blank"
            rel="noreferrer"
          >
            Reference Project
          </a>
          <a
            class="btn-primary"
            href="https://github.com/bytedance/iptv-sniffer"
            target="_blank"
            rel="noreferrer"
          >
            View Repository
          </a>
        </div>
      </div>
    </header>

    <main class="mx-auto max-w-5xl px-6 py-10">
<TabGroup :selectedIndex="selectedIndex" @change="onTabChange">
  <TabList class="flex flex-wrap gap-3 rounded-xl bg-white p-4 shadow-sm">
    <Tab
      v-for="tab in tabs"
      :key="tab.route"
      as="template"
      v-slot="{ selected }"
    >
      <RouterLink :to="tab.route" :class="tabClasses(selected)">
        {{ tab.label }}
      </RouterLink>
    </Tab>
  </TabList>
</TabGroup>

      <p class="mt-4 text-sm text-slate-600">
        {{ currentDescription }}
      </p>

      <section class="mt-6">
        <RouterView />
      </section>
    </main>
  </div>
</template>
