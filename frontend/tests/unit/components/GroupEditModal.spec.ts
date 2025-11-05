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

import GroupEditModal from "@/components/groups/GroupEditModal.vue";

describe("GroupEditModal", () => {
  it("prefills current name", () => {
    const wrapper = mount(GroupEditModal, {
      props: {
        groupName: "Entertainment",
      },
    });

    expect((wrapper.find("input").element as HTMLInputElement).value).toBe("Entertainment");
  });

  it("emits save with new name", async () => {
    const wrapper = mount(GroupEditModal, {
      props: {
        groupName: "Entertainment",
      },
    });

    await wrapper.find("input").setValue("Lifestyle");
    await wrapper.find("button.btn-primary").trigger("click");
    await flushPromises();

    expect(wrapper.emitted("save")).toBeTruthy();
    expect(wrapper.emitted("save")?.[0]).toEqual(["Entertainment", "Lifestyle"]);
  });

  it("does not emit when name unchanged", async () => {
    const wrapper = mount(GroupEditModal, {
      props: {
        groupName: "Entertainment",
      },
    });

    await wrapper.find("button.btn-primary").trigger("click");
    await flushPromises();
    expect(wrapper.emitted("save")).toBeUndefined();
  });
});
