<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useVuelidate } from "@vuelidate/core";
import { helpers, required } from "@vuelidate/validators";

import type { ScanMode, ScanStartRequest } from "@/api/scan";

defineOptions({ name: "ScanConfigForm" });

const props = withDefaults(
  defineProps<{
    isScanning?: boolean;
  }>(),
  {
    isScanning: false,
  },
);

const emit = defineEmits<{
  (e: "scan-start", config: ScanStartRequest): void;
}>();

const defaultTemplateUrl = "http://192.168.2.2:7788/rtp/{ip}:8000";

type TemplateScanConfig = {
  mode: ScanMode;
  base_url: string;
  start_ip: string;
  end_ip: string;
};

const form = ref<TemplateScanConfig>({
  mode: "template",
  base_url: defaultTemplateUrl,
  start_ip: "",
  end_ip: "",
});

const ipRegex = /^(\d{1,3}\.){3}\d{1,3}$/;

const rules = computed(() => {
  const templateRules = {
    base_url: {
      required: helpers.withMessage("Base URL is required", required),
      containsPlaceholder: helpers.withMessage(
        "Base URL must contain {ip} placeholder",
        (value: string) => value?.includes("{ip}"),
      ),
    },
    start_ip: {
      required: helpers.withMessage("Start IP is required", required),
      valid: helpers.withMessage("Invalid IP address", (value: string) => ipRegex.test(value)),
    },
    end_ip: {
      required: helpers.withMessage("End IP is required", required),
      valid: helpers.withMessage("Invalid IP address", (value: string) => ipRegex.test(value)),
    },
  };

  if (form.value.mode === "template") {
    return templateRules;
  }

  // Provide minimal required validation for other modes (future tasks will extend).
  return {
    base_url: {},
    start_ip: {},
    end_ip: {},
  };
});

const v$ = useVuelidate(rules, form);

watch(
  () => form.value.mode,
  () => {
    v$.value.$reset();
  },
);

const isDisabled = computed(() => props.isScanning);

const handleSubmit = async () => {
  const valid = await v$.value.$validate();
  if (!valid) {
    return;
  }

  emit("scan-start", { ...form.value });
};
</script>

<template>
  <div class="card space-y-4">
    <div>
      <h2 class="text-xl font-semibold text-slate-900">Scan Configuration</h2>
      <p class="text-sm text-slate-600">
        Provide base stream URL template and IP range. Use the template mode to sweep a local subnet quickly.
      </p>
    </div>

    <form class="space-y-5" @submit.prevent="handleSubmit">
      <div>
        <label class="input-label" for="mode">Scan Mode</label>
        <select
          id="mode"
          name="mode"
          class="input-field"
          v-model="form.mode"
          :disabled="isDisabled"
        >
          <option value="template">Template Scan</option>
          <option value="multicast" disabled>Multicast Preset (coming soon)</option>
          <option value="preset" disabled>Provider Preset (coming soon)</option>
        </select>
      </div>

      <div>
        <label class="input-label" for="base-url">Base URL</label>
        <input
          id="base-url"
          name="baseUrl"
          type="text"
          class="input-field"
          :disabled="isDisabled"
          v-model="form.base_url"
          placeholder="http://192.168.2.2:7788/rtp/{ip}:8000"
        />
        <p v-if="v$.base_url?.$error" class="mt-1 text-sm text-red-600">
          {{ v$.base_url.$errors[0].$message }}
        </p>
      </div>

      <div class="grid gap-4 md:grid-cols-2">
        <div>
          <label class="input-label" for="start-ip">Start IP</label>
          <input
            id="start-ip"
            name="startIp"
            type="text"
            class="input-field"
            :disabled="isDisabled"
            v-model="form.start_ip"
            placeholder="192.168.1.1"
          />
          <p v-if="v$.start_ip?.$error" class="mt-1 text-sm text-red-600">
            {{ v$.start_ip.$errors[0].$message }}
          </p>
        </div>

        <div>
          <label class="input-label" for="end-ip">End IP</label>
          <input
            id="end-ip"
            name="endIp"
            type="text"
            class="input-field"
            :disabled="isDisabled"
            v-model="form.end_ip"
            placeholder="192.168.1.254"
          />
          <p v-if="v$.end_ip?.$error" class="mt-1 text-sm text-red-600">
            {{ v$.end_ip.$errors[0].$message }}
          </p>
        </div>
      </div>

      <div class="flex justify-end">
        <button type="submit" class="btn-primary" :disabled="isDisabled">
          {{ isDisabled ? "Scanning…" : "Start Test" }}
        </button>
      </div>
    </form>
  </div>
</template>
