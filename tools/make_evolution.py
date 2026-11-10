"""Build the comparison plates and their portable animated GIF.

Run: python tools/make_evolution.py
Requires Pillow, Playwright with Chromium, and an installed copy of Calibri
(regular and bold). To use an existing
Chromium-based browser, set EVOLUTION_CHROMIUM to the executable path.
"""

from base64 import b64encode
from html import escape
from io import BytesIO
from functools import lru_cache
import os
from pathlib import Path
import re

from PIL import Image
from playwright.sync_api import sync_playwright


OUTPUT = Path(__file__).resolve().parents[1] / "assets" / "evolution"
NAMES = ["D-FINE", "DEIM", "Boundary-State DETR"]
DESCRIPTIONS = ["Refine the box edges", "Supervise more matches", "Filter incoming context"]
AP = [54.0, 54.7, None]
COLORS = ["#a6a6a6", "#4e95d9", "#156082"]
INK, GRAY, TEAL, GREEN = "#141414", "#e8e8e8", "#0b76a0", "#d9f2d0"
BLACK, RULE, RED = "#171717", "#d9d9d9", "#b6401a"
PLATE_W, PLATE_H = 1350, 450
COLUMN_W, CHART_W = 298, 423


def label(x, y, words, size=16, weight=400, color=INK, anchor="middle"):
    return (f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-size="{size}" '
            f'font-weight="{weight}" fill="{color}">{escape(words)}</text>')


def path(points, color, width=1.6, dash="", marker=""):
    extra = f' stroke-dasharray="{dash}"' if dash else ""
    if marker:
        extra += f' marker-end="url(#{marker})"'
    return (f'<path d="{points}" fill="none" stroke="{color}" stroke-width="{width}"'
            f'{extra}/>')


def rectangle(x, y, w, h, fill, border="none", dashed=False):
    extra = ' stroke-dasharray="4 3"' if dashed else ""
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" '
            f'stroke="{border}" stroke-width="1.3"{extra}/>')


@lru_cache(maxsize=1)
def input_photo():
    # The same unmarked COCO image feeds each detector. Embed it so that
    # raster animation frames and stand-alone SVG plates have no external assets.
    source = OUTPUT.parent / "bicycle.jpg"
    image = b64encode(source.read_bytes()).decode("ascii")
    return (f'<image x="56" y="351" width="116" height="77" '
            f'href="data:image/jpeg;base64,{image}"/>')


def architecture(i):
    """Show the common image-to-prediction path and each method's intervention."""
    axis = 114

    def node(top, text, fill=GRAY, width=184, dark=False):
        return (rectangle(axis-width/2, top, width, 28, fill)
                + label(axis, top+19, text, 16, 700 if dark else 500,
                        "white" if dark else INK))

    def up(start, end):
        return path(f"M{axis} {start}V{end}", TEAL, marker="up")

    pieces = [
        label(149, 24, f"({chr(97+i)}) {NAMES[i]}", 22, 700),
        label(149, 47, DESCRIPTIONS[i], 17, 400, "#424242"),
        input_photo(),
        label(axis, 446, "Input image", 16, 600),
        up(351, 341),
        node(311, "Backbone + encoder"),
        up(311, 298),
        node(268, "Earlier decoder layers"),
        up(268, 252),
        node(222, "Cross-attention + gate"),
        up(116, 100),
        node(70, "Class + box prediction", "#156082", 184, True),
        node(116, "FFN + prediction heads"),
    ]
    if i == 0:
        pieces += [
            up(222, 146),
            path("M207 130H248V151", "#626262", 1.3, "", "muted"),
        ]
        for n, h in enumerate((3, 7, 16, 26, 19, 8, 4)):
            pieces.append(rectangle(218 + n*9, 185-h, 7, h, "#6093af"))
        pieces += [
            path("M214 185H282", "#525252", 1),
            label(248, 206, "FDR box", 15, 600),
            label(248, 223, "distribution", 15),
        ]
    elif i == 1:
        # Training supervision connects to predictions, never to the image stem.
        pieces += [
            up(222, 146),
            path("M207 84H251V151", "#707070", 1.5, "4 3", "muted"),
            rectangle(181, 155, 113, 62, "#f3f8fd", "#8ca9be", True),
            label(237.5, 172, "Training", 14, 600),
            label(237.5, 191, "Dense one-to-one", 14, 700),
            label(237.5, 207, "matching", 15, 700),
        ]
    else:
        # Previous FDR predictions define candidate intervals at this decoder layer.
        pieces += [
            up(222, 208), up(159, 146),
            rectangle(18, 160, 192, 46, "#e1efd9", "#528248"),
            label(axis, 180, "Boundary transport", 17, 700),
            label(axis, 197, "Selective Mamba", 15),
            path("M207 282H288V183H213", "#536b59", 1.5, "", "state"),
            label(245, 231, "Box-edge", 15),
            label(245, 249, "distributions", 15),
        ]
    return "".join(pieces)


