"""Render Boundary Evidence v2 with a persistent detector and animated insets.

Requires Pillow, Playwright and Calibri. EVOLUTION_CHROMIUM may point to an
installed Chromium. Diagrams show mechanism; no detector output is fabricated.
"""
from base64 import b64encode
from html import escape
from io import BytesIO
import os
from pathlib import Path
import re
from PIL import Image
from playwright.sync_api import sync_playwright

ASSETS = Path(__file__).resolve().parents[1] / "assets"
DEST = ASSETS / "contributions"
DESKTOP, PORTRAIT = (1080, 660), (620, 1190)
INK, MUTED, LINE = "#141414", "#454545", "#c8cdcf"
BLUE, PALE_BLUE = "#156082", "#e9f2f6"
GREEN, PALE_GREEN = "#48713f", "#e1efd9"
GRAY = "#e8e8e8"
TITLE = "LWR: first-layer box refinement from stride-8 selective states"
DESC = ("One image enters the backbone and encoder once. Stride-8 memory supplies a shared "
        "four-direction Mamba-style state field. At native candidate-offset positions, query "
        "similarity, a conditional first-hit law with a separate no-hit term, and local inner/outer "
        "bands feed a shared head. Its zero-initialized output is added once to first-layer FDR "
        "logits. Later decoder layers inherit the correction. Neighbour-directed denoising changes "
        "training query boxes, not the image. The overview remains visible throughout the animation.")

def text(x, y, words, size=20, *, bold=False, color=INK, anchor="start"):
    return (f'<text x="{x}" y="{y}" font-size="{size}" text-anchor="{anchor}" '
            f'fill="{color}" font-weight="{700 if bold else 400}">{escape(words)}</text>')

def rect(x, y, w, h, fill, edge="none", stroke=1, dash=False):
    d = ' stroke-dasharray="5 4"' if dash else ""
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" '
            f'stroke="{edge}" stroke-width="{stroke}"{d}/>')

def path(d, color=INK, stroke=1.7, *, arrow=False, dashed=False):
    marker = f' marker-end="url(#m{color[1:]})"' if arrow else ""
    dash = ' stroke-dasharray="4 4"' if dashed else ""
    return f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{stroke}"{marker}{dash}/>'

def block(x, y, w, h, words, fill=GRAY, size=18, edge="none", dark=False):
    lines = words.split("\n")
    result = rect(x, y, w, h, fill, edge)
    for n, line in enumerate(lines):
        yy = y+h/2+(n-(len(lines)-1)/2)*(size+3)+.32*size
        result += text(x+w/2, yy, line, size, bold=True,
                       color="white" if dark else INK, anchor="middle")
    return result

def group(x, y, scale, contents):
    return f'<g transform="translate({x},{y}) scale({scale})">{contents}</g>'

def circle(x, y, r=10, fill="white", edge=INK):
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{edge}" stroke-width="1.5"/>'

def detector(photo, phase):
    cx, left, width = 145, 37, 216
    out = [block(left,0,width,34,"Class scores + boxes",BLUE,dark=True),
           block(left,60,width,37,"Later decoder layers"),
           block(left,127,width,48,"FDR distribution",PALE_BLUE),
           block(left,208,width,42,"Decoder layer 1"),
           block(left,287,width,40,"Backbone + encoder")]
    out.extend(path(f"M{cx} {bottom}V{top}",arrow=True)
               for bottom,top in [(60,35),(127,98),(208,176),(287,251),(368,328)])
    out += [block(269,123,35,56,"LWR",PALE_GREEN,14,GREEN),
            path("M269 151H255",GREEN,arrow=True),
            path("M253 307H286V180",BLUE,arrow=True),
            '<g transform="translate(305 250) rotate(-90)">'+text(0,0,"Stride-8 memory",14,anchor="middle")+'</g>',
            path("M253 229H264V193H279V181",MUTED,1.2,arrow=True,dashed=True)]
    if phase >= 0:
        out.append(rect(266,120,41,62,"none",GREEN,2))
    out += [f'<image x="70" y="368" width="150" height="99.6" href="{photo}"/>',
            text(cx,493,"Input image",19,bold=True,anchor="middle"),
            text(cx,516,"One backbone + encoder pass",16,anchor="middle")]
    return "".join(out)

