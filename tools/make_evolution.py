"""Build the comparison plates and their portable animated GIF.

Run: python tools/make_evolution.py
Requires Pillow, Playwright with Chromium, and an installed copy of Calibri
(regular and bold). To use an existing
Chromium-based browser, set EVOLUTION_CHROMIUM to the executable path.
"""

from base64 import b64encode
from html import escape
from io import BytesIO
import os
from pathlib import Path
import re

from PIL import Image
from playwright.sync_api import sync_playwright


OUTPUT = Path(__file__).resolve().parents[1] / "assets" / "evolution"
NAMES = ["D-FINE-L", "DEIM-D-FINE-L", "Boundary-State DETR-L"]
DESCRIPTIONS = ["Distribution refinement", "Dense matching in training", "Boundary-conditioned state update"]
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


def architecture(i):
    """Keep the shared forward path in the same place across all three columns."""
    x = 149
    pieces = [
        path("M149 294V277", TEAL, marker="up"),
        path("M149 242V153", TEAL, marker="up"),
        path("M149 124V103", TEAL, marker="up"),
        path("M149 75V54", TEAL, marker="up"),
        rectangle(60, 19, 178, 35, TEAL),
        label(x, 42, "Class + box prediction", 15, 700, "white"),
        rectangle(38, 75, 222, 28, GRAY),
        label(x, 94, "Class head  /  FDR box head", 15),
        rectangle(51, 124, 196, 29, GRAY),
        label(x, 144, "Feed-forward network", 15),
        rectangle(38, 242, 222, 35, GRAY),
        label(x, 264, "Cross-attention + gateway", 15),
        label(x, 309, "Query and image features", 14, 400, "#404040"),
    ]
    if i == 1:
        pieces += [
            path("M60 36H17V350H39", "#707070", 1.3, "4 3", "muted"),
            rectangle(40, 328, 218, 45, "#f3f8fd", "#4e95d9", True),
            label(x, 345, "Training only", 13, 700, "#22577a"),
            label(x, 363, "Dense O2O matching + MAL", 14),
        ]
    if i == 2:
        pieces += [
            # The green block interrupts the blue query path between CA and FFN.
            rectangle(34, 174, 230, 48, GREEN, "#a6ca96"),
            label(x, 194, "BCSA", 16, 700, "#274725"),
            label(x, 212, "Boundary-weighted Mamba states", 13, 500),
            path("M149 241V223", TEAL, marker="up"),
            '<g transform="translate(14 198) rotate(-90)">'
            + label(0, 0, "Prior boundary distribution", 13, 600, "#156082") + '</g>',
            path("M19 198H33", TEAL, marker="up"),
            rectangle(40, 328, 218, 45, "#fff8ef", "#b6401a", True),
            label(x, 345, "Training only", 13, 700, RED),
            label(x, 363, "One feature map → content + Δ", 14),
            path("M258 350H279V198H265", RED, 1.4, "4 3", "edit"),
        ]
    pieces += [
        label(x, 404, f"({chr(97+i)}) {NAMES[i]}", 20, 700, BLACK),
        label(x, 430, DESCRIPTIONS[i], 15, 400, "#454545"),
    ]
    return "".join(pieces)


def chart(stage):
    x0, x1, y0, y1 = 48, 410, 339, 65
    xs = [111, 228, 345]
    def to_y(value):
        return round(y0 - (y0-y1)*(value-50)/6, 2)
    items = [
        label(229, 31, "COCO val2017", 18, 650),
        label(20, 48, "AP", 13, 600),
    ]
    for value in range(50, 57):
        y = to_y(value)
        items += [path(f"M{x0} {y}H{x1}", RULE, 1.1),
                  label(x0-10, y+5, str(value), 14, 400, "#575757", "end")]
    for i in range(stage):
        if AP[i] is None:
            items.append(label(xs[i], y0-13, "Pending", 16, 600, "#444444"))
        else:
            y = to_y(AP[i])
            items += [rectangle(xs[i]-28, y, 56, y0-y, COLORS[i]),
                      label(xs[i], y+25, f"{AP[i]:.1f}", 20, 700, "white")]
        items += [label(xs[i], 359, f"({chr(97+i)})", 15, 600),
                  label(xs[i], 378, ["D-FINE", "DEIM", "BCSA"][i], 15, 500)]
    items += [label(229, 403, "(d) Box AP ↑", 20, 700, BLACK),
              label(229, 424, "AP axis shown from 50 to 56", 13, 400, "#5b5b5b"),
              label(218, 444, "D-FINE and DEIM report the two reference scores.", 13, 500, "#404040")]
    return "".join(items)


def svg(width, height, title, contents):
    markers = "".join(
        f'<marker id="{name}" viewBox="0 0 8 8" refX="6.8" refY="4" '
        f'markerWidth="6" markerHeight="6" orient="auto"><path d="M0 0L8 4L0 8Z" fill="{color}"/></marker>'
        for name,color in [("up",TEAL),("muted","#707070"),("edit",RED)]
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
    page.set_content('<style>*{margin:0;padding:0}svg{display:block}svg path,svg rect{visibility:hidden}</style>' + drawing)
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
        save_plate(page, cdp, f"stage-{stage}.svg", PLATE_W, "Decoder comparison and COCO box AP", full)
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
