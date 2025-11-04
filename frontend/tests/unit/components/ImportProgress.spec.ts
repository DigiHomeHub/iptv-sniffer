import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";

import ImportProgress from "@/components/m3u/ImportProgress.vue";

describe("ImportProgress", () => {
  const baseResult = {
    imported: 8,
    failed: 2,
    channels: [],
    errors: [],
  };

  it("renders channel statistics and success rate", () => {
    const wrapper = mount(ImportProgress, {
      props: {
        result: baseResult,
      },
    });

    expect(wrapper.text()).toContain("Total channels");
    expect(wrapper.text()).toContain("Imported");
    expect(wrapper.text()).toContain("Failed");
    expect(wrapper.text()).toContain("80%");
  });

  it("renders errors when provided", () => {
    const wrapper = mount(ImportProgress, {
      props: {
        result: {
          ...baseResult,
          errors: ["Channel A: invalid URL"],
        },
      },
    });

    expect(wrapper.text()).toContain("Channel A: invalid URL");
  });

  it("emits reset and view-channels events", async () => {
    const wrapper = mount(ImportProgress, {
      props: {
        result: baseResult,
      },
    });

    await wrapper.get("button.btn-secondary").trigger("click");
    await wrapper.get("button.btn-primary").trigger("click");

    expect(wrapper.emitted("reset")).toBeTruthy();
    expect(wrapper.emitted("view-channels")).toBeTruthy();
  });
});
