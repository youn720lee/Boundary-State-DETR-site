"""Build the comparison plates and their portable animated GIF.

Run: python tools/make_evolution.py
Collapsed comparison, paper palette, no browser:
python tools/make_evolution.py --auxiliary-only
Legacy extended panels: python tools/make_evolution.py --extended-only
Requires Pillow, Playwright with Chromium, and an installed copy of Calibri
(regular and bold). To use an existing
Chromium-based browser, set EVOLUTION_CHROMIUM to the executable path.
"""

import argparse
from base64 import b64encode
from html import escape
from io import BytesIO
from functools import lru_cache
import os
from pathlib import Path
import re

from PIL import Image, ImageDraw, ImageFont
import xml.etree.ElementTree as ET


OUTPUT = Path(__file__).resolve().parents[1] / "assets" / "evolution"
NAMES = ["D-FINE", "DEIM", "SHIFT-DETR"]
DESCRIPTIONS = {
    "D-FINE": "Refine the box edges",
    "DEIM": "Supervise more matches",
    "SHIFT-DETR": "Transport final edge probabilities",
    "RT-DETRv4": "Distill encoder features",
}
AP = [54.0, 54.7, None]
COLORS = ["#a6a6a6", "#4e95d9", "#156082"]
INK, GRAY, TEAL, GREEN = "#141414", "#E6E6E6", "#37769F", "#DCECD4"
BLACK, RULE, RED = "#171717", "#d9d9d9", "#b6401a"
PLATE_W, PLATE_H = 1480, 510
COLUMN_W, CHART_W = 350, 400


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
    return (f'<image x="46" y="411" width="116" height="77" '
            f'href="data:image/jpeg;base64,{image}"/>')


def architecture(method, letter):
    """Show the common image-to-prediction path and each method's intervention."""
    axis = 104

    def node(top, text, fill=GRAY, width=184, dark=False):
        return (rectangle(axis-width/2, top, width, 28, fill)
                + label(axis, top+19, text, 16, 700 if dark else 500,
                        INK))

    def up(start, end):
        return path(f"M{axis} {start}V{end}", TEAL, marker="up")

    pieces = [
        label(174, 24, f"({letter}) {method}", 21, 700),
        label(174, 47, DESCRIPTIONS[method], 17, 400, "#424242"),
        input_photo(),
        label(axis, 507, "Input image", 16, 600),
        up(411, 388),
        node(357, "Backbone + encoder"),
        up(357, 329),
        node(299, "Native decoder layers"),
        up(299, 268),
        node(238, "Final FDR logits"),
        up(133, 108),
        node(78, "Class + box prediction", GRAY, 184, True),
        node(133, "Integral + LQE"),
    ]
    if method == "D-FINE":
        pieces += [
            up(238, 163),
            path("M197 252H273V210", "#626262", 1.3, "", "muted"),
        ]
        for n, h in enumerate((3, 7, 16, 26, 19, 8, 4)):
            pieces.append(rectangle(241 + n*9, 198-h, 7, h, "#C8DDEF"))
        pieces += [
            path("M236 198H308", "#525252", 1),
            label(272, 151, "Box-edge", 15, 600),
            label(272, 168, "distribution", 15),
        ]
    elif method == "DEIM":
        # Training supervision connects to predictions, never to the image stem.
        pieces += [
            up(238, 163),
            path("M197 92H279V177", "#707070", 1.5, "4 3", "muted"),
            rectangle(213, 181, 132, 66, "#F5E3D5", "#8ca9be", True),
            label(279, 200, "Training", 14, 600),
            label(279, 220, "Dense one-to-one", 15, 700),
            label(279, 238, "matching", 15, 700),
        ]
    elif method == "RT-DETRv4":
        # Image -> teacher and encoder -> loss form a training branch.
        # The distillation loss has no outgoing edge into the decoder.
        pieces += [
            up(238, 163),
            path("M163 450H278V430", "#707070", 1.4, "4 3", "muted"),
            rectangle(232, 389, 92, 38, "#F5E3D5", "#8ca9be", True),
            label(278, 405, "DINOv3", 15, 700),
            label(278, 422, "teacher", 14),
            path("M278 389V302", "#707070", 1.4, "4 3", "muted"),
            path("M197 371H242V302", "#707070", 1.4, "4 3", "muted"),
            rectangle(229, 224, 98, 74, "#F5E3D5", "#8ca9be", True),
            label(278, 242, "Training", 14, 600),
            label(278, 261, "DSI loss", 16, 700),
            label(278, 278, "weighted", 14),
            label(278, 293, "by GAM", 14),
        ]
    elif method == "SHIFT-DETR":
        # Change the final distribution once, before every native consumer.
        pieces += [
            up(238, 224), up(198, 163),
            f'<circle cx="{axis}" cy="211" r="12" fill="#C8DDEF" stroke="{INK}" stroke-width="1.4"/>',
            label(axis, 217, "T", 20, 700),
            label(66, 232, "p", 15),
            label(66, 185, "p′", 15),
            path("M225 211H119", TEAL, 1.6, "", "up"),
            rectangle(225, 178, 119, 66, "#F5E3D5", "#7b9aaa"),
            label(284.5, 197, "Adjacent-pair", 15, 700),
            label(284.5, 215, "scores", 16, 700),
            label(284.5, 234, "Shared head", 14),
            path("M285 285V248", TEAL, 1.6, "", "up"),
            rectangle(225, 285, 119, 50, "#DCECD4", "#7b9aaa"),
            label(284.5, 304, "Mamba field", 16, 700),
            label(284.5, 324, "stride 8", 15),
            path("M197 371H285V339", TEAL, 1.5, "", "up"),
            path("M197 313H212V227H222", "#707070", 1.2, "", "muted"),
            label(149, 185, "Local transfer", 14),
            label(284.5, 264, "Native candidates", 14),
        ]
    return "".join(pieces)


