"""Render the persistent selective-transport detector diagram and animated detail.

Run python tools/make_architecture_film.py with Pillow, Playwright and Calibri.
Set EVOLUTION_CHROMIUM to use an installed Chromium executable.
"""
from base64 import b64encode
from html import escape
from io import BytesIO
import os
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

ASSETS = Path(__file__).resolve().parents[1] / "assets"
DEST = ASSETS / "contributions"
DESKTOP, PORTRAIT = (1080, 660), (620, 1280)
INK, MUTED, LINE = "#192126", "#4c565b", "#bfc9cb"
BLUE, PALE_BLUE = "#156082", "#e9f2f6"
GREEN, PALE_GREEN = "#48713f", "#e1efd9"
GRAY = "#eceeee"

TITLE = "Boundary-State DETR with selective boundary transport"
DESC = ("A single COCO photograph enters the backbone and encoder. In the last decoder layer, "
        "two opposed Mamba scans accumulate in-box content and carry exterior state across a "
        "candidate interval. The cells inside the interval set its transmission. A shared query gate "
        "admits the transmitted state. After averaging directions and weighting candidate states "
        "by their boundary probabilities, the decoder projects the result into a residual query update.")


def text(x, y, words, size=20, *, bold=False, color=INK, anchor="start", italic=False):
    attrs = (f'x="{x}" y="{y}" font-size="{size}" text-anchor="{anchor}" fill="{color}" '
             f'font-weight="{700 if bold else 400}" font-style="{"italic" if italic else "normal"}"')
    return f'<text {attrs}>{escape(words)}</text>'


def rect(x, y, w, h, fill, edge="none", stroke=1):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" '
            f'stroke="{edge}" stroke-width="{stroke}"/>')


def path(d, color=INK, stroke=1.7, *, arrow=False, dashed=False):
    marker = f' marker-end="url(#m{color[1:]})"' if arrow else ""
    dash = ' stroke-dasharray="4 4"' if dashed else ""
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{stroke}"{marker}{dash}/>'


def block(x, y, w, h, words, fill=GRAY, color=INK, size=18, edge="none"):
    return rect(x, y, w, h, fill, edge) + text(x + w/2, y + h/2 + .32*size, words, size,
                                             color=color, bold=True, anchor="middle")


def group(x, y, scale, contents):
    return f'<g transform="translate({x},{y}) scale({scale})">{contents}</g>'


def detector(photo, phase):
    """Bottom-up map. The two shorter routes originate from the encoder and previous decoder."""
    cx, left, width = 150, 39, 222
    nodes = [
        (0, 34, "Class scores and boxes", BLUE),
        (57, 38, "FFN and prediction heads", GRAY),
        (119, 46, "Boundary State Transport", PALE_GREEN),
        (190, 40, "Cross-attention + gateway", GRAY),
        (255, 38, "Earlier decoder layers", GRAY),
        (317, 38, "Backbone + encoder", GRAY),
    ]
    out = []
    for index, (y, h, words, fill) in enumerate(nodes):
        out.append(block(left, y, width, h, words, fill, "white" if index == 0 else INK, 18,
                         GREEN if index == 2 else "none"))
    stages = [(57, 35), (119, 96), (190, 166), (255, 231), (317, 294), (382, 356)]
    out.extend(path(f"M{cx} {base}V{tip}", INK, arrow=True) for base, tip in stages)
    # The state operator uses the encoder memory F and prior boundary probabilities p(B).
    out.append(path("M39 336H13V143H37", BLUE, 1.5, arrow=True))
    out.append('<g transform="translate(8 254) rotate(-90)">' +
               text(0, 0, "Features", 14, color=BLUE, anchor="middle") + '</g>')
    out.append(path("M261 274H284V143H263", BLUE, 1.5, arrow=True))
    out.append('<g transform="translate(302 213) rotate(-90)">' +
               text(0, 0, "Box probabilities", 14, color=BLUE, anchor="middle") + '</g>')
    if phase in (1, 2, 3, 4, 5):
        out.append(rect(left-2, 117, width+4, 50, "none", GREEN, 2.1))
    out.append(f'<image x="84" y="382" width="132" height="87.648" href="{photo}"/>')
    if phase == 0:
        out.append(rect(81, 379, 138, 94, "none", BLUE, 2))
        out.append(path("M150 378V356", BLUE, 3, arrow=True))
    out.append(text(cx, 493, "Input image", 19, bold=True, anchor="middle"))
    return "".join(out)


