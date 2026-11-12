# Local Probability Transport — project website

[English](https://youn720lee.github.io/Boundary-State-DETR-site/) · [한국어](https://youn720lee.github.io/Boundary-State-DETR-site/ko.html)

**Local Probability Transport for Precise Object Detection**

The public method name is **Local Probability Transport (LPT)**. The existing
GitHub Pages address is preserved. The page describes `final_transport`, implemented
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
  coordinate distance. The default total budget is 3% of the uncorrected final
  box width or height; it does not bound GT error or imply an AP gain.
- Keep standard augmentation, native denoising and native detection losses.
  No first-hit path, inner/outer band reads, paired view, feature-perturbation
  branch, neighbor-directed DN or external teacher is used in this setting.

The four experiment rows are LPT, matched additive logits, additive logits with
the same distance budget, and LPT without the state field. The scan-free row
tests the complete state-feature module, not input-dependent selectivity alone.

New-model COCO AP and B300 latency are pending. Earlier architecture results are
not presented as LPT measurements. D-FINE/DEIM AP values are published references
linked to the official model zoo; the extended RT-DETRv4 comparison links its paper.

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

- `tools/make_evidence_examples.py`: COCO carousel and an illustrative final
  distribution update. Probabilities in the diagrams are explanatory examples.
- `tools/make_evolution.py`: D-FINE, DEIM and LPT, plus the collapsed four-model
  comparison with RT-DETRv4.
- `tools/make_architecture_film.py`: persistent detector overview with successive
  detail insets, a static reduced-motion alternative, and a mobile layout.

Figures use Calibri with restrained blue/gray accents and black text.
Rendering requires Pillow, Playwright and a Chromium browser; set
`EVOLUTION_CHROMIUM` when an explicit browser executable is needed.
The website itself has no runtime package dependency.
