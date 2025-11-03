import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import { createMemoryHistory, createRouter } from "vue-router";
import { nextTick } from "vue";

import App from "@/App.vue";
import { routes } from "@/router";

async function mountWithRouter(initialPath = "/stream-test") {
  const router = createRouter({
    history: createMemoryHistory(),
    routes,
  });

  await router.push(initialPath);
  await router.isReady();

  const wrapper = mount(App, {
    global: {
      plugins: [router],
    },
  });

  return { wrapper, router };
}

describe("router configuration", () => {
  it("defines all primary navigation routes", () => {
    const routePaths = routes.map((route) => route.path);
    expect(routePaths).toContain("/stream-test");
    expect(routePaths).toContain("/channels");
    expect(routePaths).toContain("/groups");
    expect(routePaths).toContain("/settings");
  });

  it("redirects root path to stream-test", async () => {
  const { wrapper } = await mountWithRouter("/");
  await nextTick();
    expect(wrapper.html()).toContain("Stream Test");
  });

  it("updates UI when navigating between tabs", async () => {
    const { wrapper, router } = await mountWithRouter("/stream-test");
    await nextTick();

    await router.push("/channels");
    await nextTick();

    expect(router.currentRoute.value.path).toBe("/channels");
    expect(wrapper.html()).toContain("TV Channels");
  });
});
