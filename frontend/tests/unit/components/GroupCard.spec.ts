import { mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";

import GroupCard from "@/components/groups/GroupCard.vue";
import type { GroupStatistics } from "@/api/groups";

const baseGroup: GroupStatistics = {
  name: "News",
  total: 8,
  online: 6,
  offline: 2,
  online_percentage: 75,
};

describe("GroupCard", () => {
  it("emits toggle-selection when card clicked", async () => {
    const wrapper = mount(GroupCard, {
      props: {
        group: baseGroup,
        isSelected: false,
      },
    });

    await wrapper.trigger("click");
    expect(wrapper.emitted("toggle-selection")?.[0]).toEqual(["News"]);
  });

  it("emits view and edit actions", async () => {
    const wrapper = mount(GroupCard, {
      props: {
        group: baseGroup,
        isSelected: false,
      },
    });

    await wrapper.find("button.btn-secondary").trigger("click");
    expect(wrapper.emitted("view-channels")).toBeTruthy();

    await wrapper.findAll("button.btn-secondary")[1].trigger("click");
    expect(wrapper.emitted("edit")).toBeTruthy();
  });

  it("emits channel-drop with channel id", async () => {
    const channelId = "123";
    const wrapper = mount(GroupCard, {
      props: {
        group: baseGroup,
        isSelected: false,
      },
    });

    const dataTransfer = {
      data: new Map<string, string>([["text/channel-id", channelId]]),
      getData(key: string) {
        return this.data.get(key) ?? "";
      },
      setData: vi.fn(),
      dropEffect: "move",
    } as unknown as DataTransfer;

    await wrapper.trigger("dragover", { dataTransfer });
    await wrapper.trigger("drop", { dataTransfer });

    expect(wrapper.emitted("channel-drop")?.[0]).toEqual([{ groupName: "News", channelId }]);
  });
});
