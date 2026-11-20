#!/usr/bin/env python3
"""MARK KAIZEN · Video estilo GTA · TikTok 9:16 (1080x1920, 30 fps, 15 s).
Uso: python3 render.py [salida.mp4]
Requiere: Pillow + ffmpeg. Imágenes en assets/, fuentes en docs/fuente/fuentes."""
import math, os, random, struct, subprocess, sys, wave
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "mark_kaizen_gta_9x16.mp4")
W, H, FPS = 1080, 1920, 30
FD = os.path.join(ROOT, "docs", "fuente", "fuentes")
SORA = lambda s: ImageFont.truetype(os.path.join(FD, "Sora-recorte.ttf"), s)
INTER = lambda s: ImageFont.truetype(os.path.join(FD, "Inter-recorte.ttf"), s)
JP = lambda s: ImageFont.truetype(os.path.join(FD, "NotoSansJP-recorte.ttf"), s)
PINK, ORANGE, PURPLE = (255, 64, 160), (255, 107, 0), (92, 36, 160)

sheet = Image.open(os.path.join(HERE, "assets", "hoja-personaje-gta.png")).convert("RGB")
hero = Image.open(os.path.join(HERE, "assets", "hero.jpg")).convert("RGB")

# (caja en la hoja, etiqueta, duración s)
SHOTS = [
    ((380, 0, 775, 812), "PLAYER 01", 1.5),
    ((784, 4, 1020, 362), "FRENTE", 1.3),
    ((1028, 4, 1252, 362), "PERFIL", 1.3),
    ((784, 368, 1020, 810), "3/4", 1.3),
    ((4, 822, 424, 1252), "VICE CITY", 1.4),
    ((430, 822, 850, 1252), "ACTITUD", 1.3),
    ((856, 822, 1252, 1252), "KAIZEN", 1.3),
    ((1028, 368, 1252, 810), "ESPALDA", 1.4),
]
INTRO, OUTRO = 1.8, 2.4
TOTAL = INTRO + sum(s[2] for s in SHOTS) + OUTRO  # 15.0
NF = int(round(TOTAL * FPS))

def ease(t):
    t = max(0.0, min(1.0, t)); return 1 - (1 - t) ** 3

def sunset(w=W, h=H):
    g = Image.new("RGB", (1, h))
    px = g.load()
    stops = [(0.0, (30, 18, 70)), (0.35, (120, 40, 150)), (0.62, (255, 64, 130)), (0.85, (255, 140, 40)), (1.0, (255, 190, 80))]
    for y in range(h):
        t = y / (h - 1)
        for (a, ca), (b, cb) in zip(stops, stops[1:]):
            if a <= t <= b:
                k = (t - a) / (b - a)
                px[0, y] = tuple(int(ca[i] + (cb[i] - ca[i]) * k) for i in range(3))
                break
    return g.resize((w, h))

def palms(img):
    """Siluetas de palmeras (tronco curvo + frondas que caen) a ambos lados."""
    d = ImageDraw.Draw(img)
    col = (24, 8, 40)
    for x0, hgt, side in [(70, 1500, 1), (190, 1150, 1), (1010, 1450, -1), (890, 1100, -1)]:
        top = (x0 + side * 70, H - hgt)
        ctrl = (x0 - side * 30, H - hgt * 0.5)
        pts = [((1-t)**2*x0 + 2*(1-t)*t*ctrl[0] + t*t*top[0], (1-t)**2*H + 2*(1-t)*t*ctrl[1] + t*t*top[1]) for t in [i/24 for i in range(25)]]
        for a, b, w in zip(pts, pts[1:], [20 - i*0.4 for i in range(24)]):
            d.line([a, b], fill=col, width=int(w))
        for ang in range(-80, 81, 27):
            L = 300
            ex = top[0] + L * math.sin(math.radians(ang))
            ey = top[1] - 60 + abs(ang) * 1.6
            mx, my = (top[0] + ex) / 2, top[1] - 150 + abs(ang) * 0.5
            seg = [((1-t)**2*top[0] + 2*(1-t)*t*mx + t*t*ex, (1-t)**2*top[1] + 2*(1-t)*t*my + t*t*ey) for t in [i/14 for i in range(15)]]
            for a, b, w in zip(seg, seg[1:], [14 - i for i in range(14)]):
                d.line([a, b], fill=col, width=max(2, int(w)))
    return img

BG_SUNSET = palms(sunset())
TINT = Image.new("RGBA", (W, H))
_tp = TINT.load()
for y in range(H):
    t = y / (H - 1)
    a = int(70 * (1 - abs(t - 0.5) * 1.2))
    for x in range(0, W):
        _tp[x, y] = (255, 64, 160, max(0, a))
VIGN = Image.new("L", (W, H), 0)
ImageDraw.Draw(VIGN).ellipse((-300, -200, W + 300, H + 200), fill=255)
VIGN = VIGN.filter(ImageFilter.GaussianBlur(220))