def marker_defs():
    return '<defs>' + ''.join(
        f'<marker id="m{color[1:]}" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="5" '
        f'markerHeight="5" orient="auto"><path d="M0 0L8 4L0 8Z" fill="{color}"/></marker>'
        for color in (INK, BLUE, GREEN, MUTED, LINE)
    ) + '</defs>'


def scan_detail(phase):
    """Scalar, single-row worked example connected to the same vertical detector in every frame."""
    s = []
    if phase in (1, 2):
        s.append(rect(8, 12, 4, 177, BLUE))
    elif phase in (3, 4):
        s.append(rect(8, 217, 4, 174, GREEN))
    elif phase == 5:
        s.append(rect(8, 423, 4, 78, BLUE))
    s.append(text(21, 31, "One row of encoder features", 23, bold=True))
    s.append(text(21, 57, "Inside the box, the numbers show illustrative cell retentions.", 19, color=MUTED))

    # The arrows encode direction. Their moving active segment and dot mark progress
    # through the interval; the three cell values are illustrative retentions, not measurements.
    forward = phase in (1, 2)
    reverse = phase in (3, 4)
    s.append(text(22, 94, "Left to right", 17, color=BLUE if forward else MUTED))
    s.append(path("M121 89H577", BLUE if forward else MUTED, 2 if forward else 1.3, arrow=True))
    s.append(text(22, 189, "Right to left", 17, color=BLUE if reverse else MUTED))
    s.append(path("M577 184H121", BLUE if reverse else MUTED, 2 if reverse else 1.3, arrow=True))
    for i, val in enumerate(("Outside", "0.8", "0.5", "0.6", "Outside")):
        xx, ww = ((22, 149), (171, 84), (255, 84), (339, 84), (423, 156))[i]
        s.append(rect(xx, 103, ww, 56, "#f0f2f2" if i in (0, 4) else ["#e0edd8", "#c5ddc0", "#d3e4cb"][i-1],
                      "white", 2))
        s.append(text(xx+ww/2, 138, val, 21, anchor="middle", bold=i not in (0, 4)))
    for x in (171, 423):
        s.append(path(f"M{x} 97v70", GREEN, 1.7, dashed=True))
    if forward or reverse:
        cy = 89 if forward else 184
        cx = (213, 381, 381, 213)[phase-1]
        start = 121 if forward else 577
        s.append(path(f"M{start} {cy}H{cx}", BLUE, 3.5))
        s.append(f'<circle cx="{cx}" cy="{cy}" r="5" fill="{BLUE}"/>')

    s.append(path("M21 206H579", LINE, 1))
    s.append(text(21, 241, "Transmission through the box", 23, bold=True))
    s.append(text(21, 272, "T  =  0.8 × 0.5 × 0.6  =  0.24", 25, bold=True, color=GREEN))
    s.append(text(21, 301, "Each cell’s features set its Mamba retention (one channel shown).", 18, color=MUTED))
    s.append(text(21, 334, "State at each exit", 19, bold=True))
    s.append(block(21, 347, 148, 44, "Inside state", GRAY, size=18))
    s.append(text(188, 376, "+", 25, bold=True, anchor="middle"))
    s.append(block(211, 347, 368, 44, "Query gate  ×  T  ×  incoming state", PALE_GREEN,
                  size=19, edge=GREEN if phase in (3, 4) else "none"))
    s.append(path("M21 409H579", LINE, 1))
    s.append(text(21, 444, "Query update", 23, bold=True))
    flow = ((21, 142, "Average scans"), (192, 212, "Weight states by p(box)"), (433, 146, "Project + add"))
    for n, (x, w, words) in enumerate(flow):
        s.append(block(x, 458, w, 41, words, PALE_BLUE if n < 2 else BLUE,
                       INK if n < 2 else "white", 18, BLUE if phase == 5 and n < 2 else "none"))
    s.extend([path("M165 479h23", BLUE, arrow=True), path("M406 479h23", BLUE, arrow=True)])
    return "".join(s)


