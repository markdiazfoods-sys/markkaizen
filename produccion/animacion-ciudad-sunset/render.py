#!/usr/bin/env python3
"""MARK KAIZEN · Animación 'Ciudad al atardecer' estilo pantalla de carga de juego open-world.
9:16, 1080x1920, 30 fps, 10 s, con audio sintético (riser + golpe de bajo).
Uso: python3 render.py [salida.mp4]   Requiere: numpy, Pillow, ffmpeg.
Paleta de marca: negro #0B0B0F, blanco, naranja #FF6B00. Sin logos de terceros."""
import os, sys, math, random, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "mark_kaizen_ciudad-sunset_9x16.mp4")
W, H, FPS, DUR = 1080, 1920, 30, 10
BG, WHITE, ORANGE = (11, 11, 15), (255, 255, 255), (255, 107, 0)
FD = os.path.join(ROOT, "docs", "fuente", "fuentes")
SORA = lambda s: ImageFont.truetype(os.path.join(FD, "Sora-recorte.ttf"), s)
INTER = lambda s: ImageFont.truetype(os.path.join(FD, "Inter-recorte.ttf"), s)
JP = lambda s: ImageFont.truetype(os.path.join(FD, "NotoSansJP-recorte.ttf"), s)
sym = Image.open(os.path.join(ROOT, "img", "simbolo.webp")).convert("RGBA")
random.seed(7)

def ease(t): t = max(0., min(1., t)); return 1 - (1 - t) ** 4
def mix(a, b, k): return tuple(int(a[i] + (b[i] - a[i]) * k) for i in range(3))

HOR = 1180  # horizonte
# --- cielo: negro arriba -> naranja en el horizonte
sky = np.zeros((H, W, 3), np.uint8)
for y in range(H):
    k = min(1.0, max(0.0, (y / HOR))) ** 2.2
    sky[y, :] = mix(BG, ORANGE, k * 0.95)
