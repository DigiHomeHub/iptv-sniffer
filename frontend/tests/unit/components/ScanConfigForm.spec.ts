import { mount, flushPromises } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import ScanConfigForm from "@/components/streamTest/ScanConfigForm.vue";

describe("ScanConfigForm", () => {
  it("renders form inputs", () => {
    const wrapper = mount(ScanConfigForm);

    expect(wrapper.find('input[name="baseUrl"]').exists()).toBe(true);
    expect(wrapper.find('input[name="startIp"]').exists()).toBe(true);
    expect(wrapper.find('input[name="endIp"]').exists()).toBe(true);
    expect(wrapper.find('button[type="submit"]').exists()).toBe(true);
  });

  it("validates IP address format", async () => {
    const wrapper = mount(ScanConfigForm);

    await wrapper.find('input[name="startIp"]').setValue("invalid-ip");
    await wrapper.find('input[name="endIp"]').setValue("192.168.1.10");
    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(wrapper.text()).toContain("Invalid IP address");
  });

  it("emits scan-start with valid configuration", async () => {
    const wrapper = mount(ScanConfigForm);

    await wrapper.find('input[name="baseUrl"]').setValue("http://192.168.2.2:7788/rtp/{ip}:8000");
    await wrapper.find('input[name="startIp"]').setValue("192.168.1.1");
    await wrapper.find('input[name="endIp"]').setValue("192.168.1.10");
    await wrapper.find("form").trigger("submit");
    await flushPromises();

    const events = wrapper.emitted("scan-start");
    expect(events).toBeTruthy();
    expect(events?.[0]).toEqual([
      {
        mode: "template",
        base_url: "http://192.168.2.2:7788/rtp/{ip}:8000",
        start_ip: "192.168.1.1",
        end_ip: "192.168.1.10",
      },
    ]);
  });

  it("disables form controls while scanning", () => {
    const wrapper = mount(ScanConfigForm, {
      props: {
        isScanning: true,
      },
    });

    expect(wrapper.find('button[type="submit"]').attributes("disabled")).toBeDefined();
    expect(wrapper.find('input[name="startIp"]').attributes("disabled")).toBeDefined();
  });
});
