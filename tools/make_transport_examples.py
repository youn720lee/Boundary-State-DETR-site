"""Build the three COCO teaser panels from the same crop of each source image.

python tools/make_transport_examples.py --images /path/to/coco/val2017
The box and horizontal row are illustrations, not detector predictions.
"""
from argparse import ArgumentParser
from base64 import b64encode
from io import BytesIO
from pathlib import Path

from PIL import Image

from make_feature_panels import ASSETS, CASES


W, H = 417, 282
TEAL, INK, RULE = "#13667d", "#24292b", "#879396"
# Illustrative boxes in original COCO pixel coordinates and the selected row.
REGIONS = {
    "bicycle": (100, 171, 257, 298, 251),
    "airplane": (170, 168, 478, 307, 235),
    "zebra": (125, 104, 464, 318, 191),
}


def photo_uri(image):
    stream = BytesIO()
    image.save(stream, format="JPEG", quality=94)
    return "data:image/jpeg;base64," + b64encode(stream.getvalue()).decode("ascii")


def svg(title, contents):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">'
            f'<title>{title}</title>{contents}</svg>\n')


def path(commands, color, width, extra=""):
    return f'<path d="{commands}" stroke="{color}" stroke-width="{width}" fill="none" {extra}/>'


def math_label(x, y, body, size=17, anchor="middle"):
    return (f'<text x="{x:.1f}" y="{y}" text-anchor="{anchor}" font-family="Cambria Math,Georgia,serif" '
            f'font-size="{size}" fill="{INK}">{body}</text>')


def draw_case(name, images):
    image_id, crop, _, digest = CASES[name]
    image_path = ASSETS / "bicycle.jpg" if name == "bicycle" else images / f"{image_id:012d}.jpg"
    if digest:
        from hashlib import sha256
        if sha256(image_path.read_bytes()).hexdigest() != digest:
            raise ValueError(f"Unexpected COCO source: {image_path}")
    out = ASSETS / "examples"
    with Image.open(image_path) as src:
        base = src.convert("RGB").crop(crop)
    base.save(out / f"{name}-scene.webp", quality=94, method=6)
    sx = W / base.width
    sy = H / base.height
    x1, y1, x2, y2, row = REGIONS[name]
    a, b = (x1-crop[0])*sx, (x2-crop[0])*sx
    u, v, scan = (y1-crop[1])*sy, (y2-crop[1])*sy, (row-crop[1])*sy
    image = f'<image href="{photo_uri(base)}" width="{W}" height="{H}" preserveAspectRatio="none"/>'
    box = f'M{a:.2f},{u:.2f} H{b:.2f} V{v:.2f} H{a:.2f} Z'
    strip = f'M0,{scan:.2f} H{W}'
    panel = image + path(box, "white", 5) + path(box, TEAL, 2.5)
    panel += path(strip, "white", 3) + path(strip, INK, 1.4, 'stroke-dasharray="5 3"')
    for x in (a, b):
        panel += f'<circle cx="{x:.2f}" cy="{scan:.2f}" r="4.1" stroke="white" stroke-width="1.7" fill="{TEAL}"/>'
    (out / f"{name}-interval.svg").write_text(svg(f"Illustrative candidate interval on the {name}", panel), encoding="utf-8")
    # The exact same row, enlarged, connects the photograph to the two scans.
    mid = row-crop[1]
    half = round(25 / sy)
    band = base.crop((0, mid-half, base.width, mid+half))
    lo, hi = 22 + a*(W-44)/W, 22 + b*(W-44)/W
    x0, x3 = 22, W-22
    panel = '<rect width="100%" height="100%" fill="#fff"/>'
    panel += f'<rect x="{lo:.2f}" y="34" width="{hi-lo:.2f}" height="189" fill="#e7f1f2"/>'
    panel += f'<image x="{x0}" y="52" width="{x3-x0}" height="51" href="{photo_uri(band)}" preserveAspectRatio="none"/>'
    panel += path(f'M{lo:.2f},32 V222 M{hi:.2f},32 V222', TEAL, 1.6, 'stroke-dasharray="4 4"')
    panel += math_label(lo, 26, 'L') + math_label(hi, 26, 'R')
    mid_x = (lo+hi)/2
    panel += math_label(mid_x, 25, '[L, R)', 16)
    # Both directions use the same elementwise product of retention factors.
    # End arrows at the far edge of the interval, not at the edge of the photo.
    for start, end, y, k in ((x0, hi, 139, "L"), (x3, lo, 188, "R")):
        sign = 1 if start < end else -1
        entry = lo if sign == 1 else hi
        panel += path(f'M{start:.2f},{y} H{entry:.2f}', RULE, 2.5)
        panel += path(f'M{entry:.2f},{y} H{end:.2f}', TEAL, 2.5)
        panel += f'<path d="M{end:.2f} {y} l{-sign*8} -4.3 v8.6 Z" fill="{TEAL}"/>'
        # The raw histories originate beyond the two boundaries; annotate the
        # factors beside the transmitted histories at their opposite endpoints.
        outgoing = f'<tspan font-style="italic">T h</tspan><tspan dy="3" font-size="12">{k}</tspan>'
        incoming = f'<tspan font-style="italic">h</tspan><tspan dy="3" font-size="12">{k}</tspan>'
        panel += math_label(start+(entry-start)*.48, y-7, incoming, 17)
        panel += math_label(end-sign*21, y-7, outgoing, 17)
    panel += math_label(W/2, 256, '<tspan font-style="italic">T</tspan> = ∏ᵢ <tspan font-style="italic">a</tspan>ᵢ', 24)
    (out / f"{name}-crossing.svg").write_text(svg(f"Exterior states crossing one {name} interval", panel), encoding="utf-8")


if __name__ == "__main__":
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--images", type=Path, required=True)
    args = parser.parse_args()
    for case in CASES:
        draw_case(case, args.images)
