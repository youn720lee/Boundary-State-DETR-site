# Boundary-State DETR — project website

[English](https://youn720lee.github.io/Boundary-State-DETR-site/) · [한국어](https://youn720lee.github.io/Boundary-State-DETR-site/ko.html)

This public repository contains the bilingual project website, figures and animations.
Figures 1 and 2 start with the same COCO input photograph and follow the detector
from bottom to top. The proposed model uses selective bidirectional boundary
transport in the final decoder layer. Within each candidate interval, Mamba’s
content-dependent transitions determine how much exterior state reaches the
opposite edge. One query gate scales this contribution in both directions.
The feature pyramid is computed once during training and inference.

The source link on the page leads to the earlier model in the private
[`Boundary-State-DETR`](https://github.com/youn720lee/Boundary-State-DETR)
repository.

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
