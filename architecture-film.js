// Show each complete figure before its animation enters the viewport.
// Reduced-motion visitors, offline failures, and non-JS browsers keep the still.
(() => {
  const motion = matchMedia('(prefers-reduced-motion: reduce)');
  const figures = [...document.querySelectorAll('.paper-animated')];

  figures.forEach(figure => {
    const image = figure.querySelector('img[data-animation]');
    if (!image) return;
    const picture = image.closest('picture');
    const nodes = picture ? [...picture.querySelectorAll('[data-animation]')] : [image];
    const assets = nodes.map(node => {
      const attr = node === image ? 'src' : 'srcset';
      return { node, attr, still: node.getAttribute(attr), animated: node.dataset.animation };
    });
    let visible = !('IntersectionObserver' in window);
    let failed = false;

    function sync() {
      const animate = visible && !document.hidden && !motion.matches && !failed;
      assets.forEach(asset => {
        const value = animate ? asset.animated : asset.still;
        if (asset.node.getAttribute(asset.attr) !== value) asset.node.setAttribute(asset.attr, value);
      });
    }

    image.addEventListener('error', () => {
      if (assets.some(a => a.node.getAttribute(a.attr) === a.animated)) {
        failed = true;
        sync();
      }
    });
    if ('IntersectionObserver' in window) {
      const observer = new IntersectionObserver(([entry]) => {
        visible = entry.isIntersecting;
        sync();
      }, { threshold: 0.05 });
      observer.observe(image);
    }
    motion.addEventListener('change', sync);
    document.addEventListener('visibilitychange', sync);
    sync();
  });
})();
