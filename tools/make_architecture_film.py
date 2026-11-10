"""Build the persistent detector map and its BCSA/training magnification insets.

Requires Pillow, Playwright, Chromium, and locally installed Calibri. Set
EVOLUTION_CHROMIUM to the browser executable when using a system installation.
"""
from base64 import b64encode
from io import BytesIO
import os

from PIL import Image
from playwright.sync_api import sync_playwright

from make_feature_panels import ASSETS, cell_panel, crop_data

DEST = ASSETS / "contributions"
from make_evolution import GRAY, GREEN, INK, RED, TEAL, path, rectangle, label


BLUE, DARK, TRAIN = "#4e95d9", "#156082", "#fff8ef"
MOSS, EDGE, MUTED = "#274725", "#a6ca96", "#505050"
DESKTOP, PORTRAIT = (1080, 660), (700, 960)


def txt(x, y, text, size=18, color=INK, bold=False, anchor="start"):
    return label(x, y, text, size, 700 if bold else 400, color, anchor)


def block(x, y, w, h, lines, fill=GRAY, color=INK, size=18, edge="none"):
    result = rectangle(x, y, w, h, fill, edge)
    for n, value in enumerate(lines):
        baseline = y + h/2 + size*.32 + (n-(len(lines)-1)/2)*(size+2)
        result += txt(x+w/2, baseline, value, size, color, True, "middle")
    return result


def arrow(d, color=TEAL, *, dashed=False):
    marker = {TEAL: "flow", RED: "train", DARK: "blue", MOSS: "green", MUTED: "gray"}[color]
    return path(d, color, 1.9, "6 4" if dashed else "", marker)


def photograph(x, y, w, h, source):
    return f'<image x="{x}" y="{y}" width="{w}" height="{h}" preserveAspectRatio="none" href="{source}"/>'


def example(x, y, kind, source):
    # The source is the real 278 × 188 bicycle crop used in the project teaser.
    w, h = 153, 97
    result = photograph(x, y, w, h, source)
    bx, by, bw, bh = (22, 44, 103, 43) if kind == "A" else (47, 22, 89, 57)
    color = DARK if kind == "A" else "#2762a3"
    result += f'<rect x="{x+bx}" y="{y+by}" width="{bw}" height="{bh}" fill="none" stroke="white" stroke-width="4"/>'
    result += f'<rect x="{x+bx}" y="{y+by}" width="{bw}" height="{bh}" fill="none" stroke="{color}" stroke-width="2" stroke-dasharray="{"" if kind == "A" else "5 3"}"/>'
    return result + block(x+bx, y+by, 20, 19, [kind], color, "white", 15)


def vector(x, y, vals, fill, border, w=31):
    result = ""
    for i, value in enumerate(vals):
        result += block(x+i*w, y, w, 28, [str(value)], fill, INK, 18, border)
    return result


def plus(x, y, radius=12):
    return (f'<circle cx="{x}" cy="{y}" r="{radius}" fill="white" stroke="{TEAL}" stroke-width="2"/>'
            + path(f"M{x-6} {y}h12M{x} {y-6}v12", TEAL, 2))


