// Begin with the complete architecture, even when the visitor scrolls slowly from the abstract.
(() => {
  const image = document.querySelector('#architecture-film img[data-animation]');
  if (!image) return;
  // The same story uses a stacked inset on small screens. Let <picture>
  // select one source, so mobile visitors never need the desktop movie.
  const assets = [...image.closest('picture').querySelectorAll('[data-animation]')].map(node => {
    const attr = node === image ? 'src' : 'srcset';
    return { node, attr, still: node.getAttribute(attr), animated: node.dataset.animation };
  });
  const motion = matchMedia('(prefers-reduced-motion: reduce)');
  let visible = !('IntersectionObserver' in window);
  let failed = false;

  function sync() {
    const still = motion.matches || failed;
    if (!still && (!visible || document.hidden)) return;
    for (const a of assets) {
      const value = still ? a.still : a.animated;
      if (a.node.getAttribute(a.attr) !== value) a.node.setAttribute(a.attr, value);
    }
  }
  image.addEventListener('error', () => {
    if (assets.some(a => a.node.getAttribute(a.attr) === a.animated)) { failed = true; sync(); }
  });
  if (!visible) {
    const observer = new IntersectionObserver(([entry]) => {
      visible = entry.isIntersecting;
      sync();
    }, { threshold: 0.15 });
    observer.observe(image);
  }
  motion.addEventListener('change', sync);
  document.addEventListener('visibilitychange', sync);
  sync();
})();
