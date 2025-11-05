import { flushPromises, mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";

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

import GroupMergeModal from "@/components/groups/GroupMergeModal.vue";

describe("GroupMergeModal", () => {
  it("renders selected groups", () => {
    const wrapper = mount(GroupMergeModal, {
      props: {
        sourceGroups: ["News", "Sports"],
      },
    });

    expect(wrapper.text()).toContain("News");
    expect(wrapper.text()).toContain("Sports");
  });

  it("emits merge when form valid", async () => {
    const wrapper = mount(GroupMergeModal, {
      props: {
        sourceGroups: ["News", "Sports"],
      },
    });

    await wrapper.find("input").setValue("General");
    await wrapper.find("button.btn-primary").trigger("click");
    await flushPromises();

    expect(wrapper.emitted("merge")).toBeTruthy();
    expect(wrapper.emitted("merge")?.[0]).toEqual([["News", "Sports"], "General"]);
  });

  it("disables merge without target name", async () => {
    const wrapper = mount(GroupMergeModal, {
      props: {
        sourceGroups: ["News", "Sports"],
      },
    });

    expect(wrapper.find("button.btn-primary").attributes("disabled")).toBeDefined();
  });
});