def gradient_text(text, font, grad=(PINK, ORANGE)):
    mask = Image.new("L", (W, 400), 0)
    d = ImageDraw.Draw(mask)
    bb = d.textbbox((0, 0), text, font=font)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    d.text((-bb[0], -bb[1]), text, font=font, fill=255)
    mask = mask.crop((0, 0, tw, th))
    g = Image.new("RGB", (tw, th))
    gd = ImageDraw.Draw(g)
    for y in range(th):
        k = y / max(1, th - 1)
        gd.line([(0, y), (tw, y)], fill=tuple(int(grad[0][i] + (grad[1][i] - grad[0][i]) * k) for i in range(3)))
    return g, mask

def draw_center(base, text, font, y, grad=None, fill=(255, 255, 255), shadow=True, alpha=1.0, dx=0):
    if grad:
        g, m = gradient_text(text, font, grad)
        if alpha < 1: m = m.point(lambda v: int(v * alpha))
        x = (W - g.width) // 2 + dx
        if shadow:
            sm = m.filter(ImageFilter.GaussianBlur(8)).point(lambda v: int(v * 0.8))
            base.paste((0, 0, 0), (x + 6, y + 8), sm)
        base.paste(g, (x, y), m)
        return g.height
    d = ImageDraw.Draw(base)
    bb = d.textbbox((0, 0), text, font=font)
    tw = bb[2] - bb[0]
    x = (W - tw) // 2 + dx - bb[0]
    if shadow: d.text((x + 3, y + 4), text, font=font, fill=(0, 0, 0))
    d.text((x, y), text, font=font, fill=tuple(int(c * alpha) for c in fill))
    return bb[3] - bb[1]

def prep_shot(box, framed=True):
    src = sheet.crop(box)
    sw, sh = src.size
    bg = src.resize((int(H * sw / sh) + 2, H), Image.LANCZOS)
    left = (bg.width - W) // 2
    bg = bg.crop((left, 0, left + W, H)).filter(ImageFilter.GaussianBlur(45))
    bg = ImageEnhance.Brightness(bg).enhance(0.45)
    asp = sw / sh
    fw = 1000
    fh = int(fw / asp)
    if fh > 1640:
        fh = 1640; fw = int(fh * asp)
    return src, bg, (fw, fh)

PREP = [prep_shot(s[0]) for s in SHOTS]
hero_src, hero_bg, hero_size = None, None, None
_hb = hero.resize((int(H * hero.width / hero.height) + 2, H), Image.LANCZOS)
_l = (_hb.width - W) // 2
hero_bg = ImageEnhance.Brightness(_hb.crop((_l, 0, _l + W, H)).filter(ImageFilter.GaussianBlur(40))).enhance(0.5)

def ken_burns(src, size, t, pan=1):
    """Recorte que se cierra con t∈[0,1] y se reescala al tamaño fijo."""
    sw, sh = src.size
    z = 1.0 - 0.14 * ease(t)
    cw, ch = sw * z, sh * z
    cx = sw / 2 + pan * (1 - z) * sw * 0.15
    box = (cx - cw / 2, sh / 2 - ch / 2, cx + cw / 2, sh / 2 + ch / 2)
    return src.resize(size, Image.LANCZOS, box=box)

def finish(frame, flash=0.0, t=0.0, label=None, idx=None):
    frame = frame.convert("RGBA")
    frame.alpha_composite(TINT)
    frame = frame.convert("RGB")
    dark = Image.new("RGB", (W, H), (6, 2, 14))
    frame = Image.composite(frame, dark, VIGN)
    d = ImageDraw.Draw(frame)
    if label:
        d.rounded_rectangle((60, 190, 60 + 24 + int(d.textlength(label, font=SORA(34))), 254), 10, fill=(255, 107, 0))
        d.text((72, 198), label, font=SORA(34), fill=(11, 11, 15))
    if idx is not None:
        txt = f"{idx:02d}/{len(SHOTS):02d}"
        d.text((W - 60 - d.textlength(txt, font=SORA(30)), 202), txt, font=SORA(30), fill=(255, 255, 255))
    if flash > 0:
        fl = Image.new("RGB", (W, H), (255, 160, 90))
        frame = Image.blend(frame, fl, min(1, flash))
    return frame