sky_img = Image.fromarray(sky)
# sol con franjas
sd = ImageDraw.Draw(sky_img)
SUNR, SUNC = 330, (W // 2, 930)
sun = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sdd = ImageDraw.Draw(sun)
sdd.ellipse((SUNC[0] - SUNR, SUNC[1] - SUNR, SUNC[0] + SUNR, SUNC[1] + SUNR), fill=(255, 255, 255, 255))
for i in range(9):
    y0 = SUNC[1] + 20 + i * 38
    sdd.rectangle((0, y0, W, y0 + 4 + i * 3), fill=(0, 0, 0, 0))
sun_a = np.array(sun)
glow = Image.new("RGB", (W, H), ORANGE)
gm = Image.new("L", (W, H), 0); ImageDraw.Draw(gm).ellipse((SUNC[0]-620, SUNC[1]-620, SUNC[0]+620, SUNC[1]+620), fill=110)
sky_img.paste(glow, (0, 0), gm.filter(ImageFilter.GaussianBlur(120)))
sky_arr = np.array(sky_img)
sun_mask = (sun_a[..., 3] > 0)[..., None]
sky_sun = np.where(sun_mask, np.array([255, 235, 200], np.uint8), sky_arr).astype(np.uint8)

def skyline(width, base, hmin, hmax, color, windows=0.0, seed=1):
    r = random.Random(seed)
    im = Image.new("RGBA", (width, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    x = 0
    while x < width:
        bw = r.randint(70, 170); bh = r.randint(hmin, hmax)
        d.rectangle((x, base - bh, x + bw, base + 400), fill=color + (255,))
        if r.random() < 0.3: d.rectangle((x + bw // 2 - 4, base - bh - 70, x + bw // 2 + 4, base - bh), fill=color + (255,))
        if windows:
            for wy in range(base - bh + 24, base - 10, 34):
                for wx in range(x + 14, x + bw - 14, 26):
                    if r.random() < windows: d.rectangle((wx, wy, wx + 10, wy + 14), fill=ORANGE + (255,))
        x += bw + r.randint(0, 12)
    return im

def palm(h, seed):
    r = random.Random(seed)
    im = Image.new("RGBA", (420, h + 200), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    top = (210, 120)
    d.line([(200, h + 190), (205, 260), top], fill=(5, 5, 8, 255), width=16)
    for a in range(-80, 260, 34):
        ang = math.radians(a + r.randint(-8, 8)); L = r.randint(150, 200)
        mx, my = top[0] + math.cos(ang) * L * .55, top[1] + math.sin(ang) * L * .35 - 40
        ex, ey = top[0] + math.cos(ang) * L, top[1] + math.sin(ang) * L * .7 + 30
        d.line([top, (mx, my), (ex, ey)], fill=(5, 5, 8, 255), width=10)
    return im

PAD = 400  # margen para parallax horizontal
far = skyline(W + PAD * 2, HOR + 20, 160, 420, mix(BG, ORANGE, .35), 0.0, 3)
mid = skyline(W + PAD * 2, HOR + 70, 220, 640, mix(BG, ORANGE, .12), 0.22, 5)
near = skyline(W + PAD * 2, HOR + 140, 260, 760, (8, 8, 12), 0.10, 9)
palms = Image.new("RGBA", (W + PAD * 2, H), (0, 0, 0, 0))
for i, (px, ph) in enumerate([(-20, 620), (260, 520), (760, 700), (1130, 560)]):
    p = palm(ph, i); palms.alpha_composite(p, (px + PAD, 1500 - ph))
# suelo / carretera con perspectiva
road = Image.new("RGB", (W, H - HOR - 120), (8, 8, 12))

def road_frame(t):
    d_h = H - (HOR + 120)
    im = Image.new("RGB", (W, d_h), (8, 8, 12)); d = ImageDraw.Draw(im)
    vx = W // 2
    for k in range(-6, 7):  # líneas de fuga
        d.line([(vx, 0), (vx + k * 330, d_h)], fill=mix((8, 8, 12), ORANGE, .45), width=3)
    for j in range(14):  # franjas horizontales que avanzan
        z = ((j + t * 2.2) % 14) / 14
        y = int(d_h * z ** 2.2); d.line([(0, y), (W, y)], fill=mix((8, 8, 12), ORANGE, .5 * z), width=max(2, int(8 * z)))
    return im

def paste_arr(base, layer, ox, oy=0):
    l = layer.crop((0, 0, layer.width, layer.height)); base.alpha_composite(l, (int(ox), int(oy)))

def text_c(d, y, text, f, fill, a=1.0, dy=0):
    w = d.textlength(text, font=f); col = (*fill, int(255 * max(0, min(1, a))))
    d.text(((W - w) / 2, y + dy), text, font=f, fill=col)
    return w

def frame(t):
    p = t / DUR
    zoom = 1 + 0.07 * p                      # push-in lento
    base = Image.fromarray(sky_sun).convert("RGBA")
    sh = lambda amt: -PAD + amt * (p - .5)   # desplazamiento por capa (parallax)
    paste_arr(base, far, sh(60)); paste_arr(base, mid, sh(150)); paste_arr(base, near, sh(300))
    base.paste(road_frame(t), (0, HOR + 120))
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    # símbolo sale del sol
    k = ease((t - 0.3) / 1.0); size = int(430 * (0.6 + 0.4 * k))
    s = sym.resize((size, size), Image.LANCZOS)
    if k < 1: s.putalpha(s.getchannel("A").point(lambda v: int(v * k)))
    ov.alpha_composite(s, (int(SUNC[0] - size / 2), int(SUNC[1] - 330 - size / 2)))
    # textos
    a = ease((t - 2.0) / .5); text_c(d, 250, "NUEVO NIVEL", SORA(120), WHITE, a, (1 - a) * 40)
    for i, (txt, t0) in enumerate([("MEJORA.", 4.6), ("PRUEBA.", 5.1), ("APRENDE.", 5.6), ("REPITE.", 6.1)]):
        a = ease((t - t0) / .35); text_c(d, 1330 + i * 82, txt, SORA(68), ORANGE if i == 3 else WHITE, a, (1 - a) * 30)
    a = ease((t - 7.6) / .5)
    text_c(d, 1700, "MARK KAIZEN", SORA(84), WHITE, a, (1 - a) * 30)
    text_c(d, 1805, "Comenta KAIZEN", INTER(46), ORANGE, ease((t - 8.1) / .5), 0)
    base.alpha_composite(ov)
    out = base.convert("RGB")
    # destello + viñeta + zoom
    fl = max(0, 1 - abs(t - 0.9) / .15)
    if fl: out = Image.blend(out, Image.new("RGB", (W, H), ORANGE), .35 * fl)
    zw, zh = int(W * zoom), int(H * zoom)
    out = out.resize((zw, zh), Image.BILINEAR).crop(((zw - W) // 2, (zh - H) // 2, (zw - W) // 2 + W, (zh - H) // 2 + H))
    return out

def main():
    aud = ("aevalsrc='0.28*sin(2*PI*(80+60*t)*t)*(lt(t,0.9))*(t/0.9)"
           "+0.45*sin(2*PI*52*(t-0.9))*exp(-7*(t-0.9))*(gte(t,0.9))*(lt(t,2.2))"
           "+0.30*sin(2*PI*50*(t-4.6))*exp(-9*mod(t-4.6,0.5))*(gte(t,4.6))*(lt(t,6.6))"
           "+0.40*sin(2*PI*45*(t-7.6))*exp(-6*(t-7.6))*(gte(t,7.6))':s=44100:d=%d" % DUR)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-f", "lavfi", "-i", aud, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "medium",
           "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", OUT]
    pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(FPS * DUR): pr.stdin.write(frame(i / FPS).tobytes())
    pr.stdin.close(); pr.wait(); print("OK", OUT)

if __name__ == "__main__": main()