def chart(stage):
    x0, x1, y0, y1 = 33, 387, 390, 90
    xs = [84, 200, 326]
    def to_y(value):
        return round(y0 - (y0-y1)*(value-50)/6, 2)
    items = [
        label(204, 24, "(d) Box AP", 22, 700),
        label(204, 47, "COCO val2017 · L models", 17, 400, "#424242"),
    ]
    for value in range(50, 57):
        y = to_y(value)
        items += [path(f"M{x0} {y}H{x1}", RULE, 1.1),
                  label(x0-9, y+5, str(value), 15, 400, "#545454", "end")]
    for i in range(stage):
        if AP[i] is None:
            # Place the status beneath the method name, outside the AP scale.
            items.append(label(xs[i], 465, "AP pending", 15, 600, "#545454"))
        else:
            y = to_y(AP[i])
            items += [rectangle(xs[i]-24, y, 48, y0-y, COLORS[i]),
                      label(xs[i], y-9, f"{AP[i]:.1f}", 19, 700)]
        items += [label(xs[i], 417, NAMES[i], 15, 700)]
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
        panel=architecture(NAMES[i], chr(97+i))
        summary=chart(stage)
        save_plate(page, cdp, f"diagram-{stage}.svg", COLUMN_W, NAMES[i], panel)
        save_plate(page, cdp, f"ap-{stage}.svg", CHART_W, "Reported COCO box AP", summary)
        panels="".join(f'<g transform="translate({10+j*COLUMN_W} 0)">{architecture(NAMES[j], chr(97+j))}</g>'
                       for j in range(stage))
        rule=path("M1065 12V497", "#858585", 1.5, "7 7")
        full=panels+rule+f'<g transform="translate(1080 0)">{summary}</g>'
        save_plate(page, cdp, f"stage-{stage}.svg", PLATE_W, "Three detectors from input image to prediction and COCO box AP", full)
    page.close()


def render_extended(browser):
    page = browser.new_page(device_scale_factor=3)
    cdp = page.context.new_cdp_session(page)
    cdp.send("DOM.enable")
    cdp.send("CSS.enable")
    for method, letter, filename in [
        ("RT-DETRv4", "c", "rtv4-panel.svg"),
        ("SHIFT-DETR", "d", "selective-panel.svg"),
    ]:
        save_plate(page, cdp, filename, COLUMN_W, method, architecture(method, letter))
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


def render_auxiliary_without_browser():
    """Rebuild only the collapsed comparison; keep the paper GIF assets intact.

    Rasterize the completed Calibri label layer, never redistribute font files.
    Native SVG shapes remain vector. Requires the installed Windows Calibri font.
    """
    ns = {"s": "http://www.w3.org/2000/svg"}
    for method, letter, filename in [
        ("D-FINE", "a", "diagram-1.svg"), ("DEIM", "b", "diagram-2.svg"),
        ("SHIFT-DETR", "c", "diagram-3.svg"), ("RT-DETRv4", "c", "rtv4-panel.svg"),
        ("SHIFT-DETR", "d", "selective-panel.svg"),
    ]:
        drawing = svg(COLUMN_W, PLATE_H, method, architecture(method, letter))
        root = ET.fromstring(drawing)
        scale = 3
        layer = Image.new("RGBA", (COLUMN_W * scale, PLATE_H * scale), (255, 255, 255, 0))
        draw = ImageDraw.Draw(layer)
        labels = []
        for node in root.findall(".//s:text", ns):
            words = node.text or ""
            labels.append(words)
            bold = int(node.get("font-weight", "400")) >= 600
            font = ImageFont.truetype("C:/Windows/Fonts/" + ("calibrib.ttf" if bold else "calibri.ttf"),
                                      round(float(node.get("font-size", "16")) * scale))
            anchor = {"middle": "ms", "end": "rs", "start": "ls"}[node.get("text-anchor", "middle")]
            draw.text((float(node.get("x")) * scale, float(node.get("y")) * scale), words,
                      font=font, fill=node.get("fill", INK), anchor=anchor)
        memory = BytesIO()
        layer.save(memory, "PNG")
        encoded = b64encode(memory.getvalue()).decode("ascii")
        linework = re.sub(r'<text\b[^>]*>[^<]*</text>', '', drawing)
        linework = linework.replace('</title>', '</title><desc>' + escape(" · ".join(labels)) + '</desc>', 1)
        linework = linework.replace('</svg>', f'<image width="{COLUMN_W}" height="{PLATE_H}" href="data:image/png;base64,{encoded}"/></svg>')
        (OUTPUT / filename).write_text(linework, encoding="utf-8")
        print(filename)


if __name__=="__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--extended-only", action="store_true", help="Build only the two additional comparison plates")
    parser.add_argument("--auxiliary-only", action="store_true", help="Rebuild only five collapsed-comparison plates with the paper palette, without a browser")
    args = parser.parse_args()
    if args.auxiliary_only:
        render_auxiliary_without_browser()
        raise SystemExit(0)
    from playwright.sync_api import sync_playwright
    opts={"executable_path":os.environ["EVOLUTION_CHROMIUM"]} if "EVOLUTION_CHROMIUM" in os.environ else {}
    with sync_playwright() as p:
        browser=p.chromium.launch(**opts)
        if not args.extended_only:
            render_vectors(browser)
            animate(browser)
        render_extended(browser)
        browser.close()
