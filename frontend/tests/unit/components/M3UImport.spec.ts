import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

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

import M3UImport from "@/components/m3u/M3UImport.vue";
import type { M3UImportResult } from "@/api/m3u";
import m3uAPI from "@/api/m3u";

const mockedM3UApi = vi.mocked(m3uAPI);

describe("M3UImport", () => {
  let alertSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    mockedM3UApi.import.mockReset();
    alertSpy = vi.spyOn(window, "alert").mockImplementation(() => {});
  });

  afterEach(() => {
    alertSpy.mockRestore();
  });

  it("uploads playlist files and emits import-complete", async () => {
    const result: M3UImportResult = {
      imported: 2,
      failed: 0,
      channels: [],
      errors: [],
    };
    mockedM3UApi.import.mockResolvedValue(result);

    const wrapper = mount(M3UImport);
    const input = wrapper.find("input[type='file']");

    const file = new File(["#EXTM3U"], "playlist.m3u", { type: "audio/x-mpegurl" });
    Object.defineProperty(input.element, "files", {
      value: [file],
      configurable: true,
    });

    await input.trigger("change");
    await flushPromises();

    expect(mockedM3UApi.import).toHaveBeenCalledWith(file);
    expect(wrapper.emitted("import-complete")).toBeTruthy();
    expect(wrapper.emitted("import-complete")?.[0]).toEqual([result]);
  });

  it("rejects files without m3u extension", async () => {
    const wrapper = mount(M3UImport);
    const input = wrapper.find("input[type='file']");

    const file = new File(["not-a-playlist"], "notes.txt", { type: "text/plain" });
    Object.defineProperty(input.element, "files", {
      value: [file],
      configurable: true,
    });

    await input.trigger("change");
    await flushPromises();

    expect(mockedM3UApi.import).not.toHaveBeenCalled();
    expect(alertSpy).toHaveBeenCalledWith("Please upload a .m3u or .m3u8 file");
  });
});
