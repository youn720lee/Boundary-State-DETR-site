// Show each complete figure before its animation enters the viewport.
// Reduced-motion visitors, offline failures, and non-JS browsers keep the still.
(() => {
  const motion = matchMedia('(prefers-reduced-motion: reduce)');
  const korean = document.documentElement.lang === 'ko';
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
    let play = !motion.matches;

    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'figure-motion-toggle';
    image.id ||= `paper-motion-${figures.indexOf(figure) + 1}`;
    button.setAttribute('aria-controls', image.id);
    const caption = figure.querySelector('figcaption');
    figure.insertBefore(button, caption);

    function sync() {
      const animate = visible && play && !document.hidden && !failed;
      assets.forEach(asset => {
        const value = animate ? asset.animated : asset.still;
        if (asset.node.getAttribute(asset.attr) !== value) asset.node.setAttribute(asset.attr, value);
      });
      button.hidden = failed;
      if (korean) button.textContent = play ? '애니메이션 일시정지' : '애니메이션 재생';
      else button.textContent = play ? 'Pause animation' : 'Play animation';
    }

    button.addEventListener('click', () => {
      play = !play;
      sync();
    });

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
    motion.addEventListener('change', () => {
      play = !motion.matches;
      sync();
    });
    document.addEventListener('visibilitychange', sync);
    sync();
  });
})();
