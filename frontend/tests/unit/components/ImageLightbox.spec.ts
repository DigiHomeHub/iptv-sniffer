import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, describe, expect, it } from "vitest";

import ImageLightbox from "@/components/common/ImageLightbox.vue";

describe("ImageLightbox", () => {
  afterEach(() => {
    document.body.innerHTML = "";
  });

  const mountLightbox = (props: Record<string, unknown> = {}) =>
    mount(ImageLightbox, {
      props: {
        isOpen: true,
        imageUrl: "/test.png",
        altText: "Test Image",
        ...props,
      },
      attachTo: document.body,
      global: {
        stubs: {
          transition: false,
          "transition-group": false,
        },
      },
    });

  it("renders image when open", async () => {
    const wrapper = mountLightbox();
    await flushPromises();
    await wrapper.vm.$nextTick();

    const img = document.body.querySelector("img");
    expect(img).not.toBeNull();
    expect(img?.getAttribute("src")).toBe("/test.png");
    expect(img?.getAttribute("alt")).toBe("Test Image");

    wrapper.unmount();
  });

  it("emits close when button clicked", async () => {
    const wrapper = mountLightbox({ altText: "Screenshot" });
    await flushPromises();
    await wrapper.vm.$nextTick();

    const button = document.body.querySelector<HTMLButtonElement>("button[aria-label='Close']");
    expect(button).not.toBeNull();

    button?.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    await flushPromises();

    expect(wrapper.emitted("close")).toBeTruthy();

    wrapper.unmount();
  });

  it("does not render content when closed", async () => {
    const wrapper = mountLightbox({ isOpen: false });
    await flushPromises();

    const img = document.body.querySelector("img");
    expect(img).toBeNull();

    wrapper.unmount();
  });
});