def frame_intro(t):
    fr = BG_SUNSET.copy()
    k = ease(t / 0.5)
    draw_center(fr, "NO ES", SORA(170), 520, fill=(255, 255, 255), alpha=k, dx=int((1 - k) * -120))
    draw_center(fr, "UN TRAILER", SORA(150), 800, grad=(PINK, ORANGE), alpha=k, dx=int((1 - k) * 120))
    d = ImageDraw.Draw(fr)
    d.line([(W // 2 - 220, 1080), (W // 2 + 220 * ease((t - .3) / .5), 1080)], fill=(255, 107, 0), width=6)
    return finish(fr, flash=max(0, 0.5 - t * 4))

def frame_shot(i, t, dur):
    src, bg, (fw, fh) = PREP[i]
    fr = bg.copy()
    fg = ken_burns(src, (fw, fh), t / dur, pan=1 if i % 2 else -1)
    x, y = (W - fw) // 2, (H - fh) // 2 - 20
    sh = Image.new("L", (fw, fh), 255).filter(ImageFilter.GaussianBlur(2))
    fr.paste((0, 0, 0), (x + 10, y + 16), Image.new("L", (fw, fh), 150).filter(ImageFilter.GaussianBlur(18)))
    fr.paste(fg, (x, y))
    ImageDraw.Draw(fr).rectangle((x, y, x + fw, y + fh), outline=(255, 107, 0), width=4)
    return finish(fr, flash=max(0, 0.55 - (t * FPS) * 0.14), label=SHOTS[i][1], idx=i + 1)

def frame_outro(t):
    fr = hero_bg.copy()
    fw = 860
    fh = int(fw * hero.height / hero.width)
    z = ease(t / OUTRO)
    img = ken_burns(hero, (fw, fh), z * 0.8)
    x, y = (W - fw) // 2, 250
    fr.paste((0, 0, 0), (x + 10, y + 16), Image.new("L", (fw, fh), 160).filter(ImageFilter.GaussianBlur(18)))
    fr.paste(img, (x, y))
    ImageDraw.Draw(fr).rectangle((x, y, x + fw, y + fh), outline=(255, 107, 0), width=4)
    fr = finish(fr, flash=max(0, 0.6 - t * 5))
    k = ease((t - 0.2) / 0.5)
    ty = y + fh + 40
    draw_center(fr, "ES MI MARCA", SORA(110), ty, grad=(PINK, ORANGE), alpha=k)
    dd = ImageDraw.Draw(fr)
    f1, f2 = SORA(54), JP(54)
    w1, w2 = dd.textlength("MARK KAIZEN", font=f1), dd.textlength("改善", font=f2)
    x0 = (W - (w1 + 24 + w2)) / 2
    dd.text((x0, ty + 150), "MARK KAIZEN", font=f1, fill=(255, 255, 255))
    dd.text((x0 + w1 + 24, ty + 146), "改善", font=f2, fill=(255, 107, 0))
    k2 = ease((t - 0.9) / 0.5)
    if k2 > 0:
        d = ImageDraw.Draw(fr)
        txt = "COMENTA: KAIZEN"
        f = SORA(46)
        tw = d.textlength(txt, font=f)
        bx = (W - tw) // 2 - 36
        d.rounded_rectangle((bx, ty + 235, bx + tw + 72, ty + 235 + 84), 42, fill=(255, 107, 0))
        d.text((bx + 36, ty + 235 + 14), txt, font=f, fill=(11, 11, 15))
    return fr

def build_frame(n):
    t = n / FPS
    if t < INTRO: return frame_intro(t)
    t -= INTRO
    for i, s in enumerate(SHOTS):
        if t < s[2]: return frame_shot(i, t, s[2])
        t -= s[2]
    return frame_outro(min(t, OUTRO))

def audio(path):
    sr = 44100
    n = int(TOTAL * sr)
    buf = [0.0] * n
    cuts = [0.0, INTRO]
    acc = INTRO
    for s in SHOTS:
        acc += s[2]; cuts.append(acc)
    for c in cuts:  # golpe de bajo en cada corte
        i0 = int(c * sr)
        for j in range(int(0.35 * sr)):
            if i0 + j >= n: break
            tt = j / sr
            f = 45 + 90 * math.exp(-tt * 18)
            buf[i0 + j] += 0.85 * math.sin(2 * math.pi * f * tt) * math.exp(-tt * 9)
    rnd = random.Random(7)
    step = 0.3
    t = 0.0
    while t < TOTAL:  # hi-hat suave
        i0 = int(t * sr)
        for j in range(int(0.05 * sr)):
            if i0 + j >= n: break
            buf[i0 + j] += 0.12 * (rnd.random() * 2 - 1) * math.exp(-j / sr * 90)
        t += step
    for j in range(n):  # colchón grave que respira
        tt = j / sr
        env = min(1, tt / 1.2) * min(1, (TOTAL - tt) / 1.0)
        buf[j] += 0.10 * env * (math.sin(2 * math.pi * 110 * tt) + 0.6 * math.sin(2 * math.pi * 165 * tt) + 0.4 * math.sin(2 * math.pi * 220.5 * tt))
    peak = max(abs(v) for v in buf) or 1
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes(b"".join(struct.pack("<hh", *(2 * [int(max(-1, min(1, v / peak * 0.9)) * 32767)])) for v in buf))

def main():
    wav = os.path.join(HERE, "_audio.wav")
    audio(wav)
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", OUT]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for n in range(NF):
        p.stdin.write(build_frame(n).tobytes())
        if n == 12 * FPS // 2 and "--preview" in sys.argv: pass
    p.stdin.close(); p.wait()
    os.remove(wav)
    print("OK", OUT)

if __name__ == "__main__":
    if "--frame" in sys.argv:  # vista previa: python3 render.py --frame N out.png
        build_frame(int(sys.argv[sys.argv.index("--frame") + 1])).save(sys.argv[-1])
    else:
        main()