def marker_defs():
    return '<defs>'+''.join(
        f'<marker id="m{color[1:]}" viewBox="0 0 8 8" refX="7" refY="4" '
        f'markerWidth="5" markerHeight="5" orient="auto"><path d="M0 0L8 4L0 8Z" fill="{color}"/></marker>'
        for color in (INK,BLUE,GREEN,MUTED,LINE))+'</defs>'

def grid(x,y,cols=8,rows=5,cell=19,active=None):
    output=[]
    for row in range(rows):
        for col in range(cols):
            fill=PALE_GREEN if (row+col)%3==0 else PALE_BLUE
            if active==row:
                fill="#a8c3d0"
            output.append(rect(x+col*cell,y+row*cell,cell-1,cell-1,fill,"white"))
    return "".join(output)

def overview_detail():
    out=[text(20,34,"Boundary evidence at candidate offsets",25,bold=True),
         text(20,62,"Read the same spatial positions that the FDR head scores.",18),
         block(171,89,260,42,"Shared stride-8 Mamba field",PALE_BLUE),
         block(171,162,260,42,"Sample candidate positions",GRAY),
         path("M301 132V159",BLUE,arrow=True)]
    for x,words in [(20,"Query\nsimilarity"),(218,"First-hit +\nno-hit evidence"),(416,"Inner / outer\nlocal bands")]:
        out += [block(x,255,177,60,words,PALE_GREEN),
                path(f"M301 205V229H{x+88.5}V252",BLUE,arrow=True),
                path(f"M{x+88.5} 316V344H301V369",GREEN,arrow=True)]
    out += [block(171,373,260,44,"Shared evidence head",PALE_GREEN,edge=GREEN),
            path("M301 418V446",GREEN,arrow=True),
            block(171,450,260,42,"Add to first-layer FDR logits",BLUE,dark=True),
            text(301,521,"Zero-initialized correction · applied once",18,anchor="middle")]
    return "".join(out)

def field_detail():
    out=[text(20,34,"1. A shared selective state field",25,bold=True),
         text(20,62,"Keep stride-8 detail; accumulate context in four directions.",18),
         grid(76,115,cols=9,rows=6,cell=24,active=2),
         path("M61 101H307",BLUE,2.1,arrow=True),path("M307 274H61",BLUE,2.1,arrow=True),
         path("M57 113V260",BLUE,2.1,arrow=True),path("M313 260V113",BLUE,2.1,arrow=True),
         text(184,305,"80 × 80 at 640 × 640 input",18,anchor="middle"),
         path("M330 189H374",BLUE,arrow=True),
         block(384,148,193,82,"Average directions\n+ local residual",PALE_BLUE),
         path("M480 232V285",BLUE,arrow=True),block(384,290,193,46,"State feature field",PALE_GREEN),
         path("M20 360H594",LINE,1),text(24,397,"hₜ = aₜ ⊙ hₜ₋₁ + bₜ",27,bold=True),
         text(24,430,"Each cell’s features determine retention and writing.",19),
         text(24,477,"The field is built once and reused by all object queries.",19),
         text(24,510,"Candidate evidence is sampled from this field.",19)]
    return "".join(out)