def chart(stage):
    x0, x1, y0, y1 = 43, 410, 350, 76
    xs = [105, 221, 343]
    def to_y(value):
        return round(y0 - (y0-y1)*(value-50)/6, 2)
    items = [
        label(225, 24, "(d) Box AP", 22, 700),
        label(225, 47, "COCO val2017 · L models", 17, 400, "#424242"),
    ]
    for value in range(50, 57):
        y = to_y(value)
        items += [path(f"M{x0} {y}H{x1}", RULE, 1.1),
                  label(x0-9, y+5, str(value), 15, 400, "#545454", "end")]
    for i in range(stage):
        if AP[i] is None:
            # Place the status beneath the method name, outside the AP scale.
            items.append(label(xs[i], 414, "AP pending", 15, 600, "#545454"))
        else:
            y = to_y(AP[i])
            items += [rectangle(xs[i]-24, y, 48, y0-y, COLORS[i]),
                      label(xs[i], y-9, f"{AP[i]:.1f}", 19, 700)]
        items += [label(xs[i], 376, NAMES[i], 15, 700)]
    return "".join(items)


def svg(width, height, title, contents):
    markers = "".join(
        f'<marker id="{name}" viewBox="0 0 8 8" refX="6.8" refY="4" '
        f'markerWidth="6" markerHeight="6" orient="auto"><path d="M0 0L8 4L0 8Z" fill="{color}"/></marker>'
        for name,color in [("up",TEAL),("muted","#707070"),("edit",RED),("state","#536b59")]
    )
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}">'
            f'<title>{escape(title)}</title><defs>{markers}</defs>'
            f'<rect width="{width}" height="{height}" fill="white"/>'
            f'<g font-family="Calibri">{contents}</g></svg>\n')


def save_plate(page, cdp, filename, width, title, content):
    """Bake one typeset Calibri layer so devices without the font display it too."""
    drawing = svg(width, PLATE_H, title, content)
    page.set_viewport_size({"width": width, "height": PLATE_H})
    page.set_content('<style>*{margin:0;padding:0}svg{display:block}svg path,svg rect,svg image{visibility:hidden}</style>' + drawing)
    page.evaluate("document.fonts.ready")
    root = cdp.send("DOM.getDocument")["root"]["nodeId"]
    labels = cdp.send("DOM.querySelectorAll", {"nodeId": root, "selector": "text"})["nodeIds"]
    for node in labels:
        fonts = cdp.send("CSS.getPlatformFontsForNode", {"nodeId": node})["fonts"]
        if not fonts or any(f["familyName"] != "Calibri" for f in fonts):
            raise RuntimeError(f"Install Calibri before exporting {filename}; actual fonts: {fonts}")

    # Only a finished figure is distributed, without a webfont or individual glyphs.
    png = page.screenshot(omit_background=True)
    layer = b64encode(png).decode("ascii")
    linework = re.sub(r'<text\b[^>]*>[^<]*</text>', '', drawing)
    accessible_labels = re.findall(r'<text\b[^>]*>([^<]*)</text>', drawing)
    labels_desc = " · ".join(accessible_labels)
    plate = linework.replace('</title>', f'</title><desc>{labels_desc}</desc>', 1)
    plate = plate.replace('</svg>', f'<image width="{width}" height="{PLATE_H}" href="data:image/png;base64,{layer}"/></svg>')
    (OUTPUT / filename).write_text(plate, encoding="utf-8")


def render_vectors(browser):
    OUTPUT.mkdir(parents=True, exist_ok=True)
    page = browser.new_page(device_scale_factor=3)
    cdp = page.context.new_cdp_session(page)
    cdp.send("DOM.enable")
    cdp.send("CSS.enable")
    for stage in range(1,4):
        i=stage-1
        panel=architecture(i)
        summary=chart(stage)
        save_plate(page, cdp, f"diagram-{stage}.svg", COLUMN_W, NAMES[i], panel)
        save_plate(page, cdp, f"ap-{stage}.svg", CHART_W, "Reported COCO box AP", summary)
        panels="".join(f'<g transform="translate({10+j*COLUMN_W} 0)">{architecture(j)}</g>'
                       for j in range(stage))
        rule=path("M916 12V437", "#858585", 1.5, "7 7")
        full=panels+rule+f'<g transform="translate(927 0)">{summary}</g>'
        save_plate(page, cdp, f"stage-{stage}.svg", PLATE_W, "Three detectors from input image to prediction and COCO box AP", full)
    page.close()


def animate(browser):
    # Fade whole plate images. Elements common to both plates are stationary.
    slides=[]
    page=browser.new_page(viewport={"width":PLATE_W,"height":PLATE_H},device_scale_factor=1)
    for stage in range(1,4):
        src=(OUTPUT/f"stage-{stage}.svg").read_text(encoding="utf-8")
        page.set_content('<style>*{margin:0;padding:0}svg{display:block}</style>'+src)
        image=Image.open(BytesIO(page.screenshot())).convert("RGB")
        slides.append(image)
    page.close()
    frames=[slides[0]]
    delays=[1140]
    for i,pause in enumerate((1270,1210),1):
        for s in range(1,11):
            frames.append(Image.blend(slides[i-1],slides[i],s/11))
            delays.append(70)
        frames.append(slides[i])
        delays.append(pause)
    frames[0].save(OUTPUT/"boundary-state-evolution.gif",save_all=True,
                   append_images=frames[1:],loop=0,duration=delays,disposal=1,optimize=True)


if __name__=="__main__":
    opts={"executable_path":os.environ["EVOLUTION_CHROMIUM"]} if "EVOLUTION_CHROMIUM" in os.environ else {}
    with sync_playwright() as p:
        browser=p.chromium.launch(**opts)
        render_vectors(browser)
        animate(browser)
        browser.close()
