# Boundary-State DETR — project website

[English](https://youn720lee.github.io/Boundary-State-DETR-site/) · [한국어](https://youn720lee.github.io/Boundary-State-DETR-site/ko.html)

This public repository contains the bilingual project website, figures and animations.
The architecture sequence follows one image through the backbone and encoder to
BCSA, which refines each query using its boundary distribution. During training,
an auxiliary decoder pass uses the same context-adjusted features for both the
state content and its step size. Inference uses the original encoder features.

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

Paper Figures 1 and 3 use COCO val2017 image 567197, a photograph by
[Berenice Abbott, New York Public Library](https://digitalcollections.nypl.org/items/510d47d9-4ef3-a3d9-e040-e00a18064a99).

The existing hosted Site is independent of this Pages deployment.
