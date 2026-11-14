# SHIFT-DETR — project website

[English](https://youn720lee.github.io/Boundary-State-DETR-site/) · [한국어](https://youn720lee.github.io/Boundary-State-DETR-site/ko.html)

**Bounded Local Probability Refinement for Object Detection**

The model name is **SHIFT-DETR**. SHIFT describes redistributing probability between neighboring candidate locations. The page describes `final_transport`, implemented
in [`tfdet@720af927`](https://github.com/youn720lee/tfdet/commit/720af92780b9449748e838014ab6acd5c7724dfb).
The [implementation protocol and experiment commands](https://github.com/youn720lee/tfdet/blob/dqm/platform/vfm_v3_detr/FINAL_TRANSPORT_L_EXPERIMENTS.md)
define the current setting.

## Method

- Encode one image. Build a shared stride-8 Mamba-style state field with four
  directional image scans, then sample it at the native FDR candidate positions.
- Use candidate observations, the query, current probabilities and physical
  coordinate gaps to predict signed transfers between adjacent candidates.
- Correct the **final cumulative FDR distribution**, immediately before Integral
  and LQE. Native localization and GO-LSD objectives use the same corrected logits.
- Preserve probability mass and constrain distribution movement by actual
  coordinate distance. The reported two-step model shares a total budget of 5% of the uncorrected final
  box width or height; it does not bound GT error or imply an AP gain.
- Keep standard augmentation, native denoising and native detection losses.
  No first-hit path, inner/outer band reads, paired view, feature-perturbation
  branch, neighbor-directed DN or external teacher is used in this setting.

Table 1 compares published detector results on COCO val2017. SHIFT-DETR-L and
published DEIM-L use the same HGNetv2-B4 stage-1 weights (SSLD on ImageNet-1K and ImageNet-22K)
and a 50 + 8 epoch schedule. The SHIFT-DETR-L global batch size is 32. SHIFT-DETR-L (total budget 0.05, two steps)
reaches 55.1 AP and 59.9 AP75, 0.4 and 0.5 points above DEIM-L respectively,
and 0.2 AP above DEIM-L + BUTR. The comparison permits backbone pretraining and excludes
foundation-model backbones, external teachers during detector training, and Objects365 detection pretraining.
The site identifies pending mechanism tests and same-device runtime measurements.

## Publishing and preview

GitHub Pages serves `main` → `/ (root)` using **Deploy from a branch**.
Pushing `main` deploys the static files; `.nojekyll` disables Jekyll processing.

```bash
python -m http.server 8000 --bind 127.0.0.1
```

Open `http://127.0.0.1:8000/` or `http://127.0.0.1:8000/ko.html`.
The `/ko/` alias redirects to `ko.html`, preserving the query and anchor.
Edit English and Korean together and keep asset paths relative for GitHub Pages.
Preserve photograph attribution and the licenses in `assets/fonts/`.
Figures appear inline without download buttons.

## Figure sources

- `assets/paper-figures/`: the paper's Figures 1–3, with matching PDF, SVG,
  draw.io and raster versions. Figure 1 shows the detector overview; Figure 2
  compares D-FINE, DEIM and SHIFT-DETR; Figure 3 expands the selective field, adjacent
  candidate comparison and bounded local probability refinement. The COCO photograph source is
  documented in `assets/paper-figures/CREDITS.md`.
- `tools/make_paper_figure_motion.py`: regenerate the site's PNGs and GIFs from
  the bundled paper PDFs using Pillow and Poppler (`pdftoppm`). Optional
  `--paper-dir` imports a revised set of paper PDF/SVG/draw.io files first.
  The animation highlights the reading sequence; it does not show measured
  model activations. The complete detector remains visible in Figure 3.
- `tools/make_evidence_examples.py`: COCO carousel and an illustrative final
  distribution update. Probabilities in the diagrams are explanatory examples.
- `tools/make_evolution.py --auxiliary-only`: the collapsed four-model
  comparison with RT-DETRv4. Its Calibri labels are rasterized into the SVG,
  preserving typography without redistributing font files.
- `tools/make_architecture_film.py` is the earlier generator; the live page now
  uses the paper-derived assets above. Do not use it to rebuild current figures.

Figures use Calibri, black text, gray native blocks and pale blue/green/peach
method blocks. The live page uses high-resolution PNG/GIF renders so the font
does not change across operating systems. No font files are added by this update.
Animations start automatically on entering the viewport; reduced-motion and
non-JavaScript visitors see the complete still figures. Small screens can scroll
the wide figures horizontally. The website has no runtime package dependency.