def hit_detail():
    out=[text(20,34,"2. Candidate similarity and first-hit evidence",25,bold=True),
         text(20,64,"A learned map converts query–state similarity into hazards αⱼ.",18),
         text(23,114,"Box center",18),path("M119 109H572",BLUE,arrow=True),
         text(353,96,"Order candidates outward",17,anchor="middle")]
    for i,height in enumerate([22,40,78,24,6]):
        x=168+i*77
        out += [circle(x,143,5,BLUE,BLUE),rect(x-13,263-height,26,height,"#8ab4c6"),
                text(x,285,f"p{i+1}",16,anchor="middle")]
    out += [path("M145 263H518",LINE,1),
            text(333,317,"Conditional first-hit masses (schematic)",18,anchor="middle"),
            path("M20 341H594",LINE,1),
            text(24,382,"mⱼ = αⱼ ∏ᵢ<ⱼ (1 − αᵢ)",24,bold=True),
            text(24,418,"pⱼ = mⱼ / Σᵢ mᵢ",24),
            text(312,418,"p∅ = ∏ᵢ (1 − αᵢ)",24),
            text(24,464,"Normalize hits per nonempty ray; keep no-hit separately.",18),
            text(24,496,"A model-defined cue, not a physical boundary measurement.",18)]
    return "".join(out)

def bands_detail():
    out=[text(20,34,"3. Local evidence on both sides",25,bold=True),
         text(20,64,"Compare nearby features inward and outward of each candidate.",18),
         path("M52 169H555",BLUE,arrow=True),
         text(304,141,"Direction away from the box center",18,anchor="middle")]
    for i,x in enumerate([112,200,288,376,464]):
        out += [block(x-32,190,64,70,"F" if i!=2 else "xⱼ",
                      PALE_GREEN if i<2 else (BLUE if i==2 else PALE_BLUE),23,dark=i==2),
                text(x,288,["−2","−1","0","+1","+2"][i],18,anchor="middle")]
    out += [path("M69 303H243",GREEN,2),path("M333 303H507",BLUE,2),
            text(156,329,"Inner band",20,bold=True,anchor="middle"),
            text(420,329,"Outer band",20,bold=True,anchor="middle"),
            text(288,367,"Offsets in stride-8 cells",17,anchor="middle"),
            path("M20 392H594",LINE,1),text(24,433,"Read query similarity within each local band.",20),
            text(24,467,"Compare inner and outer statistics across the candidate.",20),
            text(24,508,"Three parallel rays sample each edge by default.",18)]
    return "".join(out)

def training_detail():
    out=[text(20,34,"Neighbour-directed denoising queries",25,bold=True),
         text(20,64,"Training changes query boxes; the image is encoded once.",18),
         text(20,112,"Same-class GT pair",20,bold=True),
         rect(26,137,88,106,"none",BLUE,2),rect(130,137,88,106,"none",BLUE,2),
         path("M234 190H282",arrow=True),rect(301,143,112,94,"none",GREEN,2),
         path("M383 135H413",GREEN,arrow=True),
         text(357,269,"Shifted edge",19,bold=True,anchor="middle"),
         text(357,292,"positive query",18,anchor="middle"),
         rect(447,143,135,94,"none",INK,2),path("M502 143V237",MUTED,1,dashed=True),
         text(515,269,"Merged box",19,bold=True,anchor="middle"),
         text(515,292,"negative query",18,anchor="middle"),path("M20 329H594",LINE,1),
         block(22,356,173,58,"Modify existing\nDN query slots",GRAY,18),
         path("M198 385H224",arrow=True),block(227,356,156,58,"Same decoder",PALE_BLUE,18),
         path("M386 385H413",arrow=True),block(417,356,177,58,"Native detection\nand DN losses",GRAY,18),
         text(24,461,"GT-overlap checks screen ambiguous modified boxes.",19),
         text(24,497,"DN queries are absent at inference.",19)]
    return "".join(out)

def detail(phase):
    if phase in (-1,0,5):
        return overview_detail()
    return {1:field_detail,2:hit_detail,3:bands_detail,4:training_detail}[phase]()