def map_desktop(focus):
    s = txt(20, 108, "Detector overview", 25, bold=True)
    # Use the same bottom-up decoder, colors and line conventions as figure 1.
    items = [
        (136,["Class + box prediction"],TEAL,"white"), (194,["FFN + prediction heads"],GRAY,INK),
        (260,["BCSA"],GREEN,MOSS), (331,["Self- / cross-attn + gate"],GRAY,INK),
        (394,["Query selection + prior layers"],GRAY,INK), (456,["Backbone + encoder"],GRAY,INK),
    ]
    for y, lines, fill, color in items:
        s += block(40,y,242,38,lines,fill,color,18,EDGE if fill==GREEN else "none")
    for a,b in [(194,176),(260,234),(331,300),(394,371),(456,434),(522,496)]:
        s += arrow(f"M161 {a}V{b}")
    s += txt(161,543,"One input image",18,anchor="middle")
    s += arrow("M40 414H14V279H37",DARK)
    s += '<g transform="translate(32 393) rotate(-90)">' + txt(0,0,"Boundaries",15,DARK,True) + "</g>"
    s += rectangle(26,567,270,57,TRAIN,RED,True)
    s += txt(161,589,"TRAINING ONLY",15,RED,True,"middle")
    s += txt(161,611,"Feature replay: content + Δ",18,RED,False,"middle")
    s += arrow("M296 599H313V280H285",RED,dashed=True)
    if focus == "state":
        s += path("M285 268H322L355 234",MOSS,2,"3 3")
        s += rectangle(37,257,248,44,"none",MOSS)
    elif focus == "train":
        s += path("M297 578H321L355 540",RED,2,"3 3")
    return s


def map_mobile(focus):
    # Identical nodes run left to right in portrait. The map still fits above the
    # inset, including its background branch, without shrinking either diagram.
    s = txt(20,94,"Detector overview",25,bold=True)
    parts = [(16,120,170,"Backbone + encoder",GRAY), (219,120,196,"Prior decoder layers",GRAY),
             (449,120,226,"Self- / cross-attn + gate",GRAY), (449,199,226,"BCSA",GREEN),
             (219,199,196,"FFN + heads",GRAY), (16,199,170,"Class + box",TEAL)]
    for x,y,w,v,fill in parts:
        s += block(x,y,w,43,[v],fill,"white" if fill==TEAL else MOSS if fill==GREEN else INK,18,EDGE if fill==GREEN else "none")
    for d in ["M187 141h28", "M416 141h29", "M562 164v31","M448 221h-28","M218 221h-28"]:
        s += arrow(d)
    s += arrow("M317 164V178H465V195",DARK)
    s += txt(372,175,"Boundaries",14,DARK,False,"middle")
    s += rectangle(28,271,405,46,TRAIN,RED,True)
    s += txt(42,299,"TRAINING ONLY",16,RED,True) + txt(175,299,"Feature replay: content + Δ",18,RED)
    s += arrow("M433 294H553V247",RED,dashed=True)
    if focus=="state":
        s += rectangle(446,196,232,49,"none",MOSS) + path("M675 223H686V333L664 359",MOSS,2,"3 3")
    elif focus=="train":
        s += path("M217 319V355",RED,2,"3 3")
    return s


def opening(original):
    s = txt(18,35,"From image to detection",26,bold=True)
    s += txt(18,69,"Both paths share the encoding of one augmented training image.",20)
    s += photograph(25,122,273,184,original)
    s += txt(161,337,"One detector input",20,bold=True,anchor="middle")
    s += block(334,139,289,57,["BCSA updates each query"],GREEN,MOSS,19,EDGE)
    s += txt(334,227,"Used at training and inference",19)
    s += rectangle(334,275,289,78,TRAIN,RED,True)
    s += txt(350,302,"TRAINING ONLY",16,RED,True)
    s += txt(350,330,"Replay with feature map F′",19)
    s += path("M21 397H630","#d9d9d9",1)
    s += txt(22,434,"1   Follow the BCSA block",21,MOSS,True)
    s += txt(22,474,"2   Follow the auxiliary feature path",21,RED,True)
    return s


