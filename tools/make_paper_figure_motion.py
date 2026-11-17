"""Render the seven manuscript figures for the Vernier-DETR website.

Run with Pillow and pypdfium2. By default, read the PDFs in assets/paper-figures.
To import a new manuscript, pass --paper-dir /path/to/manuscript/figures.
Motion highlights the printed diagram in reading order.
"""
import argparse
import shutil
from pathlib import Path

import pypdfium2 as pdfium
from PIL import Image, ImageDraw


OUTPUT = Path(__file__).resolve().parents[1] / "assets" / "paper-figures"
# Website name, corresponding manuscript asset, raster width in pixels.
FIGURES = [
    ("fig1-overview", "lpt-fig1-overview", 1200),
    ("fig2-evolution", "lpt-fig2-advancing", 1800),
    ("fig3-framework", "fig_shift_framework", 1800),
    ("fig4-scan", "fig_selective_scan", 1180),
    ("fig5-sampling", "fig_candidate_sampling", 1180),
    ("fig6-update", "figure_local_update", 1180),
    ("fig7-qualitative", "fig_qualitative_refinement", 2016),
]

# Rectangles use the manuscript PDF coordinates, with the origin at top left.
# All printed labels remain visible while each successive region is highlighted.
HIGHLIGHTS = {
    "fig2-evolution": [
        [(2, 2, 394, 483)],
        [(403, 2, 802, 483)],
        [(808, 2, 1197, 483)],
    ],
    "fig3-framework": [
        [(54, 16, 126, 73), (139, 1, 379, 88)],
        [(6, 102, 84, 159), (101, 128, 184, 159)],
        [(199, 128, 275, 159), (283, 112, 394, 189)],
        [(418, 119, 468, 141), (418, 158, 468, 180)],
    ],
}


def render_pdf(path, width):
    with pdfium.PdfDocument(path) as document:
        if len(document) != 1:
            raise ValueError(f"{path.name} must contain exactly one figure page")
        page = document[0]
        try:
            scale = width / page.get_width()
            bitmap = page.render(scale=scale)
            try:
                image = bitmap.to_pil().convert("RGB")
            finally:
                bitmap.close()
        finally:
            page.close()
    return image, scale


def animate_regions(still, scale, regions, output):
    # Reserve one palette entry for the outline. All other pixels keep exactly
    # the same palette entries across frames, including the photographic inset.
    poster = still.quantize(colors=255, dither=Image.Dither.NONE)
    palette = poster.getpalette()[:765]
    palette.extend([0] * (765 - len(palette)))
    poster.putpalette(palette + [31, 104, 153])
    frames = []
    for boxes in regions:
        frame = poster.copy()
        draw = ImageDraw.Draw(frame)
        for box in boxes:
            draw.rectangle(tuple(round(v * scale) for v in box),
                           outline=255, width=max(2, round(2.2 * scale)))
        frames.append(frame)
    poster.save(output, save_all=True, append_images=frames, loop=0,
                duration=[2600] + [1650] * len(frames), disposal=1,
                optimize=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paper-dir", type=Path, help="Manuscript figures directory")
    args = parser.parse_args()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for name, source_name, width in FIGURES:
        pdf = OUTPUT / f"{name}.pdf"
        if args.paper_dir:
            shutil.copyfile(args.paper_dir / f"{source_name}.pdf", pdf)
        image, scale = render_pdf(pdf, width)
        image.save(OUTPUT / f"{name}.webp", lossless=True, method=4)
        if name in HIGHLIGHTS:
            animate_regions(image, scale, HIGHLIGHTS[name], OUTPUT / f"{name}.gif")
        print(f"{name}: {image.width} x {image.height}")


if __name__ == "__main__":
    main()
