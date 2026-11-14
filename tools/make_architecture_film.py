"""Render local probability refinement with a persistent detector and animated insets.

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
TITLE = "Local Probability Refinement for Precise Object Detection"
DESC = ("One image passes through the backbone and encoder. A shared four-direction "
        "Mamba field is built from stride-8 memory and sampled at native candidate positions. "
        "The final decoder distribution, query-conditioned visual cues, and actual candidate "
        "gaps drive one shared adjacent-pair head. Local conservative transfers correct the "
        "final distribution before Integral, LQE, FGL, and GO-LSD consume it. The total "
        "one-dimensional Wasserstein distance is bounded by 5% of the uncorrected "
        "final box width or height. Native denoising and losses are retained. "
        "The overview remains visible while the details change.")

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
    cx, left, width = 139, 27, 224
    out = [block(left,0,width,34,"Class scores + boxes",BLUE,dark=True),
           block(left,59,width,35,"Integral + LQE"),
           block(left,120,width,43,"Local refinement",PALE_BLUE,19,BLUE),
           block(left,192,width,40,"Final FDR distribution"),
           block(left,262,width,38,"Native decoder layers"),
           block(left,332,width,38,"Backbone + encoder")]
    out.extend(path(f"M{cx} {bottom}V{top}",arrow=True)
               for bottom,top in [(59,35),(120,95),(192,164),(262,233),(332,301),(395,371)])
    out += [text(152,184,"p",17),text(152,113,"p′",17),
            block(264,236,46,73,"Mamba\nstride 8",PALE_BLUE,12,BLUE),
            path("M251 350H288V312",BLUE,arrow=True),
            path("M288 234V220H319V142H253",BLUE,arrow=True),
            text(285,185,"Pair",13,anchor="middle"),
            text(285,203,"scores",13,anchor="middle"),
            rect(24,117,230,49,"none",BLUE,2),
            f'<image x="65" y="395" width="148" height="98.3" href="{photo}"/>',
            text(cx,516,"Input image",19,bold=True,anchor="middle")]
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
    out=[text(20,34,"Refine the final edge distribution",25,bold=True),
         text(20,62,"Use visual evidence to move mass between adjacent candidates.",18),
         block(22,101,171,52,"Final FDR logits",GRAY),
         path("M197 127H224",arrow=True),
         block(229,101,118,52,"Softmax p",PALE_BLUE),
         path("M350 127H382",BLUE,arrow=True),
         block(386,101,205,52,"Local refinement",PALE_BLUE,19,BLUE),
         block(386,215,205,61,"Shared pair head",PALE_BLUE,19,BLUE),
         path("M489 214V156",BLUE,arrow=True),
         block(22,218,153,55,"Mamba field",PALE_BLUE),
         block(202,218,153,55,"Query + p + gaps",GRAY),
         path("M98 276V306H365V245H383",BLUE,arrow=True),
         path("M357 245H383",MUTED,arrow=True),
         path("M489 154V176H610V344H309V365",BLUE,arrow=True),
         block(178,370,261,47,"Corrected distribution p′",BLUE,dark=True),
         path("M309 420V451",BLUE,arrow=True),
         text(309,481,"Integral · LQE · FGL · GO-LSD",22,bold=True,anchor="middle"),
         text(309,516,"One distribution supplies boxes, scores, and localization losses.",17,anchor="middle")]
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

def pair_detail():
    out=[text(20,34,"2. Score each neighboring pair",25,bold=True),
         text(20,62,"Sample the field at the decoder’s native candidate locations.",18),
         text(20,100,"Support from the first-layer anchor",18,bold=True),
         path("M39 162H574",BLUE,arrow=True)]
    for i,x in enumerate([67,130,219,340,510]):
        out += [circle(x,162,6,PALE_BLUE,BLUE),
                text(x,143,"x"+str(i),17,anchor="middle")]
    out += [path("M219 183V195H340V183",MUTED),
            text(279.5,219,"Actual gap |x₃ − x₂|",18,anchor="middle"),
            text(20,257,"Final probabilities",19,bold=True),
            text(219,258,"p₂",21,anchor="middle"),text(340,258,"p₃",21,anchor="middle"),
            path("M219 269V294H448V322",BLUE,arrow=True),
            path("M340 269V294H448",BLUE),
            block(42,326,246,59,"Query affinity + appearance",PALE_BLUE,17),
            block(325,326,245,59,"p, actual gap, coverage",GRAY,17),
            path("M166 388V418H309V444",BLUE,arrow=True),
            path("M447 388V418H309",BLUE),
            block(180,447,258,44,"Shared head → scores sᵢ",BLUE,dark=True),
            text(309,523,"The same head scores every adjacent pair on all four box sides.",17,anchor="middle")]
    return "".join(out)

def redistribution_detail():
    out=[text(20,34,"3. Move mass locally",25,bold=True),
         text(20,62,"Jᵢ = c tanh(sᵢ) × donor probability, with c < ½.",18)]
    xs=[81,230,501]
    for x,prob,name in zip(xs,[.2,.5,.3],["x₀","x₁","x₂"]):
        out += [rect(x-22,228-prob*220,44,prob*220,"#b5c8d2"),
                text(x,249,name,18,anchor="middle"),
                text(x,220-prob*220,str(prob),18,bold=True,anchor="middle")]
    out += [path("M40 228H567",MUTED),text(25,103,"p",21,bold=True),
            path("M100 117H207",BLUE,2.1,arrow=True),
            text(156,100,"J₀ = 0.08",19,anchor="middle"),
            text(25,309,"p′",21,bold=True)]
    for x,prob,name in zip(xs,[.12,.58,.3],["x₀","x₁","x₂"]):
        out += [rect(x-22,442-prob*220,44,prob*220,BLUE),
                text(x,463,name,18,anchor="middle"),
                text(x,434-prob*220,str(prob),18,bold=True,anchor="middle")]
    out += [path("M40 442H567",MUTED),
            text(309,502,"p′ᵢ = pᵢ − Jᵢ + Jᵢ₋₁     ·     Σ p′ᵢ = 1",23,bold=True,anchor="middle"),
            text(309,529,"Illustrative values; the candidate positions stay fixed during refinement.",16,anchor="middle")]
    return "".join(out)

def budget_detail():
    out=[text(20,34,"4. Bound the total redistribution distance",25,bold=True),
         text(20,62,"Weight each transfer by its actual coordinate gap.",18),
         block(22,102,270,62,"Native final distribution p",GRAY,18),
         path("M295 133H330",arrow=True),
         block(333,102,260,62,"Decode Wfinal, Hfinal",PALE_BLUE,18),
         text(24,218,"D = Σᵢ |Jᵢ| · |xᵢ₊₁ − xᵢ|",28,bold=True),
         text(24,268,"B = 0.05 × Wfinal   (left / right)",23),
         text(24,301,"B = 0.05 × Hfinal   (top / bottom)",23),
         path("M20 330H594",LINE,1),
         text(24,378,"α = (B/T) / max(B/T, D)",28,bold=True),
         path("M307 368H357",BLUE,arrow=True),
         block(367,340,211,51,"Scale all J by α",PALE_BLUE,20,BLUE),
         text(24,438,"W₁(p⁰, pᵀ) ≤ B",25,bold=True),
         text(24,476,"Each of the two updates receives half of the total budget B.",19),
         text(24,514,"The reference is the uncorrected final box in this forward pass.",17)]
    return "".join(out)

def outputs_detail():
    out=[text(20,34,"5. Use one corrected distribution",25,bold=True),
         text(20,62,"The correction precedes every native final-head consumer.",18),
         block(168,104,278,57,"Corrected final distribution p′",BLUE,19,dark=True)]
    for x,words in [(20,"Integral"),(220,"LQE"),(420,"FGL + GO-LSD")]:
        out += [path(f"M307 164V211H{x+87}V256",BLUE,arrow=True),
                block(x,260,174,53,words,PALE_BLUE,19,BLUE)]
    out += [text(107,349,"Box coordinates",18,anchor="middle"),
            text(307,349,"Classification score",18,anchor="middle"),
            text(507,349,"Localization losses",18,anchor="middle"),
            path("M416 238H600V369H416Z",MUTED,1.1,dashed=True),
            text(507,398,"Training only",18,bold=True,anchor="middle"),
            path("M20 429H594",LINE,1),
            text(24,468,"Train with native denoising and the detector’s original losses.",18),
            text(24,505,"A zero-initialized pair head reproduces the native distribution.",18)]
    return "".join(out)

def detail(phase):
    if phase in (-1,0):
        return overview_detail()
    return {1:field_detail,2:pair_detail,3:redistribution_detail,4:budget_detail,5:outputs_detail}[phase]()

def scene(size,phase,photo):
    mobile=size==PORTRAIT
    w,h=size
    if mobile:
        drawing=text(16,29,"Local probability refinement",25,bold=True)
        drawing+=group(135,49,1,detector(photo,phase))
        drawing+=rect(10,592,600,575,"white",LINE)+group(12,606,.98,detail(phase))
        drawing+=path("M389 191H599V592",BLUE,1.4,dashed=True)
    else:
        drawing=text(22,37,"Detector with SHIFT-DETR",27,bold=True)+text(365,37,"Local probability refinement",27,bold=True)
        drawing+=rect(354,55,708,586,"white",LINE)+group(374,69,1.08,detail(phase))
        drawing+=group(13,60,1.08,detector(photo,phase))
        drawing+=path("M287 213L354 191",BLUE,1.4,dashed=True)
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
                   duration=[3600,4000,4800,4800,5200,4200],loop=0,disposal=1,optimize=False)
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