def state_inset(stage, original):
    s = txt(16,33,"BCSA",28,MOSS,True) + txt(96,33,"Boundary-weighted Mamba states",24,bold=True)
    s += txt(16,63,"Two candidate boxes from the previous decoder layer",19)
    for x, kind, prob, vals, border in [(70,"A","0.75",(4,0,2),DARK),(396,"B","0.25",(0,4,2),"#2762a3")]:
        s += example(x,79,kind,original)
        s += txt(x+77,200,"Box "+kind,18,border,True,"middle")
        s += arrow(f"M{x+77} 206v19",DARK)
        s += txt(x+77,250,"Mamba state "+kind,19,border,True,"middle")
        s += vector(x+30,258,vals,"#eef5fa",border)
        if stage>=2:
            s += arrow(f"M{x+77} 289v22",DARK)
            s += txt(x+77,335,"× "+prob,22,border,True,"middle")
    if stage>=2:
        s += txt(312,325,"Boundary",16,MUTED,False,"middle")+txt(312,344,"probability",16,MUTED,False,"middle")
        s += arrow("M147 342v26h150",DARK)+arrow("M473 342v26H327",DARK)
        s += plus(312,368)
        s += arrow("M312 382v13",MOSS)
        s += txt(253,419,"Weighted state",18,MOSS,True,"end")
        s += vector(268,399,(3,1,2),GREEN,EDGE)
    if stage>=3:
        s += arrow("M313 429v14",MOSS)
        s += block(174,448,279,35,["Query readout + projection"],GRAY,INK,17)
        s += arrow("M313 484v22",MOSS)
        s += txt(94,527,"Existing query q",18,DARK,True) + arrow("M220 521h76")
        s += plus(313,521)+arrow("M327 521h34")
        s += block(366,502,190,38,["Updated query q′"],TEAL,"white",19)
    return s


def training(original, stage=3):
    s = txt(16,33,"One feature map for content and step size",27,bold=True)
    s += txt(16,63,"Training only",18,RED,True)
    s += txt(122,63,"·  Reuse the encoded training sample.",19)
    s += '<g transform="translate(18 88) scale(.55)">' + cell_panel("bicycle",original) + '</g>'
    s += txt(18,257,"Exterior cell centers",16)
    s += txt(272,110,"Encoder map F",21,bold=True)
    s += txt(272,144,"At each level, take each channel’s mean",19)
    s += txt(272,167,"over cells outside every GT box.",19)
    s += block(270,196,351,48,["F′ = F − 0.5 × exterior mean"],"#eaf4f8",INK,21)
    if stage >= 2:
        s += arrow("M444 247v21H160v27",RED,dashed=True)
        s += arrow("M444 268h42v27",RED,dashed=True)
        s += block(18,300,280,46,["Content projections v′ and u′"],TRAIN,INK,19)
        s += block(346,300,280,46,["Step size Δ′"],TRAIN,INK,19)
        s += arrow("M158 348v21h162v18",RED,dashed=True)
        s += arrow("M485 348v21H320",RED,dashed=True)
        s += block(125,392,391,44,["BCSA with the same query and bounds"],GREEN,MOSS,19,EDGE)
    if stage >= 3:
        s += arrow("M320 438v24",RED,dashed=True)
        s += block(125,467,391,44,["0.1 × auxiliary detection loss"],TEAL,"white",20)
        s += txt(320,544,"Class, L1 and GIoU on the same targets",18,INK,False,"middle")
    return s


def scene(size, frame, original):
    width,height = size
    portrait = size==PORTRAIT
    focus = "train" if frame==4 else "state" if frame else None
    x,y = (23,368) if portrait else (368,76)
    title = "Boundary-State DETR"
    desc = ("Decoder overview and a connected detail. Region states are weighted by their boundary "
            "probabilities and combined, read out and projected, then added to the original query. "
            "Training reuses the encoded map. Context-centered features provide both content and step size.")
    s = txt(18,44,title,32,bold=True)
    s += path(f"M18 61H{width-18}","#d9d9d9",1)
    s += map_mobile(focus) if portrait else map_desktop(focus)
    inset = opening(original) if frame==0 else training(original) if frame==4 else state_inset(frame,original)
    stroke = RED if focus=="train" else EDGE if focus else "#d9d9d9"
    s += rectangle(x-12,y-8,671,581,"white",stroke)
    s += f'<g transform="translate({x} {y})">{inset}</g>'
    if focus=="state":
        s += txt(x+16,y+562,"States average reset row scans. Probabilities and state components are illustrative.",16,MUTED)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img">'
            f'<title>{title}</title><desc>{desc}</desc><defs>' + "".join(
                f'<marker id="{key}" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="5" markerHeight="5" orient="auto">'
                f'<path d="M0 0L8 4L0 8Z" fill="{col}"/></marker>' for key,col in
                [("flow",TEAL),("train",RED),("blue",DARK),("green",MOSS),("gray",MUTED)])
            + f'</defs><rect width="{width}" height="{height}" fill="white"/><g font-family="Calibri">{s}</g></svg>')


