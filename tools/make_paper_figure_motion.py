"""Publish paper-exact SHIFT-DETR figures and motion overlays (Pillow + Poppler).

The PDF remains the source of Calibri glyphs: no font file is redistributed.
Motion indicates the reading sequence, not measured activations or predictions.
"""
from pathlib import Path
import argparse
import shutil
import subprocess
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "paper-figures"
ACCENT = "#37769F"


def save_gif(path, frames, durations):
    # Fixed palette across frames prevents color flicker at text/line edges.
    samples=[frames[i].resize((480,240),Image.Resampling.LANCZOS) for i in sorted(set([0,len(frames)//2,len(frames)-1]))]
    palette_source=Image.new("RGB",(480,240*len(samples)),"white")
    for i,sample in enumerate(samples): palette_source.paste(sample,(0,240*i))
    core=[(255,255,255),(20,20,20),(230,230,230),(200,221,239),
          (220,236,212),(245,227,213),(55,118,159),(251,243,236),
          (131,131,131),(125,146,159),(199,219,234),(223,235,214),
          (194,215,232),(229,238,219),(184,209,228),(0,0,0)]
    palette=Image.new("P",(1,1))
    palette.putpalette([v for rgb in core for v in rgb] + palette_source.quantize(colors=240).getpalette()[:720])
    indexed = [f.quantize(palette=palette, dither=Image.Dither.NONE) for f in frames]
    indexed[0].save(path, save_all=True, append_images=indexed[1:],
                    duration=durations, loop=0, disposal=2, optimize=False)


def scaled_rect(draw, box, scale, color=ACCENT, width=2):
    draw.rectangle(tuple(round(v*scale) for v in box), outline=color, width=round(width*scale))


def phase_frame(base, phase, tick):
    """Keep detector context and all stages visible; highlight the active step."""
    frame = base.copy()
    d = ImageDraw.Draw(frame)
    s = frame.width/1200
    bounds = [(256, 96, 541, 518), (570, 96, 842, 518), (866, 96, 1182, 518)]
    scaled_rect(d, bounds[phase], s, width=1.7)
    # A moving marker follows an existing connection, without inventing outputs.
    paths = [((300,285),(383,285)), ((653,242.6),(689,242.6)), ((965,148),(1041,148))]
    (x1,y1),(x2,y2) = paths[phase]
    t = tick/7
    x=(x1+(x2-x1)*t)*s; y=(y1+(y2-y1)*t)*s; r=3.4*s
    d.ellipse((x-r,y-r,x+r,y+r),fill=ACCENT)
    return frame


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--paper-dir", type=Path, default=OUT)
    parser.add_argument("--pdftoppm", default="pdftoppm")
    args=parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    names=["lpt-fig1-overview","lpt-fig2-advancing","lpt-fig3-operator"]
    for name in names:
        for ext in ("pdf","svg","drawio"):
            source = args.paper_dir/f"{name}.{ext}"
            target = OUT/f"{name}.{ext}"
            if source.resolve() != target.resolve():
                shutil.copy2(source, target)
        subprocess.run([args.pdftoppm,"-png","-singlefile","-scale-to-x", "1800" if name!=names[0] else "1000", "-scale-to-y","-1",str(OUT/f"{name}.pdf"),str(OUT/name)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)

    operator=Image.open(OUT/f"{names[2]}.png").convert("RGB")
    frames=[operator.copy()]; durations=[2200]
    for phase in range(3):
        for tick in range(8):
            frames.append(phase_frame(operator,phase,tick));durations.append(280)
        frames.append(phase_frame(operator,phase,7));durations.append(1100)
    frames.append(operator.copy());durations.append(4000)
    save_gif(OUT/f"{names[2]}.gif",frames,durations)

    evolution=Image.open(OUT/f"{names[1]}.png").convert("RGB")
    ev=[]; timing=[]
    for phase in range(3):
        f=evolution.copy();d=ImageDraw.Draw(f);s=f.width/1200
        if phase<2: d.rectangle((round((400+phase*405)*s),0,f.width,f.height), fill="white")
        ev.append(f);timing.append(2200 if phase<2 else 4500)
    save_gif(OUT/f"{names[1]}.gif",ev,timing)
    # Existing directly shared GIF URLs now tell the current paper's story too.
    shutil.copy2(OUT/f"{names[2]}.gif",ROOT/"assets/contributions/architecture-film.gif")
    shutil.copy2(OUT/f"{names[2]}.gif",ROOT/"assets/contributions/architecture-film-mobile.gif")
    shutil.copy2(OUT/f"{names[1]}.gif",ROOT/"assets/evolution/boundary-state-evolution.gif")
    for name in names:
        image=Image.open(OUT/f"{name}.png")
        print(name, image.size)
    for p in OUT.glob("*.gif"):
        im=Image.open(p)
        print(p.name,im.size,im.n_frames,p.stat().st_size)


if __name__=="__main__":
    main()
