"""Draw COCO feature-cell schematics for the three example objects.

python tools/make_feature_panels.py --images /path/to/coco/val2017
The examples use the existing gallery crops and GT boxes from instances_val2017.
The grid illustrates cell centers; it is not a measured activation map.
"""
from argparse import ArgumentParser
from base64 import b64encode
from hashlib import sha256
from io import BytesIO
from pathlib import Path

from PIL import Image


ASSETS = Path(__file__).resolve().parents[1] / "assets"
CASES = {
    "bicycle": (426166, (47, 128, 325, 316), (105.67, 172.78, 149.93, 123.52), None),
    "airplane": (545407, (111, 102, 528, 384), (176.43, 175.16, 299.74, 123.32),
                 "c0a40fd533950c0065e59d79dec077a445a1fddcdb8af0f0535f83a092acd02b"),
    "zebra": (552902, (85, 66, 502, 348), (129.82, 106.62, 331.56, 207.53),
              "ecae0002c2e7c82e63a47c377d92d05a9d340dbe283e2c4a0fdfe21627e77885"),
}


def crop_data(name, images=None):
    image_id, crop, _, digest = CASES[name]
    file = ASSETS / "bicycle.jpg" if name == "bicycle" else images / f"{image_id:012d}.jpg"
    if digest and sha256(file.read_bytes()).hexdigest() != digest:
        raise ValueError(f"Expected the unmodified COCO photo: {file}")
    with Image.open(file) as photo:
        out = BytesIO()
        photo.convert("RGB").crop(crop).save(out, "JPEG", quality=94)
    return "data:image/jpeg;base64," + b64encode(out.getvalue()).decode("ascii")


def cell_panel(name, photo, width=417, height=282):
    """Outline the GT in the crop and mark only cell centers outside it."""
    _, (left, top, right, bottom), (bx, by, bw, bh), _ = CASES[name]
    scale_x, scale_y = width / (right-left), height / (bottom-top)
    bx, by = (bx-left)*scale_x, (by-top)*scale_y
    bw, bh = bw*scale_x, bh*scale_y
    elements = [f'<image width="{width}" height="{height}" href="{photo}" preserveAspectRatio="none"/>']
    for row in range(8):
        for col in range(12):
            x, y = (col+.5)*width/12, (row+.5)*height/8
            if not (bx <= x <= bx+bw and by <= y <= by+bh):
                elements.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="3" fill="#eafff9" stroke="#174d54" stroke-width="1.4"/>')
    for color, thickness in (("white", 4.7), ("#075e56", 2.4)):
        elements.append(f'<rect x="{bx:.2f}" y="{by:.2f}" width="{bw:.2f}" height="{bh:.2f}" fill="none" stroke="{color}" stroke-width="{thickness}"/>')
    return "".join(elements)


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--images", type=Path, required=True)
    images = parser.parse_args().images
    for name in CASES:
        drawing = cell_panel(name, crop_data(name, images))
        graphic = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 417 282" width="834" height="564" role="img">'
                   f'<title>Exterior feature cells: {name}</title><desc>The outlined annotated box excludes '
                   'interior cell centers from the context mean. Dots illustrate exterior centers.</desc>'
                   f'{drawing}</svg>\n')
        (ASSETS / "examples" / f"{name}-context.svg").write_text(graphic, encoding="utf-8")


if __name__ == "__main__":
    main()
