# Boundary-State DETR — project website

[English](https://youn720lee.github.io/Boundary-State-DETR-site/) · [한국어](https://youn720lee.github.io/Boundary-State-DETR-site/ko.html)

This public repository contains only the bilingual project website: HTML, CSS,
JavaScript, figures, animations, and fonts. The design and content are preserved
from the existing [project site](https://boundary-state-detr.tranqualize.chatgpt.site/).

Model source is kept in the separate **private**
[`Boundary-State-DETR`](https://github.com/youn720lee/Boundary-State-DETR)
repository. Access to that repository requires authorization.

## Publishing

GitHub Pages serves `main` → `/ (root)` with **Deploy from a branch**.
Changes pushed to `main` are deployed automatically. No build step is required;
`.nojekyll` preserves the static files.

## Local preview

```bash
python -m http.server 8000 --bind 127.0.0.1
```

Open `http://127.0.0.1:8000/` or `http://127.0.0.1:8000/ko.html`.
The `ko/` alias redirects to `ko.html`, preserving the query and section anchor.

Edit `index.html` and `ko.html` together. Keep asset paths relative for the
GitHub Pages project URL. Preserve photograph credits and the font licenses in
`assets/fonts/`. Figures appear inline without download buttons.

The existing hosted Site is independent of this Pages deployment.