def scene(size, phase, photo):
    mobile = size == PORTRAIT
    w, h = size
    if mobile:
        drawing = text(16, 28, "Selective transport", 25, bold=True)
        drawing += rect(10, 39, 600, 515, "white", LINE)
        drawing += group(10, 41, 1, scan_detail(phase))
        drawing += text(16, 587, "Detector", 25, bold=True)
        # The input image stays below all other nodes, including the detail callout.
        drawing += group(97, 566, 1.42, detector(photo, phase))
        drawing += path("M469 736L539 710L595 554", GREEN, 1.4, dashed=True)
    else:
        drawing = text(22, 44, "Detector", 28, bold=True)
        drawing += text(379, 44, "Selective transport", 28, bold=True)
        drawing += rect(365, 63, 695, 570, "white", LINE)
        drawing += group(377, 71, 1.12, scan_detail(phase))
        drawing += group(18, 74, 1.11, detector(photo, phase))
        drawing += path("M311 208L365 168", GREEN, 1.4, dashed=True)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img"><title>{TITLE}</title><desc>{DESC}</desc>{marker_defs()}'
            f'<rect width="{w}" height="{h}" fill="white"/><g font-family="Calibri, Arial, sans-serif">'
            f'{drawing}</g></svg>\n')


def render(page, markup):
    page.set_content('<style>*{margin:0}svg{display:block}</style>'+markup)
    page.evaluate("document.fonts.ready")
    page.locator("svg image").evaluate(
        "e=>new Promise((ok,bad)=>{const i=new Image();i.onload=ok;i.onerror=bad;i.src=e.getAttribute('href')})")
    return Image.open(BytesIO(page.screenshot())).convert("RGB")


def save(browser, size, suffix, photo):
    w, h = size
    page = browser.new_page(viewport={"width": w, "height": h}, device_scale_factor=2)
    plates = []
    for phase in range(6):
        plate = render(page, scene(size, phase, photo))
        plates.append(plate.resize(size, Image.Resampling.LANCZOS))
    page.close()
    # Keep the reduced-motion poster in native vector form, with an embedded photograph.
    stem = DEST / f"architecture-film{suffix}"
    stem.with_suffix(".svg").write_text(scene(size, -1, photo), encoding="utf-8")
    palette_source = Image.new("RGB", (w, h*len(plates)))
    for n, plate in enumerate(plates):
        palette_source.paste(plate, (0, n*h))
    palette = palette_source.quantize(colors=256, method=Image.Quantize.MEDIANCUT)
    frames = [p.quantize(palette=palette, dither=Image.Dither.NONE) for p in plates]
    white_index = frames[0].getpixel((0, 0)) * 3
    colors = frames[0].getpalette()
    colors[white_index:white_index+3] = [255, 255, 255]
    for frame in frames:
        frame.putpalette(colors)
    frames[0].save(stem.with_suffix(".gif"), save_all=True, append_images=frames[1:],
                   duration=[3000, 1000, 1300, 1000, 1300, 3300], loop=0, disposal=1, optimize=False)


def main():
    photo = "data:image/jpeg;base64," + b64encode((ASSETS/"bicycle.jpg").read_bytes()).decode("ascii")
    DEST.mkdir(exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=os.environ.get("EVOLUTION_CHROMIUM"))
        try:
            save(browser, DESKTOP, "", photo)
            save(browser, PORTRAIT, "-mobile", photo)
        finally:
            browser.close()


if __name__ == "__main__":
    main()
