/** Selection owns its request, stream callbacks and loading updates. */
export function createRequestScope() {
  let epoch = 0;
  let controller = new AbortController();
  return {
    current() { const current = epoch; return { signal: controller.signal, isCurrent: () => current === epoch }; },
    next() {
      controller.abort();
      controller = new AbortController();
      const current = ++epoch;
      return { signal: controller.signal, isCurrent: () => current === epoch };
    },
    dispose() { controller.abort(); epoch += 1; }
  };
}
