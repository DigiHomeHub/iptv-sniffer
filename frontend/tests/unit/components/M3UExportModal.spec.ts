import { flushPromises, mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/api/m3u", () => {
  const importMock = vi.fn();
  const exportMock = vi.fn();
  return {
    default: {
      import: importMock,
      export: exportMock,
    },
    importM3U: importMock,
    exportM3U: exportMock,
  };
});

import M3UExportModal from "@/components/m3u/M3UExportModal.vue";
import m3uAPI from "@/api/m3u";

const mockedM3UApi = vi.mocked(m3uAPI);

const dialogStubs = {
  Dialog: {
    template: "<div><slot /></div>",
    props: ["open"],
  },
  DialogPanel: {
    template: "<div><slot /></div>",
  },
  DialogTitle: {
    template: "<div><slot /></div>",
  },
};

describe("M3UExportModal", () => {
  beforeEach(() => {
    mockedM3UApi.export.mockReset();
  });

  it("calls export with provided filters", async () => {
    const wrapper = mount(M3UExportModal, {
      props: { isOpen: true },
      global: { stubs: dialogStubs },
    });

    await wrapper.get("#export-group").setValue("央视");
    await wrapper.get("#export-resolution").setValue("1080p");
    await wrapper.get("#export-status").setValue("online");

    await wrapper.get("button.btn-primary").trigger("click");
    await flushPromises();

    expect(mockedM3UApi.export).toHaveBeenCalledWith({
      group: "央视",
      resolution: "1080p",
      status: "online",
    });
    expect(wrapper.emitted("close")).toBeTruthy();
  });

  it("resets filters when modal closes", async () => {
    const wrapper = mount(M3UExportModal, {
      props: { isOpen: true },
      global: { stubs: dialogStubs },
    });

    await wrapper.get("#export-group").setValue("影视");
    await wrapper.get("#export-resolution").setValue("4K");
    await wrapper.get("#export-status").setValue("offline");

    await wrapper.setProps({ isOpen: false });
    await wrapper.vm.$nextTick();

    expect((wrapper.get("#export-group").element as HTMLInputElement).value).toBe("");
    expect((wrapper.get("#export-resolution").element as HTMLSelectElement).value).toBe("");
    expect((wrapper.get("#export-status").element as HTMLSelectElement).value).toBe("");
  });

  it("emits close without exporting when cancelled", async () => {
    const wrapper = mount(M3UExportModal, {
      props: { isOpen: true },
      global: { stubs: dialogStubs },
    });

    await wrapper.get("button.btn-secondary").trigger("click");
    await flushPromises();

    expect(mockedM3UApi.export).not.toHaveBeenCalled();
    expect(wrapper.emitted("close")).toBeTruthy();
  });
});