def render(page, cdp, markup):
    page.set_content('<style>*{margin:0}svg{display:block}</style>'+markup)
    page.evaluate("document.fonts.ready")
    for element in page.locator("svg image").all():
        element.evaluate("e=>new Promise((ok,bad)=>{const i=new Image();i.onload=ok;i.onerror=bad;i.src=e.getAttribute('href')})")
    root = cdp.send("DOM.getDocument")["root"]["nodeId"]
    for node in cdp.send("DOM.querySelectorAll", {"nodeId":root,"selector":"text"})["nodeIds"]:
        used = cdp.send("CSS.getPlatformFontsForNode", {"nodeId":node})["fonts"]
        if not used or any(f["familyName"]!="Calibri" for f in used):
            raise RuntimeError(f"Export requires installed Calibri: {used}")
    return Image.open(BytesIO(page.screenshot())).convert("RGB")


def save(browser, size, suffix, original):
    w,h = size
    page=browser.new_page(viewport={"width":w,"height":h},device_scale_factor=2)
    cdp=page.context.new_cdp_session(page)
    cdp.send("DOM.enable")
    cdp.send("CSS.enable")
    plates=[]
    for frame in range(5):
        plates.append(render(page,cdp,scene(size,frame,original)))
    page.close()
    # Store a finished 2× typeset plate so the reduced-motion view uses exactly
    # the same Calibri glyphs on devices that lack the installed font.
    still=BytesIO()
    plates[4].save(still,format="PNG",optimize=True)
    data=b64encode(still.getvalue()).decode("ascii")
    poster=(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img">'
            '<title>Boundary-State DETR with BCSA detail</title><desc>Candidate states are scaled by their '
            'boundary probabilities and summed, then read out, projected and added to the existing query. '
            'The inset shows a training-only second decoder pass with a common feature source for content and step size.</desc>'
            f'<image width="{w}" height="{h}" href="data:image/png;base64,{data}"/></svg>\n')
    (DEST/f"architecture-film{suffix}.svg").write_text(poster, encoding="utf-8")
    plates=[p.resize(size,Image.Resampling.LANCZOS) for p in plates]
    # Keep text crisp across scene boundaries. The map remains pinned.
    durations=[3000,2050,2200,5000,7800]
    sample=Image.new("RGB",(w,h*len(plates)),"white")
    for index,plate in enumerate(plates):
        sample.paste(plate,(0,index*h))
    palette=sample.quantize(colors=256,method=Image.Quantize.MEDIANCUT)
    converted=[im.quantize(palette=palette,dither=Image.Dither.NONE) for im in plates]
    white=converted[0].getpixel((0,0))*3
    colors=converted[0].getpalette()
    colors[white:white+3]=[255,255,255]
    for im in converted:
        im.putpalette(colors)
    converted[0].save(DEST/f"architecture-film{suffix}.gif",save_all=True,append_images=converted[1:],
                      duration=durations,loop=0,disposal=1,optimize=False)


def main():
    original=crop_data("bicycle")
    DEST.mkdir(exist_ok=True)
    with sync_playwright() as p:
        exe=os.environ.get("EVOLUTION_CHROMIUM")
        browser=p.chromium.launch(executable_path=exe)
        try:
            save(browser,DESKTOP,"",original)
            save(browser,PORTRAIT,"-mobile",original)
        finally:
            browser.close()


if __name__=="__main__":
    main()
