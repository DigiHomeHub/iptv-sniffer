import { flushPromises, mount } from "@vue/test-utils";
import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";

import StreamTest from "@/views/StreamTest.vue";
import ScanConfigForm from "@/components/streamTest/ScanConfigForm.vue";

const apiMocks = vi.hoisted(() => {
  return {
    startMock: vi.fn(),
    getStatusMock: vi.fn(),
    cancelMock: vi.fn(),
  };
});

vi.mock("@/api/scan", () => ({
  scanAPI: {
    start: apiMocks.startMock,
    getStatus: apiMocks.getStatusMock,
    cancel: apiMocks.cancelMock,
  },
}));

describe("StreamTest view", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    apiMocks.startMock.mockReset();
    apiMocks.getStatusMock.mockReset();
    apiMocks.cancelMock.mockReset();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("starts scan and polls for progress", async () => {
    apiMocks.startMock.mockResolvedValue({
      scan_id: "scan-123",
      status: "pending",
      total: 10,
    });
    apiMocks.getStatusMock.mockResolvedValue({
      scan_id: "scan-123",
      status: "running",
      total: 10,
      progress: 5,
      valid: 3,
      invalid: 2,
      channels: [],
    });

    const wrapper = mount(StreamTest);
    const form = wrapper.findComponent(ScanConfigForm);

    form.vm.$emit("scan-start", {
      mode: "template",
      base_url: "http://192.168.2.2:7788/rtp/{ip}:8000",
      start_ip: "192.168.1.1",
      end_ip: "192.168.1.10",
    });
    await flushPromises();

    expect(apiMocks.startMock).toHaveBeenCalled();

    await vi.advanceTimersByTimeAsync(1100);
    await flushPromises();

    expect(apiMocks.getStatusMock).toHaveBeenCalled();
    const exposed: any = wrapper.vm;
    expect(exposed.scanProgress.completed).toBe(5);
  });

  it("stops polling when scan completes", async () => {
    apiMocks.startMock.mockResolvedValue({
      scan_id: "scan-abc",
      status: "pending",
      total: 4,
    });
    apiMocks.getStatusMock.mockResolvedValue({
      scan_id: "scan-abc",
      status: "completed",
      total: 4,
      progress: 4,
      valid: 4,
      invalid: 0,
      channels: [],
    });

    const wrapper = mount(StreamTest);
    const form = wrapper.findComponent(ScanConfigForm);
    form.vm.$emit("scan-start", {
      mode: "template",
      base_url: "http://192.168.2.2:7788/rtp/{ip}:8000",
      start_ip: "192.168.1.1",
      end_ip: "192.168.1.4",
    });
    await flushPromises();

    await vi.advanceTimersByTimeAsync(1100);
    await flushPromises();

    const progressComponent = wrapper.findComponent({ name: "ScanProgress" });
    expect(progressComponent.exists()).toBe(false);
  });
});
