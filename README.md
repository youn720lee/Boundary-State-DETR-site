# LWR — project website

[English](https://youn720lee.github.io/Boundary-State-DETR-site/) · [한국어](https://youn720lee.github.io/Boundary-State-DETR-site/ko.html)

This repository contains the bilingual project page, figures and animations for
**Look Where You Regress: Candidate-Aligned Features for Object Detection**.
The existing Pages address is preserved.

The current page describes Boundary Evidence v2, implemented at
[`tfdet@8c9a2e4`](https://github.com/youn720lee/tfdet/commit/8c9a2e4b81c6d6cae2531feb1e7b1cd462062f21).
The paper and page use **Look Where You Regress (LWR)** as the public method name;
the existing `boundary_evidence` architecture name and v2 execution flags stay unchanged.
Its [implementation and commands](https://github.com/youn720lee/tfdet/blob/dqm/platform/vfm_v3_detr/BOUNDARY_EVIDENCE_V2.md)
are the source of truth:

- One encoded image supplies a stride-8, four-direction Mamba-style selective
  state field shared across queries. There is no 32×32 interval table.
- Direct query similarity, conditional first-hit distributions, separate no-hit
  information and local inner/outer observations are read at native FDR candidate offset positions.
- A zero-initialized shared head corrects the first decoder layer's distribution
  logits once. Later FDR, LQE and native self-distillation remain in place.
- Neighbour-directed denoising changes query boxes during training, not input
  images. Standard image augmentation is retained; no paired-view branch or
  external teacher is used.

The page presents the current method, its figures and the planned ablations.
COCO results for this model are pending. Published D-FINE/DEIM values are linked
to the official DEIM model zoo; the extended RT-DETRv4 comparison links its paper.

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

## Figure sources

- `tools/make_evidence_examples.py`: COCO example carousel, candidate positions
  and evidence schematic. Photos are preserved; overlays are illustrative.
- `tools/make_evolution.py`: D-FINE, DEIM, proposed model, and the collapsed
  four-model comparison including RT-DETRv4.
- `tools/make_architecture_film.py`: an autoplay architecture GIF with a persistent
  detector overview and successive detail insets, plus a static reduced-motion
  alternative and a mobile layout.

All current diagrams use Calibri, restrained blue/green/gray accents and mostly
black text. Set `EVOLUTION_CHROMIUM` to a locally installed Chromium executable
when rendering with the scripts. Pillow and Playwright are required for rendering;
the website itself has no runtime package dependency.

The existing hosted Site is independent of this Pages deployment.
