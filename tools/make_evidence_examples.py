"""Draw candidate-offset evidence schematics on existing, unmodified COCO crops.

Run: python tools/make_evidence_examples.py
Optional: --render-dir PATH writes PNG previews using Playwright Chromium.
The boxes, selected offsets and cue pathways are schematics, not model outputs.
"""
from argparse import ArgumentParser
from base64 import b64encode
from html import escape
from io import BytesIO
import os
from pathlib import Path

from PIL import Image

from make_feature_panels import CASES
from make_transport_examples import REGIONS

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "examples"
W, H = 417, 282
INK, BLUE, GREEN = "#171717", "#156082", "#48713f"
PALE, RULE = "#e9f2f6", "#8a8a8a"


def uri(im):
    memory = BytesIO()
    im.save(memory, "PNG")
    return "data:image/png;base64," + b64encode(memory.getvalue()).decode("ascii")


def text(x, y, value, size=15, weight=400, anchor="middle", fill=INK):
    return (f'<text x="{x:.2f}" y="{y:.2f}" font-size="{size}" font-weight="{weight}" '
            f'text-anchor="{anchor}" fill="{fill}">{escape(value)}</text>')


def line(d, color=INK, width=1.3, arrow=False, dash=None):
    options = ' marker-end="url(#arrow)"' if arrow else ""
    if dash:
        options += f' stroke-dasharray="{dash}"'
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}"{options}/>'


def svg(title, body, desc):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="417" height="282" '
            f'viewBox="0 0 {W} {H}" font-family="Calibri,Arial,sans-serif">'
            f'<title>{escape(title)}</title><desc>{escape(desc)}</desc>'
            '<defs><marker id="arrow" markerWidth="6" markerHeight="6" refX="5.4" '
            'refY="3" orient="auto"><path d="M0 0L6 3L0 6Z" fill="#171717"/></marker></defs>'
            f'<rect width="417" height="282" fill="white"/>{body}</svg>\n')


def draw_case(name):
    with Image.open(OUT / f"{name}-scene.webp") as src:
        photo = src.convert("RGB").resize((W, H), Image.Resampling.LANCZOS)
    _, crop, _, _ = CASES[name]
    left, top, right, bottom, _ = REGIONS[name]
    sx, sy = W / (crop[2] - crop[0]), H / (crop[3] - crop[1])
    x0, x1 = (left - crop[0]) * sx, (right - crop[0]) * sx
    y0, y1 = (top - crop[1]) * sy, (bottom - crop[1]) * sy
    cx, cy = (x0+x1)/2, (y0+y1)/2
    rays = [cy - .4*(y1-y0), cy, cy + .4*(y1-y0)]
    # Show a small subset of outward candidate offsets; retain unequal spacing.
    distances = [.16, .32, .44, .54, .64]
    candidate_x = [cx + r*(x1-x0) for r in distances]
    candidate_x = [min(W-15, x) for x in candidate_x]
    contents = f'<image width="417" height="282" href="{uri(photo)}"/>'
    box_path = f'M{x0:.2f},{y0:.2f}H{x1:.2f}V{y1:.2f}H{x0:.2f}Z'
    contents += line(box_path, "white", 4.5) + line(box_path, BLUE, 1.8)
    for y in rays:
        contents += line(f'M{cx:.2f},{y:.2f}H{candidate_x[-1]+5:.2f}', "white", 3.2)
        contents += line(f'M{cx:.2f},{y:.2f}H{candidate_x[-1]+5:.2f}', INK, 1.15, dash="4 3")
        for x in candidate_x:
            contents += f'<circle cx="{x:.2f}" cy="{y:.2f}" r="3.7" fill="{BLUE}" stroke="white" stroke-width="1.3"/>'
    contents += '<rect x="11" y="9" width="191" height="25" fill="white" fill-opacity=".94"/>'
    contents += text(20, 26, "Candidate offsets · right edge", 15, anchor="start")
    contents += '<rect x="11" y="249" width="235" height="25" fill="white" fill-opacity=".94"/>'
    contents += text(20, 266, "Same construction for all four edges", 14, anchor="start")
    candidates = OUT / f"{name}-candidates.svg"
    candidates.write_text(svg(f"Candidate-offset positions on the {name}", contents,
        "Illustrative first-layer box and a subset of candidate offsets on three parallel outward rays. Positions are a schematic, not detector predictions."), encoding="utf-8")

    # Enlarge the same central image strip, with matched candidate positions.
    # No synthetic activations, probability heights or inferred boundaries.
    strip_left, strip_right = max(0, cx-15), min(W, candidate_x[-1]+18)
    strip = photo.crop((round(strip_left), round(cy-23), round(strip_right), round(cy+23)))
    map_x = lambda x: 22 + (x-strip_left) * 373 / (strip_right-strip_left)
    contents = text(W/2, 19, "Read state features at these positions", 16, 700)
    contents += f'<image x="22" y="30" width="373" height="57" href="{uri(strip)}" preserveAspectRatio="none"/>'
    for j, x in enumerate(candidate_x):
        px = map_x(x)
        contents += f'<circle cx="{px:.2f}" cy="59" r="4" fill="{BLUE}" stroke="white" stroke-width="1.4"/>'
        contents += text(px, 105, f"c{j+1}", 14)
    contents += line('M29,115H387', arrow=True)
    contents += text(W/2, 132, "Center → outward order", 14)
    labels = [(22, "Query", "similarity"), (151, "First-hit", "distribution"), (280, "Inner / outer", "local bands")]
    for x, top_label, bottom_label in labels:
        fill = "#e1efd9" if x == 151 else PALE
        contents += f'<rect x="{x}" y="145" width="115" height="45" fill="{fill}" stroke="#747474" stroke-width=".8"/>'
        contents += text(x+57.5, 163, top_label, 15, 700) + text(x+57.5, 181, bottom_label, 15)
        contents += line(f'M{x+57.5},190V205H208.5V219', arrow=x==151)
    contents += '<rect x="107" y="220" width="203" height="29" fill="#e8e8e8" stroke="#747474" stroke-width=".8"/>'
    contents += text(W/2, 240, "Shared candidate-score head", 15, 700)
    contents += text(W/2, 271, "Add once to the first FDR logits", 15)
    evidence = OUT / f"{name}-evidence.svg"
    evidence.write_text(svg(f"Three candidate-evidence cues for the {name}", contents,
        "The same central photo strip locates a subset of candidate offsets. Three branches represent direct query similarity, learned first-hit evidence and local inner/outer observations from the shared stride-8 state field. A shared head adds a correction to the first FDR logits. The diagram contains no measured feature or probability values."), encoding="utf-8")
    return candidates, evidence


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--render-dir", type=Path)
    args = parser.parse_args()
    outputs = [path for name in CASES for path in draw_case(name)]
    if args.render_dir:
        from playwright.sync_api import sync_playwright
        args.render_dir.mkdir(parents=True, exist_ok=True)
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=os.environ.get("EVOLUTION_CHROMIUM"))
            page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=2)
            for path in outputs:
                page.set_content('<style>html,body{margin:0}</style>'+path.read_text(encoding="utf-8"))
                page.screenshot(path=str(args.render_dir / (path.stem + ".png")))
            browser.close()
    print("Generated six candidate-evidence teaser SVGs.")


if __name__ == "__main__":
    main()
