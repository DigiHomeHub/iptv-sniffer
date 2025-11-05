import { flushPromises, mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@headlessui/vue", () => ({
  Dialog: {
    template: "<div><slot /></div>",
    props: ["open"],
  },
  DialogPanel: {
    template: "<div><slot /></div>",
  },
  TransitionRoot: {
    template: "<div><slot /></div>",
    props: ["show"],
  },
  TransitionChild: {
    template: "<div><slot /></div>",
  },
}));

vi.mock("@/api/channels", () => ({
  channelsAPI: {
    update: vi.fn(),
  },
}));

vi.mock("@/api/groups", () => ({
  groupsAPI: {
    getChannels: vi.fn(),
  },
}));

import GroupChannelsModal from "@/components/groups/GroupChannelsModal.vue";
import { channelsAPI } from "@/api/channels";
import { groupsAPI } from "@/api/groups";

const updateMock = vi.mocked(channelsAPI.update);
const getChannelsMock = vi.mocked(groupsAPI.getChannels);

describe("GroupChannelsModal", () => {
  beforeEach(() => {
    updateMock.mockReset();
    getChannelsMock.mockReset();
    getChannelsMock.mockResolvedValue({
      channels: [
        { id: "1", name: "Channel 1", url: "http://1", is_online: true, group: "News" },
        { id: "2", name: "Channel 2", url: "http://2", is_online: false, group: "News" },
      ],
      total: 2,
      page: 1,
      pages: 1,
    });
  });

  it("loads channels for group on mount", async () => {
    mount(GroupChannelsModal, {
      props: {
        groupName: "News",
      },
    });

    await flushPromises();
    expect(getChannelsMock).toHaveBeenCalledWith("News", 1, 25);
  });

  it("moves selected channels to new group", async () => {
    const wrapper = mount(GroupChannelsModal, {
      props: {
        groupName: "News",
      },
    });

    await flushPromises();
    await wrapper.findAll("input[type='checkbox']")[0].setValue(true);
    await wrapper.find("input#move-target").setValue("General");
    await wrapper.find("button.btn-primary").trigger("click");
    await flushPromises();

    expect(updateMock).toHaveBeenCalledWith("1", { group: "General" });
    expect(wrapper.emitted("channels-updated")).toBeTruthy();
  });
});
