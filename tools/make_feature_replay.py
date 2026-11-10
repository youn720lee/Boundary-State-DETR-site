"""Render the exterior-cell example and the training-only decoder replay.

First run make_feature_panels.py with the three corresponding COCO images.
Uses the same Calibri and Chromium/Pillow setup as make_architecture_film.py.
"""
import os
from xml.etree import ElementTree as ET

from playwright.sync_api import sync_playwright

from make_architecture_film import (ASSETS, DARK, EDGE, GREEN, INK, MOSS, RED,
    TRAIN, arrow, block, crop_data, path, rectangle, render, scene, txt)


def example_art():
    data = ET.parse(ASSETS / "examples" / "zebra-context.svg").getroot()
    ET.register_namespace("", "http://www.w3.org/2000/svg")
    return "".join(ET.tostring(e, encoding="unicode") for e in data
                   if e.tag.rsplit("}", 1)[-1] not in ("title", "desc"))


def annotated_art(x, y, width, art):
    return f'<g transform="translate({x} {y}) scale({width/417})">{art}</g>'


def working_example(x, y, width):
    # One feature cell and one channel-wise mean, in the same coordinate system.
    s = txt(0,0,"Center the encoded features",23,bold=True)
    s += txt(0,32,"At every level, estimate one mean per channel.",18)
    rows = [("Feature at one cell", "[ 5,  3,  8 ]"),
            ("Exterior mean", "[ 2,  4,  6 ]"),
            ("F′ = F − 0.5 × mean", "[ 4,  1,  5 ]")]
    for i,(name,values) in enumerate(rows):
        row = 66+40*i
        if i==2:
            s += rectangle(-4,row-24,width+3,35,"#eaf4f8")
        s += txt(0,row,name,20,bold=i==2)
        s += txt(width-5,row,values,21,bold=i==2,anchor="end")
    s += txt(0,184,"Illustrative channel values",15,"#505050")
    return f'<g transform="translate({x} {y})">{s}</g>'


def replay(x,y,w,show_loss):
    s = txt(0,0,"Use F′ twice in the final BCSA",23,bold=True)
    hw=(w-26)/2
    for i,word in enumerate(("Write content v′, u′","Set the step size Δ′")):
        xx=i*(hw+26)
        s += block(xx,24,hw,45,[word],TRAIN,INK,19)
        if show_loss:
            a=xx+hw/2
            s += path(f"M{a} 69V91H{w/2}", RED, 1.7, "4 3")
    if show_loss:
        s += arrow(f"M{w/2} 90v19",RED,dashed=True)
        s += block(0,113,w,45,["Same query and bounds → auxiliary prediction"],GREEN,MOSS,18,EDGE)
        s += txt(w/2,188,"Classification + L1 + GIoU, weighted by 0.1",18,anchor="middle")
    return f'<g transform="translate({x} {y})">{s}</g>'


def wrapper(w,h,body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img">'
            '<title>Feature replay from one encoded sample</title><desc>The mean over cell centers outside the annotated '
            'boxes is subtracted at half strength. The same features control the Mamba content and step-size projections '
            'in the auxiliary pass. Detection uses the unmodified encoded features.</desc><defs>'
            f'<marker id="train" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="5" markerHeight="5" orient="auto">'
            f'<path d="M0 0L8 4L0 8Z" fill="{RED}"/></marker></defs><rect width="{w}" height="{h}" fill="white"/>'
            f'<g font-family="Calibri, Carlito, Arial, sans-serif">{body}</g></svg>')


def detail(frame, w, h, art):
    mobile = w < 600
    s = txt(20,39,"Feature replay",30,bold=True) + txt(w-19,37,"TRAINING ONLY",17,RED,True,"end")
    s += path(f"M20 58H{w-20}","#d4d4d4",1)
    s += txt(22,96,"Select exterior cells",23,bold=True)
    s += txt(22,126,"Centers outside all target boxes contribute to the mean.",17)
    photo_w=375 if mobile else 435
    s += annotated_art(22,147,photo_w,art)
    if mobile:
        if frame>=2: s += working_example(22,438,480)
        if frame>=3: s += replay(22,648,495,frame>=4)
    else:
        if frame>=2: s += working_example(523,96,455)
        if frame>=3: s += replay(522,349,478,frame>=4)
        s += path("M490 84V549","#d9d9d9",1)
        s += txt(22,475,"Cells drawn over the COCO image are schematic.",17,"#505050")
    s += path(f"M20 {h-52}H{w-20}","#d4d4d4",1)
    s += txt(22,h-19,"Inference uses F and one decoder pass.",19,DARK,True)
    return wrapper(w,h,s)


def write_movie(browser, path, size, images, times):
    w,h=size
    page=browser.new_page(viewport={"width":w,"height":h},device_scale_factor=1)
    cdp=page.context.new_cdp_session(page)
    cdp.send("DOM.enable")
    cdp.send("CSS.enable")
    frames=[render(page,cdp,src) for src in images]
    page.close()
    path.with_suffix(".svg").write_text(images[-1],encoding="utf-8")
    frames[0].save(path.with_suffix(".gif"),format="GIF",save_all=True,append_images=frames[1:],
                   duration=times,loop=0,disposal=1,optimize=True)


def main():
    art=example_art()
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=os.getenv("EVOLUTION_CHROMIUM"))
        try:
            for name,size in (("explain/environment",(1040,680)),("explain/environment-mobile",(540,915)),
                              ("contributions/intervention",(1040,610))):
                frames=[detail(i,*size,art) for i in (1,2,3,4)]
                write_movie(browser,ASSETS/name,size,frames,[1750,2600,2100,6200])
            # Preserve the earlier public overview URL for bookmarks and embeds.
            overview=[]
            for i in (0,2,3,4):
                nested=scene((1080,660),i,crop_data("bicycle"))
                body=f'<svg x="20" y="0" width="1000" height="610" viewBox="0 0 1080 660">{nested}</svg>'
                overview.append(wrapper(1040,610,body))
            write_movie(browser,ASSETS/"contributions"/"overview",(1040,610),overview,[2400,2400,4700,6200])
        finally:
            browser.close()


if __name__=="__main__":
    main()
