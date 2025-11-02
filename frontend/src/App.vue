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

    <main class="mx-auto max-w-4xl px-6 py-10">
      <section class="card space-y-4">
        <h2 class="text-xl font-semibold text-slate-900">Frontend Setup</h2>
        <p class="text-slate-600">
          Vue 3 + Vite application scaffolded with Tailwind CSS and Headless UI.
          This shell will host the network scan dashboard and channel management
          workflows.
        </p>
        <div class="grid gap-4 md:grid-cols-2">
          <div class="rounded-lg border border-slate-200 p-4">
            <h3 class="text-sm font-semibold uppercase tracking-wide text-slate-500">
              Tech Stack
            </h3>
            <ul class="mt-2 space-y-1 text-sm text-slate-600">
              <li>Vue 3 + TypeScript</li>
              <li>Vite with Hot Module Replacement</li>
              <li>Tailwind CSS utility styling</li>
              <li>Headless UI components</li>
            </ul>
          </div>
          <div class="rounded-lg border border-slate-200 p-4">
            <h3 class="text-sm font-semibold uppercase tracking-wide text-slate-500">
              Next Steps
            </h3>
            <ul class="mt-2 space-y-1 text-sm text-slate-600">
              <li>Integrate scan API for live progress</li>
              <li>Implement preset selection UI</li>
              <li>Visualize channel validation results</li>
              <li>Provide download/export workflows</li>
            </ul>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>