def scene(size,phase,photo):
    mobile=size==PORTRAIT
    w,h=size
    if mobile:
        drawing=text(16,29,"LWR",25,bold=True)
        drawing+=group(135,49,1,detector(photo,phase))
        drawing+=rect(10,592,600,575,"white",LINE)+group(12,606,.98,detail(phase))
        drawing+=path("M388 278H599V592" if phase==4 else "M439 201H599V592",GREEN,1.4,dashed=True)
    else:
        drawing=text(22,37,"Detector (LWR)",27,bold=True)+text(365,37,"Candidate-aligned refinement",27,bold=True)
        drawing+=rect(354,55,708,586,"white",LINE)+group(374,69,1.08,detail(phase))
        drawing+=group(13,60,1.08,detector(photo,phase))
        drawing+=path("M287 306L354 360" if phase==4 else "M343 223L354 191",GREEN,1.4,dashed=True)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img">'
            f'<title>{TITLE}</title><desc>{DESC}</desc>{marker_defs()}'
            f'<rect width="{w}" height="{h}" fill="white"/><g font-family="Calibri">{drawing}</g></svg>\n')

def render(page,markup):
    page.set_content('<style>*{margin:0}svg{display:block}</style>'+markup)
    page.evaluate("document.fonts.ready")
    page.locator("svg image").first.evaluate(
        "e=>new Promise((ok,bad)=>{const i=new Image();i.onload=ok;i.onerror=bad;i.src=e.getAttribute('href')})")
    return Image.open(BytesIO(page.screenshot())).convert("RGB")

def save(browser,size,suffix,photo):
    w,h=size
    page=browser.new_page(viewport={"width":w,"height":h},device_scale_factor=2)
    plates=[render(page,scene(size,phase,photo)).resize(size,Image.Resampling.LANCZOS) for phase in range(6)]
    stem=DEST/f"architecture-film{suffix}"
    drawing=scene(size,-1,photo)
    page.set_content('<style>*{margin:0}svg{display:block}svg path,svg rect,svg image,svg circle{visibility:hidden}</style>'+drawing)
    page.evaluate("document.fonts.ready")
    text_layer=b64encode(page.screenshot(omit_background=True)).decode("ascii")
    vector=re.sub(r'<text\b[^>]*>[^<]*</text>','',drawing)
    vector=vector.replace('</svg>',f'<image width="{w}" height="{h}" href="data:image/png;base64,{text_layer}"/></svg>')
    stem.with_suffix(".svg").write_text(vector,encoding="utf-8")
    page.close()
    palette_source=Image.new("RGB",(w,h*len(plates)))
    for n,plate in enumerate(plates):
        palette_source.paste(plate,(0,n*h))
    palette=palette_source.quantize(colors=256,method=Image.Quantize.MEDIANCUT)
    frames=[p.quantize(palette=palette,dither=Image.Dither.NONE) for p in plates]
    white_index=frames[0].getpixel((0,0))*3
    colors=frames[0].getpalette()
    colors[white_index:white_index+3]=[255,255,255]
    for frame in frames:
        frame.putpalette(colors)
    frames[0].save(stem.with_suffix(".gif"),save_all=True,append_images=frames[1:],
                   duration=[2600,3200,4000,3300,3700,2600],loop=0,disposal=1,optimize=False)
    preview=Path(os.environ.get("EVIDENCE_FIGURE_PREVIEW","F:/CVPR27/_workspace/bsd-evidence-page-preview"))
    preview.mkdir(parents=True,exist_ok=True)
    for n,frame in enumerate(plates):
        frame.save(preview/f"architecture{suffix}-{n}.png")

def main():
    photo="data:image/jpeg;base64,"+b64encode((ASSETS/"bicycle.jpg").read_bytes()).decode("ascii")
    DEST.mkdir(exist_ok=True)
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=os.environ.get("EVOLUTION_CHROMIUM"))
        try:
            save(browser,DESKTOP,"",photo)
            save(browser,PORTRAIT,"-mobile",photo)
        finally:
            browser.close()

if __name__=="__main__":
    main()
