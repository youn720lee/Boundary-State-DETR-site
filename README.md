# Vernier-DETR: Refining Box-Edge Distributions with Features from Neighboring Candidates

[English project page](https://youn720lee.github.io/Boundary-State-DETR-site/) · [한국어 프로젝트 페이지](https://youn720lee.github.io/Boundary-State-DETR-site/ko.html)

Vernier-DETR samples image features at the D-FINE decoder's candidate edge coordinates. A shared head compares neighboring candidates and moves probability between them before the detector decodes the box. All queries read one stride-8 context map. Both model sizes use three sampling rays, two refinement steps, and a total distance budget of 0.05 times the unrefined box width or height.

## COCO val2017

| Model | AP | AP50 | AP75 | AP small | AP medium | AP large | Deploy params | GFLOPs | T4 mean latency |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Vernier-DETR-L | 55.1 | 72.8 | 59.9 | 36.8 | 60.1 | 72.7 | 30.8M | 91.3 | 8.11 ms |
| Vernier-DETR-X | 56.8 | 74.4 | 61.8 | 39.1 | 61.6 | 74.4 | 61.7M | 202.8 | 12.93 ms |

Both detectors train for 58 epochs on COCO train2017 with ImageNet-pretrained backbones and no Objects365 or external teacher during detector training. Latency is the batch-one mean for 640 × 640 inputs on an NVIDIA T4 with TensorRT FP16. The pages reproduce the manuscript’s four tables and seven figures.

## Editing and preview

Serve the repository root with `python -m http.server 8000 --bind 127.0.0.1`. GitHub Pages deploys the root of `main`. Update `index.html` and `ko.html` together. The `/ko/` alias preserves the query string and section link.

The figures in `assets/paper-figures/` use the manuscript PDFs. To refresh the web images and the animations for Figures 2 and 3, install Pillow and pypdfium2 and run `python tools/make_paper_figure_motion.py`. Pass `--paper-dir PATH` to import revised figure PDFs from the manuscript. The opening COCO carousel illustrates the operation. Figure 7 shows measured predictions for three selected COCO val2017 detections. See the [figure credits](assets/paper-figures/CREDITS.md) and the photo credits on both pages.
