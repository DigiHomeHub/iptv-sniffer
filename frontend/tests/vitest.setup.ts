class ResizeObserverStub {
  observe() {}
  unobserve() {}
  disconnect() {}
}

if (typeof window !== "undefined") {
  // @ts-ignore
  window.ResizeObserver = window.ResizeObserver || ResizeObserverStub;
}
