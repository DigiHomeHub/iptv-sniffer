import { flushPromises, mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/api/groups", () => ({
  groupsAPI: {
    list: vi.fn(),
    merge: vi.fn(),
    delete: vi.fn(),
    rename: vi.fn(),
  },
}));

vi.mock("@/api/channels", () => ({
  channelsAPI: {
    update: vi.fn(),
  },
}));

import GroupsView from "@/views/Groups.vue";
import { channelsAPI } from "@/api/channels";
import { groupsAPI } from "@/api/groups";

const listMock = vi.mocked(groupsAPI.list);
const mergeMock = vi.mocked(groupsAPI.merge);
const deleteMock = vi.mocked(groupsAPI.delete);
const renameMock = vi.mocked(groupsAPI.rename);
const updateChannelMock = vi.mocked(channelsAPI.update);

describe("GroupsView", () => {
  beforeEach(() => {
    listMock.mockReset();
    mergeMock.mockReset();
    deleteMock.mockReset();
    renameMock.mockReset();
    updateChannelMock.mockReset();

    listMock.mockResolvedValue({
      groups: [
        { name: "News", total: 3, online: 2, offline: 1, online_percentage: 66.7 },
        { name: "Sports", total: 2, online: 2, offline: 0, online_percentage: 100 },
      ],
      total_groups: 2,
    });
  });

  it("renders group cards from API", async () => {
    const wrapper = mount(GroupsView);
    await flushPromises();

    expect(listMock).toHaveBeenCalled();
    const text = wrapper.text();
    expect(text).toContain("News");
    expect(text).toContain("Sports");
  });

  it("handles channel drop to another group", async () => {
    const wrapper = mount(GroupsView);
    await flushPromises();

    const groupCard = wrapper.findComponent({
      name: "GroupCard",
    });

    groupCard.vm.$emit("channel-drop", { groupName: "Sports", channelId: "123" });
    await flushPromises();

    expect(updateChannelMock).toHaveBeenCalledWith("123", { group: "Sports" });
  });
});
