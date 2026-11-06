(() => {
  const section = document.querySelector(".teaser");
  const viewer = section?.querySelector("#boundary-viewer");
  if (!viewer) return;
  const cases = [...viewer.querySelectorAll("[data-example]")];
  const bar = section.querySelector(".example-controls");
  const stageBar = section.querySelector(".stage-controls");
  const stages = [...stageBar.querySelectorAll("[data-stage]")];
  const compact = matchMedia("(max-width: 700px)");
  let current = 0;
  let stage = 0;
  const output = bar.querySelector("output");

  function render() {
    cases.forEach((example, index) => {
      example.hidden = index !== current;
      example.querySelectorAll(".scene").forEach((panel, i) => {
        panel.hidden = compact.matches && i !== stage;
      });
    });
    output.textContent = (current + 1) + " / " + cases.length + "　" + cases[current].dataset.example;
    stages.forEach((button, i) => button.setAttribute("aria-pressed", String(i === stage)));
    stageBar.hidden = !compact.matches;
  }
  function move(delta) {
    current = (current + delta + cases.length) % cases.length;
    render();
  }
  bar.querySelector("[data-previous]").addEventListener("click", () => move(-1));
  bar.querySelector("[data-next]").addEventListener("click", () => move(1));
  stages.forEach((button, index) => button.addEventListener("click", () => { stage = index; render(); }));
  section.addEventListener("keydown", event => {
    if (event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return;
    if (event.key === "ArrowLeft" || event.key === "ArrowRight") {
      event.preventDefault();
      move(event.key === "ArrowLeft" ? -1 : 1);
    }
  });
  let start = null;
  viewer.addEventListener("pointerdown", event => {
    if (event.isPrimary && event.pointerType !== "mouse") start = {x: event.clientX, y: event.clientY};
  });
  viewer.addEventListener("pointercancel", () => { start = null; });
  viewer.addEventListener("pointerup", event => {
    if (!start || !event.isPrimary) return;
    const dx = event.clientX - start.x, dy = event.clientY - start.y;
    start = null;
    if (Math.abs(dx) > 42 && Math.abs(dx) > 1.6 * Math.abs(dy)) move(dx < 0 ? 1 : -1);
  });
  compact.addEventListener("change", render);
  viewer.tabIndex = 0;
  render();
  bar.hidden = false;
})();
