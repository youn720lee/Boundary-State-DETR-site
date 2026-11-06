(() => {
  const stack = document.querySelector("#evolution .ev-stack");
  if (!stack || !("IntersectionObserver" in window)) return;
  const frames = [...stack.querySelectorAll("[data-frame]")];
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  if (frames.length < 2 || reducedMotion.matches) return;

  // HTML initially shows the complete comparison, including without JavaScript.
  let active = -1;
  let visible = false;
  let timer;
  const observer = new IntersectionObserver(([entry]) => {
    visible = entry.isIntersecting;
    advanceWhenVisible();
  });

  function show(index) {
    active = index;
    frames.forEach((frame, i) => frame.classList.toggle("ev-current", i === active));
    if (active === frames.length - 1) {
      observer.disconnect();
      window.clearTimeout(timer);
      document.removeEventListener("visibilitychange", advanceWhenVisible);
      reducedMotion.removeEventListener("change", motionChanged);
    }
  }

  function advanceWhenVisible() {
    window.clearTimeout(timer);
    if (!visible || document.hidden) return;
    if (active < 0) show(0);
    if (active < frames.length - 1) {
      timer = window.setTimeout(() => {
        show(active + 1);
        advanceWhenVisible();
      }, 2400);
    }
  }

  function motionChanged() {
    if (reducedMotion.matches) show(frames.length - 1);
  }
  document.addEventListener("visibilitychange", advanceWhenVisible);
  reducedMotion.addEventListener("change", motionChanged);
  observer.observe(stack);
})();
