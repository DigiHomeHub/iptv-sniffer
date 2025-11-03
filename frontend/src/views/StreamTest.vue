<script setup lang="ts">
import { onUnmounted, ref } from "vue";

import ToastMessage from "@/components/common/Toast.vue";
import ChannelResultsGrid from "@/components/streamTest/ChannelResultsGrid.vue";
import ScanConfigForm from "@/components/streamTest/ScanConfigForm.vue";
import ScanProgress from "@/components/streamTest/ScanProgress.vue";
import { config } from "@/config";
import { scanAPI, type ScanStartRequest } from "@/api/scan";
import type { Channel } from "@/types/channel";

defineOptions({ name: "StreamTest" });

type ScanStatus = "pending" | "running" | "completed" | "cancelled" | "failed";

interface ScanProgressState {
  scan_id: string;
  status: ScanStatus;
  total: number;
  completed: number;
  valid: number;
  invalid: number;
}

const scanId = ref<string | null>(null);
const isScanning = ref(false);
const isPolling = ref(false);
const elapsedTime = ref(0);
const channels = ref<Channel[]>([]);
const scanProgress = ref<ScanProgressState>({
  scan_id: "",
  status: "pending",
  total: 0,
  completed: 0,
  valid: 0,
  invalid: 0,
});

const toastVisible = ref(false);
const toastMessage = ref("");
const toastType = ref<"success" | "error" | "info" | "warning">("info");

let pollTimer: ReturnType<typeof setInterval> | null = null;
let elapsedTimer: ReturnType<typeof setInterval> | null = null;

function showToast(message: string, type: "success" | "error" | "info" | "warning") {
  toastMessage.value = message;
  toastType.value = type;
  toastVisible.value = true;
  setTimeout(() => {
    toastVisible.value = false;
  }, 3000);
}

async function handleScanStart(payload: ScanStartRequest) {
  try {
    const response = await scanAPI.start(payload);
    scanId.value = response.scan_id;
    scanProgress.value = {
      scan_id: response.scan_id,
      status: response.status as ScanStatus,
      total: response.total ?? 0,
      completed: 0,
      valid: 0,
      invalid: 0,
    };
    channels.value = [];
    isScanning.value = true;

    startTimers();
    startPolling();
    showToast("Scan started successfully", "success");
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : "Failed to start scan";
    showToast(message, "error");
  }
}

function startTimers() {
  elapsedTime.value = 0;
  if (!elapsedTimer) {
    elapsedTimer = setInterval(() => {
      elapsedTime.value += 1;
    }, 1000);
  }
}

function stopTimers() {
  if (elapsedTimer) {
    clearInterval(elapsedTimer);
    elapsedTimer = null;
  }
}

function startPolling() {
  if (isPolling.value || !scanId.value) {
    return;
  }
  isPolling.value = true;
  pollTimer = setInterval(fetchStatusUpdate, config.pollInterval);
  fetchStatusUpdate();
}

async function fetchStatusUpdate() {
  if (!scanId.value) {
    return;
  }

  try {
    const status = await scanAPI.getStatus(scanId.value);
    scanProgress.value = {
      scan_id: status.scan_id,
      status: status.status as ScanStatus,
      total: status.total,
      completed: status.progress,
      valid: status.valid,
      invalid: status.invalid,
    };
    channels.value = Array.isArray(status.channels) ? status.channels : channels.value;

    if (status.status === "completed") {
      showToast("Scan completed", "success");
      stopPolling();
    } else if (status.status === "cancelled") {
      showToast("Scan cancelled", "info");
      stopPolling();
    }
  } catch (error) {
    console.error("Failed to poll scan status", error);
    showToast("Lost connection to scan service", "error");
    stopPolling();
  }
}

async function handleCancelScan() {
  if (!scanId.value) {
    return;
  }
  try {
    await scanAPI.cancel(scanId.value);
    stopPolling();
    showToast("Cancel request sent", "info");
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : "Failed to cancel scan";
    showToast(message, "error");
  }
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer);
    pollTimer = null;
  }
  stopTimers();
  isPolling.value = false;
  isScanning.value = false;
}

onUnmounted(() => {
  stopPolling();
});

defineExpose({
  startPolling,
  stopPolling,
  scanId,
  isPolling,
  scanProgress,
});
</script>

<template>
  <div class="space-y-6">
    <header>
      <h1 class="text-3xl font-bold text-slate-900">Stream Test</h1>
      <p class="mt-1 text-sm text-slate-600">
        Validate IPTV streams in real time. Configure an IP sweep and monitor the scan results as channels are tested.
      </p>
    </header>

    <ScanConfigForm :is-scanning="isScanning" @scan-start="handleScanStart" />

    <ScanProgress
      v-if="isScanning || isPolling"
      class="mt-6"
      :status="scanProgress"
      :elapsed-time="elapsedTime"
      @cancel="handleCancelScan"
    />

    <ChannelResultsGrid
      v-if="channels.length"
      class="mt-6"
      :channels="channels"
    />

    <ToastMessage
      v-if="toastVisible"
      :message="toastMessage"
      :type="toastType"
    />
  </div>
</template>
