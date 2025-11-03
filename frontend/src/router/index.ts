import type { NavigationGuardNext, RouteLocationNormalized } from "vue-router";
import { createMemoryHistory, createRouter, createWebHistory } from "vue-router";

const routes = [
  {
    path: "/",
    redirect: "/stream-test",
  },
  {
    path: "/stream-test",
    name: "StreamTest",
    component: () => import("@/views/StreamTest.vue"),
    meta: { title: "Stream Test" },
  },
  {
    path: "/channels",
    name: "Channels",
    component: () => import("@/views/Channels.vue"),
    meta: { title: "TV Channels" },
  },
  {
    path: "/groups",
    name: "Groups",
    component: () => import("@/views/Groups.vue"),
    meta: { title: "TV Groups" },
  },
  {
    path: "/settings",
    name: "Settings",
    component: () => import("@/views/Settings.vue"),
    meta: { title: "Advanced Settings" },
  },
  {
    path: "/:pathMatch(.*)*",
    redirect: "/stream-test",
  },
];

export const createAppRouter = (history = createWebHistory()) =>
  createRouter({
    history,
    routes,
  });

const history = typeof window === "undefined" ? createMemoryHistory() : createWebHistory();
const router = createAppRouter(history);

router.beforeEach((_to: RouteLocationNormalized, _from: RouteLocationNormalized, next: NavigationGuardNext) => {
  // Reserved for future authentication/authorization hooks.
  next();
});

export { routes };
export default router;
